"""Render check results as text or JSON."""

from __future__ import annotations

import json as _json
from dataclasses import asdict

from .config import EffectiveConfig
from .model import Finding


def ordered(findings: list[Finding]) -> list[Finding]:
    """Errors first, then warnings; stable within each group."""
    return [f for f in findings if f.severity == "error"] + [f for f in findings if f.severity != "error"]


def config_dict(cfg: EffectiveConfig) -> dict[str, object]:
    """The effective configuration as plain data."""
    return {"profile": cfg.profile, "cloud": cfg.cloud, "options": cfg.options, "overrides": cfg.overrides}


def text(findings: list[Finding], exceptions: list[dict[str, str]], cfg: EffectiveConfig) -> str:
    """One line per finding (`ERROR|WARN <rule> <file> <item>: <message>`), then a summary line."""
    lines = [f"{f.severity.upper()} {f.rule} {f.file} {f.item}: {f.message}" for f in ordered(findings)]
    lines += [f"EXCEPTION {e['rule']} {e['step']}: {e['reason']}" for e in exceptions]
    errors = sum(1 for f in findings if f.severity == "error")
    lines.append(f"{errors} errors, {len(findings) - errors} warnings")
    return "\n".join(lines) + "\n"


def json(findings: list[Finding], exceptions: list[dict[str, str]], cfg: EffectiveConfig) -> str:
    """Findings, exceptions and the effective configuration as JSON."""
    payload = {
        "config": config_dict(cfg),
        "findings": [asdict(f) for f in ordered(findings)],
        "exceptions": exceptions,
    }
    return _json.dumps(payload, indent=2) + "\n"
