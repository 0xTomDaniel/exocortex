#!/usr/bin/env python3
"""Bounded batch reviews in new Herdr panes; local receipts, no raw terminal API."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time

ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}\Z")
TERMINAL = {"completed", "blocked", "failed", "timed_out", "dispatch_unknown", "interrupted"}


def validate(req):
    op = req.get("operation") if isinstance(req, dict) else None
    fields = {"operation", "request_id", "prompt"} if op == "review" else {"operation", "request_id"}
    if not isinstance(op, str) or op not in {"review", "result"} or set(req) != fields:
        raise ValueError("expected review/request_id/prompt or result/request_id")
    if not isinstance(req["request_id"], str) or not ID.fullmatch(req["request_id"]):
        raise ValueError("invalid request_id")
    if op == "review" and (not isinstance(req["prompt"], str) or not req["prompt"].strip() or len(req["prompt"]) > 8000):
        raise ValueError("prompt must contain 1..8000 characters")
    return op


def save(path, value):
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(value, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        parent_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def environment(config):
    env = {"HOME": config["home"], "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin", "LANG": "en_US.UTF-8"}
    for key in ("TERM", "TMPDIR", "HERDR_ENV", "HERDR_SOCKET_PATH", "HERDR_WORKSPACE_ID", "HERDR_TAB_ID", "HERDR_PANE_ID"):
        if key in os.environ:
            env[key] = os.environ[key]
    if config.get("config_home"):
        env["XDG_CONFIG_HOME"] = config["config_home"]
    return env


def private_directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("job directory must be a private, owned directory, not a symlink")


def call(config, args):
    env = environment(config)
    p = subprocess.run([config["binary"], *args], env=env, capture_output=True, text=True, timeout=10)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[:2000])
    return json.loads(p.stdout)["result"]


def receipt(config, directory):
    record = json.loads((directory / "record.json").read_text())
    # A lost process/host cannot be inferred successful. Never auto-relaunch it.
    if record["status"] not in TERMINAL and time.time() > record["created_at"] + 240:
        record = dict(record, status="interrupted", error="No terminal receipt within deadline; inspect node before retrying under a new ID")
    if record["status"] in {"completed", "blocked"}:
        record["output"] = (directory / "output.txt").read_text()[:24000]
    return {"node": config["node"], **record}


def handle(config, config_path, req):
    op = validate(req)
    if not config.get("jobs_root"):
        raise ValueError("delegation not configured on this node")
    root = Path(config["jobs_root"])
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_directory(root)
    directory = root / req["request_id"]
    if directory.exists() or directory.is_symlink():
        private_directory(directory)
    if op == "result":
        if not (directory / "record.json").exists():
            raise ValueError("unknown request_id")
        return receipt(config, directory)
    digest = hashlib.sha256(req["prompt"].encode()).hexdigest()
    with open(root / ".admission.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if directory.exists():
            record = json.loads((directory / "record.json").read_text())
            if record["prompt_sha256"] != digest:
                raise ValueError("request_id conflict: prompt changed")
            return {**receipt(config, directory), "replayed": True}
        active = 0
        for p in root.glob("*/record.json"):
            r = json.loads(p.read_text())
            active += r["status"] not in TERMINAL or r["status"] in {"dispatch_unknown", "interrupted"}
        if active >= 1:
            raise ValueError("node review capacity is one; wait for existing receipt")
        directory.mkdir(mode=0o700)
        root_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(root_fd)
        finally:
            os.close(root_fd)
        record = {"request_id": req["request_id"], "prompt_sha256": digest,
                  "status": "dispatching", "created_at": time.time(), "policy": "codex-read-only"}
        save(directory / "prompt.json", req["prompt"])
        save(directory / "record.json", record)
        try:
            created = call(config, ["workspace", "create", "--cwd", config["review_root"],
                                    "--label", "review-" + req["request_id"], "--no-focus"])
            record.update(workspace_id=created["workspace"]["workspace_id"],
                          pane_id=created["root_pane"]["pane_id"], status="dispatched")
            save(directory / "record.json", record)
            command = shlex.join([config["python"], str(Path(__file__).resolve()),
                                  "--run", str(Path(config_path).resolve()), req["request_id"]])
            call(config, ["pane", "run", record["pane_id"], command])
        except Exception as exc:
            # A lost response may follow actual launch. Do not retry pane input.
            # Do not overwrite a terminal/running receipt produced by the runner.
            current = json.loads((directory / "record.json").read_text())
            if current["status"] == "dispatching":
                current.update(status="dispatch_unknown", error=str(exc)[:2000])
                save(directory / "record.json", current)
        return {**receipt(config, directory), "replayed": False}


def run(config_path, request_id):
    if not ID.fullmatch(request_id):
        raise ValueError("invalid request_id")
    config = json.loads(Path(config_path).read_text())
    directory = Path(config["jobs_root"]) / request_id
    with open(directory / ".runner.lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        record = json.loads((directory / "record.json").read_text())
        if record["status"] != "dispatched":
            return
        record.update(status="running", started_at=time.time())
        save(directory / "record.json", record)
        print("REVIEW_STARTED " + request_id, flush=True)
        prompt = ("Perform a read-only review of the provided review workspace. Do not change files, "
                  "access credentials, contact external services, or control other Herdr panes. "
                  "Report actionable findings and limitations. Set review_status=blocked if unable to inspect the source. This is a batch job; final output "
                  "is captured automatically. Request: " + json.loads((directory / "prompt.json").read_text()))
        cmd = [config["codex"], "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
               "--skip-git-repo-check", "--sandbox", "read-only", "-c", 'approval_policy="never"',
               "-c", 'web_search="disabled"', "-c", 'model_reasoning_effort="low"',
               "--model", config.get("model", "gpt-5.5"), "--cd", config["review_root"],
               "--output-schema", config["result_schema"],
               "--json", "--output-last-message", str(directory / "output.txt"), "-"]
        if config.get("legacy_landlock", False):
            cmd[2:2] = ["--enable", "use_legacy_landlock"]
        env = environment(config)
        # Batch reviewers do not need terminal-control context. This removes
        # accidental routing, not same-UID socket authority on the host.
        for key in list(env):
            if key.startswith("HERDR_"):
                del env[key]
        env["CODEX_HOME"] = config["codex_home"]
        process = None
        try:
            with open(directory / "events.jsonl", "w") as log:
                process = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                record["worker_pid"] = process.pid
                save(directory / "record.json", record)
                try:
                    process.communicate(prompt.encode(), timeout=180)
                    output = directory / "output.txt"
                    record.update(status="failed", exit_code=process.returncode)
                    if process.returncode == 0 and output.exists() and output.stat().st_size:
                        answer = json.loads(output.read_text())
                        if (isinstance(answer, dict) and answer.get("review_status") in {"completed", "blocked"}
                                and all(isinstance(answer.get(k), list) and all(isinstance(v, str) for v in answer[k])
                                        for k in ("findings", "limitations"))):
                            record["status"] = answer["review_status"]
                        else:
                            record["error"] = "invalid review result schema"
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    record.update(status="timed_out", exit_code=process.returncode)
        except Exception as exc:
            if process and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            record.update(status="failed", error=str(exc)[:2000])
        record["finished_at"] = time.time()
        save(directory / "record.json", record)
        print("REVIEW_FINISHED " + json.dumps(record), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--run":
        sys.exit("operator runner invocation required")
    run(sys.argv[2], sys.argv[3])
