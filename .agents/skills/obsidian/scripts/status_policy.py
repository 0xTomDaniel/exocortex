"""Exo note lifecycle policy; not the status of an agent runtime or a job.

Missing/unknown status never implies completion. This module does not change
Nitride expression semantics or guess whether an outcome has been achieved.
"""
import json
import re

import yaml

from note_metadata import MetadataError, parse_frontmatter

WORK = ('Todo', 'Doing', 'Waiting', 'Someday', 'Done', 'Closed')
FAMILIES = {
    'work': WORK,
    'document': ('Draft', 'Active', 'Closed'),
    'period': ('Planned', 'Active', 'Ended'),
    'ongoing': ('Active', 'Someday', 'Closed'),
    'learning': WORK,
    'descriptive': (),
}
TYPES = {
    'work': ('Task', 'Project', 'Historical Project', 'Customer Development Experiment',
             'Experiment', 'Deal', 'Review', 'Weekly Review', 'Sprint Review',
             'Cycle Review', 'Quarterly Review', 'Investment Review',
             'Team Planning Session', 'Planning Session', 'Work Session',
             'Research', 'Investment Research', 'Asset Assessment', 'Assessment'),
    'document': ('Plan', 'Investment Plan', 'Document', 'Legal Document', 'Report',
                 'Worksheet', 'Documentation', 'Cycle Map'),
    'period': ('Week', 'Sprint', 'Cycle', 'Quarter', 'Year', 'Bonus Week', 'Period'),
    'ongoing': ('Area', 'Creative Practice', 'Practice', 'Habit System',
                'Accountability Tracker', 'Tracker', 'Investment Portfolio',
                'Portfolio', 'Investment Watchlist', 'Watchlist', 'Queue'),
    'learning': ('Book', 'Article', 'Video', 'Resource'),
    'descriptive': ('Person', 'Company', 'Place', 'Product', 'Software', 'Family',
                    'Pet', 'Agent', 'Reference', 'Inspiration', 'Quote', 'Principle',
                    'Preference', 'Health Preference', 'Health Concern', 'Reflection',
                    'Financial Event', 'Financial Record', 'Operating Evidence',
                    'System State', 'Work', 'Research Note', 'Investment Research Note',
                    'Investment Research Source', 'Source', 'Dashboard', 'Setup',
                    'Taxonomy', 'Note Type', 'Status', 'Focus Mode', 'Entity Type',
                    'Energy', 'Context', 'Priority', 'Work Type', 'Period Type',
                    'Scope', 'Task Resolution'),
}
TYPE_FAMILY = {kind: family for family, kinds in TYPES.items() for kind in kinds}
# Only spelling/representation and explicitly accepted synonyms. Ambiguous
# Complete, Active-on-a-project, Queued and review outcomes need evidence.
ALIASES = {'Later': 'Someday', 'Incubating': 'Someday',
           'In Progress': 'Doing', 'In progress': 'Doing', 'Reading': 'Doing'}
CANONICAL = frozenset(s for values in FAMILIES.values() for s in values)


def label(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    # Exact canonical target or ordinary text. Never infer a target from a
    # display alias or silently equate unrelated qualified links by basename.
    return value[2:-2] if value.startswith('[[') and value.endswith(']]') else value


def normalize_status(value: object) -> str | None:
    name = label(value)
    name = ALIASES.get(name, name)
    return name if name in CANONICAL else None


def status_equal(left: object, right: object) -> bool:
    a, b = normalize_status(left), normalize_status(right)
    return a == b if a is not None and b is not None else left == right


def allowed_statuses(metadata: dict) -> tuple[str, ...]:
    kind = label(metadata.get('type'))
    if kind not in TYPE_FAMILY:
        raise MetadataError('status requires one recognized note type; classify the note first')
    return FAMILIES[TYPE_FAMILY[kind]]


def validate_status(metadata: dict) -> None:
    if 'status' not in metadata:
        return
    allowed = allowed_statuses(metadata)
    value = metadata['status']
    if not allowed:
        raise MetadataError('this descriptive note type has no generic status; preserve meaning in history or a specific property')
    if value not in tuple(f'[[{name}]]' for name in allowed):
        raise MetadataError('status must be one canonical link: ' + ', '.join(allowed))
    if value == '[[Closed]]':
        resolution = metadata.get('resolution')
        if not isinstance(resolution, str) or not resolution.strip():
            raise MetadataError('Closed requires an explicit nonblank resolution')


def repair_status(text: str) -> str:
    """Repair unambiguous representations only; preserve all other bytes/text."""
    metadata = parse_frontmatter(text)
    if 'status' not in metadata:
        return text
    old = metadata['status']
    normalized = normalize_status(old)
    # Parking a legacy Later commitment needs evidence; don't automate it.
    if label(old) == 'Later' or normalized not in allowed_statuses(metadata):
        return text
    new = f'[[{normalized}]]'
    if old == new:
        return text
    candidate = dict(metadata, status=new)
    validate_status(candidate)
    match = re.match(r'\A---\r?\n(.*?)^---[ \t]*\r?$', text, re.M | re.S)
    node = yaml.compose(match.group(1))
    for key, value in node.value:
        if key.value == 'status':
            start = match.start(1) + value.start_mark.index
            end = match.start(1) + value.end_mark.index
            result = text[:start] + json.dumps(new) + text[end:]
            if parse_frontmatter(result) != candidate:
                raise MetadataError('status repair changed unrelated metadata')
            return result
    raise MetadataError('status location unavailable')
