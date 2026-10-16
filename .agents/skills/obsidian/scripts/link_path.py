#!/usr/bin/env python3
import argparse
from collections import deque

from obsidian_cli import note_selector, parse_links_output, resolve_note, run_obsidian


def neighbors(note, vault=None):
    code, out, err = run_obsidian(["links", note_selector(note)], vault=vault)
    if code != 0:
        return [], err or out
    return parse_links_output(out, include_flags=False), None


def norm(name):
    x = name.strip().lower()
    x = x.removesuffix(".md")
    return x


def main():
    ap = argparse.ArgumentParser(
        description="Find shortest outgoing-link path between two Obsidian notes"
    )
    ap.add_argument("source", help="Source note")
    ap.add_argument("target", help="Target note")
    ap.add_argument("--max-depth", type=int, default=4, help="Maximum BFS depth (default: 4)")
    ap.add_argument("--vault", help="Optional vault name for obsidian CLI")
    args = ap.parse_args()

    src = resolve_note(args.source, args.vault)
    target_norm = norm(resolve_note(args.target, args.vault))

    q = deque([(src, 0)])
    prev = {src: None}
    errors = []
    found = None

    while q:
        node, depth = q.popleft()
        if norm(node) == target_norm:
            found = node
            break
        if depth >= args.max_depth:
            continue

        nxt, err = neighbors(node, vault=args.vault)
        if err:
            errors.append((node, err))
            continue
        for nb in nxt:
            if nb in prev:
                continue
            prev[nb] = node
            q.append((nb, depth + 1))
            if norm(nb) == target_norm:
                found = nb
                q.clear()
                break

    if not found:
        print(
            f"No path found from '{args.source}' to '{args.target}' within depth {args.max_depth}."
        )
        if errors:
            print("Warnings:")
            for n, e in errors[:10]:
                print(f"  - {n}: {e}")
        raise SystemExit(2 if errors else 1)

    path = []
    cur = found
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    print(f"Path ({len(path) - 1} hops):")
    for i, n in enumerate(path):
        prefix = "└─" if i == len(path) - 1 else "├─"
        print(f"{prefix} {n}")

    if errors:
        print("\nWarnings:")
        for n, e in errors[:10]:
            print(f"  - {n}: {e}")


if __name__ == "__main__":
    main()
