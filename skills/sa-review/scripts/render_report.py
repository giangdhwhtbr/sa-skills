#!/usr/bin/env python3
"""Write DESIGN_DIR/review-report.md from the mechanical checks plus judgement findings.

Usage: render_report.py DESIGN_DIR [--judgement FILE.json]
FILE.json is a list of {"rule", "severity", "file", "item", "message"} written by the reviewing agent.
Only review-report.md is written; no other file in the design folder is touched.
Exit codes: 0 = report written, 2 = unreadable input or missing dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REFS = HERE.parents[1] / "sa-design" / "references"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write review-report.md for a sa-design design folder.")
    parser.add_argument("design_dir", type=Path)
    parser.add_argument("--judgement", type=Path, help="JSON list of judgement-rule findings")
    parser.add_argument("--refs", type=Path, default=DEFAULT_REFS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    sys.path.insert(0, str(HERE))
    try:
        from sacheck import checks, report, review_md
    except ImportError as error:
        print(f"missing dependency: {error.name}; run: pip install pyyaml jsonschema", file=sys.stderr)
        return 2

    design_dir: Path = args.design_dir
    if not (design_dir / "design-state.yaml").is_file():
        print(f"{design_dir}: not a design folder", file=sys.stderr)
        return 2
    try:
        judgement = json.loads(args.judgement.read_text()) if args.judgement else []
        cfg, findings, exceptions = checks.run(design_dir, args.refs)
    except (OSError, ValueError) as error:
        print(f"cannot build the report: {error}", file=sys.stderr)
        return 2
    result = json.loads(report.json(findings, exceptions, cfg))
    text = review_md.render(result, judgement, checks.load_state(design_dir))
    (design_dir / "review-report.md").write_text(text)
    print(f"wrote {design_dir / 'review-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
