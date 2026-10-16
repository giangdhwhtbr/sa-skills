"""Render design/review-report.md from check.py JSON output plus judgement-rule findings."""

from __future__ import annotations

from typing import Any


def _yaml_value(value: Any) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def _finding_rows(findings: list[dict[str, Any]]) -> list[str]:
    if not findings:
        return ["None."]
    rows = ["| Rule | File | Item | Finding |", "|---|---|---|---|"]
    rows += [f"| {f['rule']} | {f['file']} | {f['item']} | {f['message']} |" for f in findings]
    return rows


def render(result: dict[str, Any], judgement: list[dict[str, Any]], state: dict[str, Any]) -> str:
    """Build the report: configuration first, then summary, errors, warnings, exceptions and step status."""
    cfg = result["config"]
    findings = list(result["findings"]) + list(judgement)
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] != "error"]

    lines = ["# Design review", "", "## Configuration", ""]
    lines.append(f"- Profile: {cfg['profile']}")
    lines.append(f"- Cloud: {cfg['cloud']}")
    options = [
        f"{step}.{name} = {_yaml_value(value)}"
        for step, values in sorted(cfg["options"].items()) for name, value in sorted(values.items())
    ]
    lines.append("- Options: " + ("; ".join(options) if options else "none"))
    overrides = [f"{rule}: {severity}" for rule, severity in sorted(cfg["overrides"].items())]
    lines.append("- Rule overrides: " + (", ".join(overrides) if overrides else "none"))

    lines += ["", "## Summary", ""]
    verdict = "Ready" if not errors else "Not ready"
    lines.append(f"{verdict}: {len(errors)} errors, {len(warnings)} warnings, "
                 f"{len(result['exceptions'])} accepted exceptions.")

    lines += ["", "## Errors", "", *_finding_rows(errors)]
    lines += ["", "## Warnings", "", *_finding_rows(warnings)]

    lines += ["", "## Accepted exceptions", ""]
    if result["exceptions"]:
        lines += ["| Step | Rule | Reason |", "|---|---|---|"]
        lines += [f"| {e['step']} | {e['rule']} | {e['reason']} |" for e in result["exceptions"]]
    else:
        lines.append("None.")

    lines += ["", "## Step status", "", "| Step | Status | Open questions |", "|---|---|---|"]
    for step in state.get("steps", []):
        open_questions = "; ".join(step.get("open_questions") or []) or "-"
        lines.append(f"| {step['key']} | {step['status']} | {open_questions} |")
    return "\n".join(lines) + "\n"
