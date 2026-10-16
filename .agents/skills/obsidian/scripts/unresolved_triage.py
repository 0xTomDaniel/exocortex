#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict, deque

from obsidian_cli import note_selector, parse_links_output, resolve_note, run_obsidian


def outgoing(note, vault=None):
    code, out, err = run_obsidian(["links", note_selector(note)], vault=vault)
    if code != 0:
        return [], err or out
    return parse_links_output(out), None


def main():
    ap = argparse.ArgumentParser(
        description="Rank unresolved link targets by frequency in local graph exploration"
    )
    ap.add_argument("seeds", nargs="+", help="Seed notes")
    ap.add_argument(
        "--depth", type=int, default=2, help="Traversal depth from each seed (default: 2)"
    )
    ap.add_argument("--top", type=int, default=25, help="Max unresolved targets to print")
    ap.add_argument("--vault", help="Optional vault for obsidian CLI")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()
    args.seeds = [resolve_note(seed, args.vault) for seed in args.seeds]

    q = deque()
    seen = set()
    for s in args.seeds:
        q.append((s, 0, s))  # node, depth, root-seed
        seen.add((s, s))

    counts = Counter()
    source_files = defaultdict(set)
    source_seeds = defaultdict(set)
    first_seen_hop = {}
    errors = []

    while q:
        node, depth, root = q.popleft()
        links, err = outgoing(node, vault=args.vault)
        if err:
            errors.append({"note": node, "seed": root, "error": err})
            continue

        for l in links:
            tgt = l["target"]
            if l["unresolved"]:
                counts[tgt] += 1
                source_files[tgt].add(node)
                source_seeds[tgt].add(root)
                if tgt not in first_seen_hop:
                    first_seen_hop[tgt] = depth + 1
                continue

            if depth >= args.depth:
                continue
            key = (tgt, root)
            if key in seen:
                continue
            seen.add(key)
            q.append((tgt, depth + 1, root))

    rows = []
    for target, c in counts.most_common():
        rows.append(
            {
                "target": target,
                "count": c,
                "seed_coverage": len(source_seeds[target]),
                "first_seen_hop": first_seen_hop.get(target),
                "source_files": sorted(source_files[target]),
                "source_seeds": sorted(source_seeds[target]),
            }
        )

    result = {
        "seeds": args.seeds,
        "depth": args.depth,
        "unresolved_count": len(rows),
        "ranked": rows,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Seeds: {', '.join(args.seeds)} | depth={args.depth}")
    print(f"Unresolved targets found: {len(rows)}")
    for i, r in enumerate(rows[: args.top], start=1):
        print(
            f"{i:>2}. {r['target']}  [count={r['count']}, seeds={r['seed_coverage']}, first_hop={r['first_seen_hop']}]"
        )
        print(f"    sources: {', '.join(r['source_files'])}")

    if errors:
        print("\nWarnings:")
        for e in errors[:20]:
            print(f"  - seed={e['seed']} note={e['note']}: {e['error']}")


if __name__ == "__main__":
    main()
