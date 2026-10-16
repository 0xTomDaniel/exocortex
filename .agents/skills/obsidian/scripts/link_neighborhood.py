#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict, deque

from obsidian_cli import note_selector, parse_links_output, resolve_note, run_obsidian


def get_outgoing(note, vault=None):
    code, out, err = run_obsidian(["links", note_selector(note)], vault=vault)
    if code != 0:
        return [], err or out
    return parse_links_output(out), None


def get_incoming(note, vault=None):
    code, out, err = run_obsidian(["backlinks", note_selector(note), "format=json"], vault=vault)
    if code != 0:
        return [], err or out
    if not out or out.startswith("No backlinks found"):
        return [], None
    try:
        rows = json.loads(out)
    except json.JSONDecodeError:
        return [], "Failed to parse backlinks JSON"
    incoming = []
    for row in rows:
        src = row.get("file")
        if src:
            incoming.append({"source": src})
    return incoming, None


def main():
    ap = argparse.ArgumentParser(
        description="Explore Obsidian wikilink neighborhood using obsidian CLI"
    )
    ap.add_argument(
        "seed", help="Seed note name (wikilink-style, e.g. 'My Note' or 'Path/Note.md')"
    )
    ap.add_argument("--depth", type=int, default=1, help="Traversal depth (default: 1)")
    ap.add_argument(
        "--include-backlinks", action="store_true", help="Include incoming links in traversal"
    )
    ap.add_argument(
        "--include-unresolved", action="store_true", help="Traverse unresolved link names as nodes"
    )
    ap.add_argument("--vault", help="Optional vault name for obsidian CLI")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()
    args.seed = resolve_note(args.seed, args.vault)

    seen = {args.seed}
    hops = defaultdict(list)
    hops[0].append(args.seed)
    q = deque([(args.seed, 0)])
    edges = []
    errors = []

    while q:
        node, depth = q.popleft()
        if depth >= args.depth:
            continue

        outgoing, err = get_outgoing(node, vault=args.vault)
        if err:
            errors.append({"note": node, "error": err})
        for link in outgoing:
            tgt = link["target"]
            unresolved = link["unresolved"]
            edges.append({"from": node, "to": tgt, "direction": "out", "unresolved": unresolved})
            if unresolved and not args.include_unresolved:
                continue
            if tgt not in seen:
                seen.add(tgt)
                hops[depth + 1].append(tgt)
                q.append((tgt, depth + 1))

        if args.include_backlinks:
            incoming, err = get_incoming(node, vault=args.vault)
            if err:
                errors.append({"note": node, "error": err})
            for ref in incoming:
                src = ref["source"]
                edges.append({"from": src, "to": node, "direction": "in", "unresolved": False})
                if src not in seen:
                    seen.add(src)
                    hops[depth + 1].append(src)
                    q.append((src, depth + 1))

    result = {
        "seed": args.seed,
        "depth": args.depth,
        "nodes_by_hop": {str(k): v for k, v in sorted(hops.items())},
        "edge_count": len(edges),
        "edges": edges,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Seed: {args.seed} | depth={args.depth}")
    for hop in sorted(hops.keys()):
        print(f"\nHop {hop} ({len(hops[hop])}):")
        for n in sorted(hops[hop]):
            print(f"  - {n}")
    print(f"\nEdges: {len(edges)}")
    unresolved = sum(1 for e in edges if e.get("unresolved"))
    if unresolved:
        print(f"Unresolved edges: {unresolved}")
    if errors:
        print("\nWarnings:")
        for e in errors:
            print(f"  - {e['note']}: {e['error']}")


if __name__ == "__main__":
    main()
