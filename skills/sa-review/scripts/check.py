#!/usr/bin/env python3
"""Mechanical checks of a sa-design design folder.

Usage: check.py DESIGN_DIR [--step KEY] [--format text|json] [--dependents KEY] [--changed] [--refs DIR]
Exit codes: 0 = no error findings, 1 = at least one error finding, 2 = usage error, unreadable input
or missing dependency (pip install pyyaml jsonschema).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REFS = HERE.parents[1] / "sa-design" / "references"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a sa-design design folder.")
    parser.add_argument("design_dir", type=Path)
    parser.add_argument("--step", help="check one step only (its key, e.g. context-map)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--dependents", metavar="KEY", help="print the steps that read this step's data")
    parser.add_argument("--changed", action="store_true", help="print files edited after their recorded hash")
    parser.add_argument("--refs", type=Path, default=DEFAULT_REFS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    sys.path.insert(0, str(HERE))
    try:
        from sacheck import catalog, checks, report
    except ImportError as error:
        print(f"missing dependency: {error.name}; run: pip install pyyaml jsonschema", file=sys.stderr)
        return 2

    design_dir: Path = args.design_dir
    if not (design_dir / "sa-config.yaml").is_file() or not (design_dir / "design-state.yaml").is_file():
        print(f"{design_dir}: not a design folder (sa-config.yaml and design-state.yaml are required)", file=sys.stderr)
        return 2

    if args.dependents:
        steps = catalog.load_steps(args.refs)
        if args.dependents not in {s.key for s in steps}:
            print(f"unknown step '{args.dependents}'", file=sys.stderr)
            return 2
        print("\n".join(checks.dependents(args.dependents, steps)))
        return 0
    if args.changed:
        changed = checks.changed_files(design_dir)
        if changed:
            print("\n".join(changed))
        return 0

    try:
        cfg, findings, exceptions = checks.run(design_dir, args.refs, args.step)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print(f"cannot read the design folder: {error}", file=sys.stderr)
        return 2
    render = report.json if args.format == "json" else report.text
    sys.stdout.write(render(findings, exceptions, cfg))
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
