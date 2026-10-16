"""Validate design data files against the plugin's JSON Schemas (written in YAML)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from . import catalog
from .catalog import StepSpec
from .model import Finding


def json_path(parts: Iterable[Any]) -> str:
    """Render a jsonschema error path as `a.b[0].c`."""
    out = ""
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out or "(root)"


parse = catalog.parse_yaml


def load_yaml(path: Path) -> tuple[Any, Finding | None]:
    """Parse a YAML file; return the data or a SCHEMA finding describing the parse error."""
    try:
        return parse(path.read_text()), None
    except yaml.YAMLError as error:
        return None, Finding("SCHEMA", "error", path.name, "(file)", f"not valid YAML: {error}")


def validate_data(data: Any, file_name: str, schema_file: Path) -> list[Finding]:
    """Validate already-parsed data; every schema violation becomes a SCHEMA finding."""
    validator = Draft202012Validator(parse(schema_file.read_text()))
    return [
        Finding("SCHEMA", "error", file_name, json_path(error.absolute_path), error.message)
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def validate(data_file: Path, schema_file: Path) -> list[Finding]:
    """Validate one data file; every schema violation becomes a SCHEMA finding."""
    data, problem = load_yaml(data_file)
    if problem is not None:
        return [problem]
    return validate_data(data, data_file.name, schema_file)


def schema_for(step: StepSpec, refs: Path) -> Path:
    """The schema file that validates a step's data file."""
    return refs / "schema" / step.schema
