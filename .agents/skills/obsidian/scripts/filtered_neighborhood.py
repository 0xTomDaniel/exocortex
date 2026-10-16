#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6,<7"]
# ///
import argparse
import datetime as dt
import json
from collections import defaultdict, deque

from note_metadata import parse_frontmatter
from status_policy import status_equal
from obsidian_cli import note_selector, parse_links_output, resolve_note, run_obsidian


def get_outgoing(note, vault=None):
    code, out, err = run_obsidian(["links", note_selector(note)], vault=vault)
    if code != 0:
        return [], err or out
    return parse_links_output(out), None


def get_file_info(note, vault=None):
    code, out, err = run_obsidian(["file", note_selector(note)], vault=vault)
    if code != 0:
        raise RuntimeError(err or out or "File lookup failed")
    info = {}
    for ln in out.splitlines():
        if "\t" not in ln:
            continue
        k, v = ln.split("\t", 1)
        info[k.strip()] = v.strip()
    return info


def read_note_text(note, vault=None):
    code, out, err = run_obsidian(["read", note_selector(note)], vault=vault)
    if code != 0:
        raise RuntimeError(err or out or "Note read failed")
    return out


def parse_date(date_str):
    try:
        return dt.date.fromisoformat(str(date_str))
    except (TypeError, ValueError):
        return None


def matches_filters(note, args, cache, vault=None):
    if note in cache:
        return cache[note]

    info = get_file_info(note, vault=vault)
    if not info:
        cache[note] = (False, {"reason": "not-found"})
        return cache[note]

    modified_ms = int(info.get("modified", "0") or 0)
    modified_date = (
        dt.datetime.fromtimestamp(modified_ms / 1000, dt.UTC).date() if modified_ms else None
    )

    if args.modified_after and modified_date and modified_date < args.modified_after:
        cache[note] = (False, {"reason": "modified-before-window"})
        return cache[note]
    if args.modified_before and modified_date and modified_date > args.modified_before:
        cache[note] = (False, {"reason": "modified-after-window"})
        return cache[note]

    txt = read_note_text(note, vault=vault)
    fm = parse_frontmatter(txt)

    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    for req in args.tags:
        q = req.lstrip("#")
        ok = any(str(t) == q or str(t).startswith(q + "/") for t in tags)
        if not ok:
            cache[note] = (False, {"reason": f"missing-tag:{req}"})
            return cache[note]

    for key, val in args.props:
        actual = fm.get(key)
        if key == 'status':
            ok = status_equal(actual, val)
        elif isinstance(actual, list):
            ok = val in actual
        else:
            ok = str(actual) == val
        if not ok:
            cache[note] = (False, {"reason": f"property-mismatch:{key}"})
            return cache[note]

    if args.date_property:
        dv = fm.get(args.date_property)
        if isinstance(dv, list):
            dv = dv[0] if dv else None
        d = parse_date(str(dv)) if dv else None
        if not d:
            cache[note] = (False, {"reason": f"missing-date-property:{args.date_property}"})
            return cache[note]
        if args.date_after and d < args.date_after:
            cache[note] = (False, {"reason": "date-before-window"})
            return cache[note]
        if args.date_before and d > args.date_before:
            cache[note] = (False, {"reason": "date-after-window"})
            return cache[note]

    cache[note] = (
        True,
        {"frontmatter": fm, "modified": str(modified_date) if modified_date else None},
    )
    return cache[note]


def parse_prop(expr):
    if "=" not in expr:
        raise ValueError(f"Invalid --prop '{expr}', expected key=value")
    k, v = expr.split("=", 1)
    return k.strip(), v.strip()


def main():
    ap = argparse.ArgumentParser(
        description="Neighborhood traversal with optional tag/property/date filters"
    )
    ap.add_argument("seed", help="Seed note name/path")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument(
        "--tag", action="append", dest="tags", default=[], help="Require tag (repeatable)"
    )
    ap.add_argument(
        "--prop",
        action="append",
        dest="prop_expr",
        default=[],
        help="Require property key=value (repeatable)",
    )
    ap.add_argument("--date-property", help="Frontmatter date property for date window filtering")
    ap.add_argument("--date-after", help="Include notes with date_property >= YYYY-MM-DD")
    ap.add_argument("--date-before", help="Include notes with date_property <= YYYY-MM-DD")
    ap.add_argument("--modified-after", help="Include notes modified on/after YYYY-MM-DD")
    ap.add_argument("--modified-before", help="Include notes modified on/before YYYY-MM-DD")
    ap.add_argument(
        "--strict-filter-traversal",
        action="store_true",
        help="Only expand from nodes that match filters",
    )
    ap.add_argument("--include-unresolved", action="store_true")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    args.seed = resolve_note(args.seed, args.vault)

    args.props = [parse_prop(x) for x in args.prop_expr]
    args.date_after = parse_date(args.date_after) if args.date_after else None
    args.date_before = parse_date(args.date_before) if args.date_before else None
    args.modified_after = parse_date(args.modified_after) if args.modified_after else None
    args.modified_before = parse_date(args.modified_before) if args.modified_before else None

    q = deque([(args.seed, 0)])
    seen = {args.seed}
    all_hops = defaultdict(list)
    matched_hops = defaultdict(list)
    all_hops[0].append(args.seed)

    edges = []
    errors = []
    cache = {}

    seed_ok, _ = matches_filters(args.seed, args, cache, vault=args.vault)
    if seed_ok:
        matched_hops[0].append(args.seed)

    while q:
        node, depth = q.popleft()
        if depth >= args.depth:
            continue

        node_ok, _ = matches_filters(node, args, cache, vault=args.vault)
        if args.strict_filter_traversal and not node_ok and depth > 0:
            continue

        outgoing, err = get_outgoing(node, vault=args.vault)
        if err:
            errors.append({"note": node, "error": err})

        for l in outgoing:
            tgt = l["target"]
            unresolved = l["unresolved"]
            edges.append({"from": node, "to": tgt, "unresolved": unresolved})
            if unresolved and not args.include_unresolved:
                continue
            if tgt in seen:
                continue
            seen.add(tgt)
            all_hops[depth + 1].append(tgt)
            ok, _meta = matches_filters(tgt, args, cache, vault=args.vault)
            if ok:
                matched_hops[depth + 1].append(tgt)
            q.append((tgt, depth + 1))

    result = {
        "seed": args.seed,
        "depth": args.depth,
        "filters": {
            "tags": args.tags,
            "props": args.props,
            "date_property": args.date_property,
            "date_after": str(args.date_after) if args.date_after else None,
            "date_before": str(args.date_before) if args.date_before else None,
            "modified_after": str(args.modified_after) if args.modified_after else None,
            "modified_before": str(args.modified_before) if args.modified_before else None,
        },
        "all_nodes_by_hop": {str(k): v for k, v in sorted(all_hops.items())},
        "matched_nodes_by_hop": {str(k): v for k, v in sorted(matched_hops.items())},
        "edge_count": len(edges),
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Seed: {args.seed} | depth={args.depth}")
    print("\nMatched nodes by hop:")
    for hop in sorted(matched_hops.keys()):
        print(f"  Hop {hop} ({len(matched_hops[hop])})")
        for n in sorted(matched_hops[hop]):
            print(f"    - {n}")

    total_all = sum(len(v) for v in all_hops.values())
    total_matched = sum(len(v) for v in matched_hops.values())
    print(f"\nDiscovered nodes: {total_all} | matched: {total_matched}")

    if errors:
        print("\nWarnings:")
        for e in errors[:20]:
            print(f"  - {e['note']}: {e['error']}")


if __name__ == "__main__":
    main()
