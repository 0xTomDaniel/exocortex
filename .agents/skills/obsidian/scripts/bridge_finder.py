#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict, deque

from obsidian_cli import note_selector, parse_links_output, resolve_note, run_obsidian


def outgoing(note, vault=None):
    code, out, err = run_obsidian(["links", note_selector(note)], vault=vault)
    if code != 0:
        return [], err or out
    return parse_links_output(out, include_flags=False), None


def incoming(note, vault=None):
    code, out, err = run_obsidian(["backlinks", note_selector(note), "format=json"], vault=vault)
    if code != 0:
        return [], err or out
    if not out or out.startswith("No backlinks found"):
        return [], None
    try:
        rows = json.loads(out)
    except json.JSONDecodeError:
        return [], "Failed to parse backlinks JSON"
    vals = []
    for row in rows:
        f = row.get("file")
        if f:
            vals.append(f)
    return vals, None


def neighbors(note, include_backlinks=False, vault=None):
    out, err = outgoing(note, vault=vault)
    errs = []
    if err:
        errs.append(err)
    alln = set(out)
    if include_backlinks:
        inc, err = incoming(note, vault=vault)
        if err:
            errs.append(err)
        alln.update(inc)
    return sorted(alln), errs


def bfs(seed, depth, include_backlinks=False, vault=None):
    dist = {seed: 0}
    q = deque([seed])
    errors = []
    while q:
        node = q.popleft()
        d = dist[node]
        if d >= depth:
            continue
        nbs, errs = neighbors(node, include_backlinks=include_backlinks, vault=vault)
        for e in errs:
            errors.append({"note": node, "error": e})
        for nb in nbs:
            if nb in dist:
                continue
            dist[nb] = d + 1
            q.append(nb)
    return dist, errors


def norm(name):
    n = name.strip().lower()
    n = n.removesuffix(".md")
    return n


def main():
    ap = argparse.ArgumentParser(
        description="Find bridge notes connecting multiple seed neighborhoods"
    )
    ap.add_argument("seeds", nargs="+", help="Seed notes (2 or more)")
    ap.add_argument("--depth", type=int, default=2, help="Neighborhood depth per seed")
    ap.add_argument("--include-backlinks", action="store_true")
    ap.add_argument("--top", type=int, default=20, help="Number of bridge candidates to print")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    args.seeds = [resolve_note(seed, args.vault) for seed in args.seeds]

    if len(args.seeds) < 2:
        raise SystemExit("Provide at least 2 seeds")

    seed_dists = {}
    errors = []
    for s in args.seeds:
        d, errs = bfs(s, args.depth, include_backlinks=args.include_backlinks, vault=args.vault)
        seed_dists[s] = d
        errors.extend(errs)

    seeds_set = {norm(s) for s in args.seeds}
    coverage = defaultdict(dict)
    for s, dmap in seed_dists.items():
        for node, d in dmap.items():
            coverage[node][s] = d

    bridges = []
    for node, per_seed in coverage.items():
        if norm(node) in seeds_set:
            continue
        reach = len(per_seed)
        if reach < 2:
            continue
        dist_sum = sum(per_seed.values())
        bridges.append(
            {
                "node": node,
                "seed_coverage": reach,
                "distance_sum": dist_sum,
                "distances": per_seed,
            }
        )

    bridges.sort(key=lambda x: (-x["seed_coverage"], x["distance_sum"], x["node"].lower()))

    result = {
        "seeds": args.seeds,
        "depth": args.depth,
        "candidate_count": len(bridges),
        "bridges": bridges,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Seeds: {', '.join(args.seeds)} | depth={args.depth}")
    print(f"Bridge candidates: {len(bridges)}")
    for i, b in enumerate(bridges[: args.top], start=1):
        cov = b["seed_coverage"]
        ds = b["distance_sum"]
        dstr = ", ".join(f"{k}:{v}" for k, v in sorted(b["distances"].items()))
        print(f"{i:>2}. {b['node']}  [coverage={cov}, distance_sum={ds}]  {{{dstr}}}")

    if errors:
        print("\nWarnings:")
        for e in errors[:20]:
            print(f"  - {e['note']}: {e['error']}")


if __name__ == "__main__":
    main()
