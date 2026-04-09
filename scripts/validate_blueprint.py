#!/usr/bin/env python3
"""Validate Home Assistant blueprint files against HA's blueprint schema."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

# HA accepts these domains for blueprints
VALID_DOMAINS = {"automation", "script", "template"}

# HA version format: YYYY.MM.PATCH  (e.g. 2025.12.4)
_VERSION_RE = re.compile(r"^\d{4}\.\d{1,2}\.\d+$")


# ---------------------------------------------------------------------------
# Custom YAML loader that ignores unknown HA-specific tags like !input
# ---------------------------------------------------------------------------

class _HaLoader(yaml.SafeLoader):
    pass


def _ignore_tag(loader: yaml.Loader, tag: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_HaLoader.add_multi_constructor("", _ignore_tag)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _err(path: str, msg: str) -> str:
    return f"  [{path}] {msg}"


def _validate_version(value: Any, path: str) -> list[str]:
    if not isinstance(value, str):
        return [_err(path, f"must be a string, got {type(value).__name__}")]
    if not _VERSION_RE.match(value):
        return [_err(path, f"must be formatted as YYYY.MM.PATCH, got '{value}'")]
    return []


def _validate_input_entry(key: str, value: Any, path: str) -> list[str]:
    """Validate a single input entry (either a plain input or a section)."""
    errors: list[str] = []

    if value is None:
        return errors  # null inputs are allowed

    if not isinstance(value, dict):
        errors.append(_err(path, "must be a mapping or null"))
        return errors

    allowed_plain = {"name", "description", "default", "selector"}
    allowed_section = {"name", "icon", "description", "collapsed", "input"}

    is_section = "input" in value

    if is_section:
        unknown = set(value) - allowed_section
        if unknown:
            errors.append(
                _err(path, f"unknown key(s) in section input: {sorted(unknown)}"))
        nested = value.get("input", {})
        if not isinstance(nested, dict):
            errors.append(_err(f"{path}.input", "must be a mapping"))
        else:
            for sub_key, sub_val in nested.items():
                errors.extend(_validate_input_entry(
                    sub_key, sub_val, f"{path}.input.{sub_key}"))
    else:
        unknown = set(value) - allowed_plain
        if unknown:
            errors.append(
                _err(path, f"unknown key(s) in input: {sorted(unknown)}"))
        if "selector" in value and not isinstance(value["selector"], dict):
            errors.append(_err(f"{path}.selector", "must be a mapping"))

    return errors


def _collect_all_input_keys(inputs: dict[str, Any]) -> list[str]:
    """Flatten all input keys including those nested inside sections."""
    keys: list[str] = []
    for key, value in inputs.items():
        if isinstance(value, dict) and "input" in value:
            keys.extend(value["input"].keys())
        else:
            keys.append(key)
    return keys


def _validate_inputs(inputs: Any, path: str) -> list[str]:
    errors: list[str] = []

    if not isinstance(inputs, dict):
        errors.append(_err(path, "must be a mapping"))
        return errors

    for key, value in inputs.items():
        errors.extend(_validate_input_entry(key, value, f"{path}.{key}"))

    # Check for duplicate input keys across sections
    all_keys = _collect_all_input_keys(inputs)
    seen: set[str] = set()
    for k in all_keys:
        if k in seen:
            errors.append(
                _err(path, f"duplicate input key '{k}' across sections"))
        seen.add(k)

    return errors


def _validate_blueprint_meta(meta: Any, path: str) -> list[str]:
    errors: list[str] = []

    if not isinstance(meta, dict):
        errors.append(_err(path, "must be a mapping"))
        return errors

    # Required: name
    if "name" not in meta:
        errors.append(_err(f"{path}.name", "required field missing"))
    elif not isinstance(meta["name"], str):
        errors.append(_err(f"{path}.name", "must be a string"))

    # Required: domain
    if "domain" not in meta:
        errors.append(_err(f"{path}.domain", "required field missing"))
    else:
        domain = meta["domain"]
        if not isinstance(domain, str):
            errors.append(_err(f"{path}.domain", "must be a string"))
        elif domain not in VALID_DOMAINS:
            errors.append(_err(
                f"{path}.domain", f"'{domain}' is not valid; must be one of {sorted(VALID_DOMAINS)}"))

    # Optional: description
    if "description" in meta and not isinstance(meta["description"], str):
        errors.append(_err(f"{path}.description", "must be a string"))

    # Optional: author
    if "author" in meta and not isinstance(meta["author"], str):
        errors.append(_err(f"{path}.author", "must be a string"))

    # Optional: source_url
    if "source_url" in meta:
        url = meta["source_url"]
        if not isinstance(url, str):
            errors.append(_err(f"{path}.source_url", "must be a string"))
        elif not (url.startswith("http://") or url.startswith("https://")):
            errors.append(_err(f"{path}.source_url",
                          "must be a http/https URL"))

    # Optional: homeassistant.min_version
    if "homeassistant" in meta:
        ha_meta = meta["homeassistant"]
        if not isinstance(ha_meta, dict):
            errors.append(_err(f"{path}.homeassistant", "must be a mapping"))
        else:
            if "min_version" in ha_meta:
                errors.extend(_validate_version(
                    ha_meta["min_version"], f"{path}.homeassistant.min_version"))

    # Optional: labels
    if "labels" in meta:
        labels = meta["labels"]
        if not isinstance(labels, list):
            errors.append(_err(f"{path}.labels", "must be a list"))
        elif not all(isinstance(lb, str) for lb in labels):
            errors.append(
                _err(f"{path}.labels", "all entries must be strings"))

    # Optional: input
    if "input" in meta:
        errors.extend(_validate_inputs(meta["input"], f"{path}.input"))

    # Unknown top-level blueprint keys
    known = {"name", "domain", "description", "author",
             "source_url", "homeassistant", "input", "labels"}
    unknown = set(meta) - known
    if unknown:
        errors.append(_err(path, f"unknown key(s): {sorted(unknown)}"))

    return errors


def validate_file(filepath: str) -> list[str]:
    errors: list[str] = []
    path = Path(filepath)

    # 1. File must exist
    if not path.exists():
        return [f"{filepath}: file not found"]

    # 2. Parse YAML
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.load(fh, Loader=_HaLoader)
    except yaml.YAMLError as exc:
        return [f"{filepath}: YAML parse error: {exc}"]

    if not isinstance(data, dict):
        return [f"{filepath}: root must be a YAML mapping"]

    # 3. Skip non-blueprint YAML files silently
    if "blueprint" not in data:
        return []

    # 4. Validate blueprint metadata
    meta_errors = _validate_blueprint_meta(data["blueprint"], "blueprint")
    for e in meta_errors:
        errors.append(f"{filepath}: {e}")

    return errors


def main(argv: list[str] | None = None) -> int:
    files = argv if argv is not None else sys.argv[1:]

    if not files:
        print("Usage: validate_blueprint.py <file.yaml> [...]")
        return 1

    all_errors: list[str] = []
    for f in files:
        all_errors.extend(validate_file(f))

    if all_errors:
        print("Blueprint validation failed:\n")
        for e in all_errors:
            print(e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
