# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6,<7"]
# ///
"""Audit/repair standalone status comparisons in saved Base filters.

Requires explicit --attention to remove legacy Reviewed exclusions. Does not
change dates, membership or the meaning of the generic Base evaluator.
"""
import argparse
import json
from pathlib import Path
import re

import yaml

from note_metadata import MetadataError
from status_policy import ALIASES, label, normalize_status
from validate_notes import save_repair


def rewrite(text: str, attention: bool = False) -> str:
    # Compose syntax nodes without YAML 1.1 scalar coercion. Edit only filter
    # spans: the rest of the document, including comments and CRLF, stays intact.
    base = yaml.compose(text, Loader=yaml.BaseLoader)
    if not isinstance(base, yaml.MappingNode):
        raise MetadataError('Base must be a mapping')
    events = list(yaml.parse(text))
    if any(isinstance(event, yaml.AliasEvent) or getattr(event, 'anchor', None) for event in events):
        raise MetadataError('anchored/aliased Bases require explicit inspection; no automatic repair')
    edits = []

    def mapping(node):
        if not isinstance(node, yaml.MappingNode):
            raise MetadataError('expected Base mapping')
        result = {}
        for key, child in node.value:
            if not isinstance(key, yaml.ScalarNode) or key.value in result:
                raise MetadataError('non-scalar or duplicate Base key')
            result[key.value] = child
        return result

    def validate(node):
        if isinstance(node, yaml.MappingNode):
            for child in mapping(node).values():
                validate(child)
        elif isinstance(node, yaml.SequenceNode):
            for child in node.value:
                validate(child)

    def filters(node):
        if isinstance(node, yaml.MappingNode):
            for child in mapping(node).values():
                filters(child)
            return
        if isinstance(node, yaml.SequenceNode):
            for child in node.value:
                filters(child)
            return
        value = node.value.strip()
        match = re.fullmatch(r"status\s*(==|!=)\s*(\"[^\"\n]*\"|'[^'\n]*')", value)
        if not match:
            return
        operator, raw = match.groups()
        old = raw[1:-1]
        if attention and operator == '!=' and label(old) == 'Reviewed':
            result = 'true'
        else:
            name = normalize_status(old)
            if name is None:
                return
            names = [name] + [alias for alias, target in ALIASES.items() if target == name]
            variants = [variant for n in names for variant in (f'[[{n}]]', n)]
            joiner = ' && ' if operator == '!=' else ' || '
            result = '(' + joiner.join(f'status {operator} {json.dumps(v)}' for v in variants) + ')'
        replacement = json.dumps(result)
        # Block scalar spans include the final line ending. Retain that separator
        # so the next YAML key cannot become part of the replacement line.
        original = text[node.start_mark.index:node.end_mark.index]
        if original.endswith('\r\n'):
            replacement += '\r\n'
        elif original.endswith('\n'):
            replacement += '\n'
        edits.append((node.start_mark.index, node.end_mark.index, replacement))

    validate(base)
    fields = mapping(base)
    if 'filters' in fields:
        filters(fields['filters'])
    if 'views' in fields:
        if not isinstance(fields['views'], yaml.SequenceNode):
            raise MetadataError('Base views must be a list')
        for view in fields['views'].value:
            fields_view = mapping(view)
            if 'filters' in fields_view:
                filters(fields_view['filters'])
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--attention', action='store_true')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup-dir', type=Path)
    args = parser.parse_args()
    if args.apply and not args.backup_dir:
        parser.error('--apply requires --backup-dir outside the vault')
    reports, errors = [], []
    for path in args.paths:
        try:
            original = path.read_bytes()
            candidate = rewrite(original.decode('utf-8'), args.attention).encode('utf-8')
            if args.apply and candidate != original:
                save_repair(path, original, candidate, args.backup_dir)
            reports.append({'path': str(path), 'changed': candidate != original, 'applied': args.apply})
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            errors.append({'path': str(path), 'error': str(exc)})
    print(json.dumps({'bases': reports, 'errors': errors}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
