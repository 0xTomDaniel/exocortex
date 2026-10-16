"""Strict frontmatter parsing shared by note validation and graph filtering."""

import re
import datetime as dt

import yaml


class MetadataError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise MetadataError("property names must be strings")
        if key in mapping:
            raise MetadataError(f"duplicate property: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def parse_frontmatter(text: str) -> dict:
    if not text or not text.startswith(("---\n", "---\r\n")):
        return {}
    match = re.match(r"\A---\r?\n(.*?)^---[ \t]*\r?$", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise MetadataError("missing closing frontmatter delimiter")
    try:
        result = yaml.load(match.group(1), Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" near line {mark.line + 2}" if mark else ""
        raise MetadataError("invalid YAML" + where) from exc
    except MetadataError:
        raise
    except ValueError as exc:
        raise MetadataError("invalid YAML calendar value") from exc
    if result is None:
        return {}
    if not isinstance(result, dict):
        raise MetadataError("frontmatter must be a mapping")
    return result


def validate_attention_dates(metadata: dict) -> None:
    """Exo's attention/period fields use calendar days, not datetimes or coercion."""
    for key in ('due', 'review_on', 'week_start', 'week_end'):
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            continue
        if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            try:
                dt.date.fromisoformat(value)
                continue
            except ValueError:
                pass
        raise MetadataError(f'{key} must be a valid YYYY-MM-DD calendar date or absent/null; no implicit timestamp, scalar or list coercion')
