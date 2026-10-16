#!/usr/bin/env python3
"""Draw the diagrams of a sa-design design folder (draw.io + Mermaid, optional PNG).

Usage: diagrams.py DESIGN_DIR [--only KEY ...] [--png] [--force] [--refs DIR]
Exit codes: 0 = diagrams written or already up to date, 1 = the design data has error findings (nothing
written), 2 = usage error, missing Python package, or Node.js / elkjs missing for a graph diagram.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
DEFAULT_REFS = SKILLS / "sa-design" / "references"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Draw the diagrams of a sa-design design folder.")
    parser.add_argument("design_dir", type=Path)
    parser.add_argument("--only", nargs="+", metavar="KEY", help="draw only these steps (e.g. context-map saga)")
    parser.add_argument("--png", action="store_true", help="also export one PNG per page (needs draw.io desktop)")
    parser.add_argument("--force", action="store_true", help="redraw even when the data has not changed")
    parser.add_argument("--refs", type=Path, default=DEFAULT_REFS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    sys.path[:0] = [str(HERE), str(SKILLS / "sa-review" / "scripts")]
    try:
        from sadiagram import elk, run
    except ImportError as error:
        print(f"missing dependency: {error.name}; run: pip install pyyaml jsonschema", file=sys.stderr)
        return 2

    try:
        result = run.run(args.design_dir, args.refs, only=args.only, png=args.png, force=args.force)
    except run.UsageError as error:
        print(str(error), file=sys.stderr)
        return 2
    except elk.LayoutError as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print(f"cannot read or write the design folder: {error}", file=sys.stderr)
        return 2

    if result.exit_code == 1:
        print("not drawn: the design data has errors; fix them with /sa-design (see /sa-review):")
        print("\n".join(f"  {line}" for line in result.errors))
        return 1
    if result.exit_code == 2:
        print("\n".join(result.errors), file=sys.stderr)
        return 2
    lines = [*(f"wrote {w}" for w in result.written), *(f"unchanged {u}" for u in result.unchanged),
             *(f"skipped {s}" for s in result.skipped)]
    if args.png and (result.png_exported or result.png_cached):
        lines.append(f"png: {result.png_exported} exported, {result.png_cached} cached")
    lines += [f"warning: {w}" for w in result.warnings]
    if not result.written and not result.unchanged:
        lines.append("nothing to draw: no drawable step (02-10) is done")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
