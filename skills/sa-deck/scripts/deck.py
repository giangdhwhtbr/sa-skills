#!/usr/bin/env python3
"""Build the presentation of a sa-design design folder: deck.html and deck.pptx from design/deck/deck.yaml.

Usage: deck.py DESIGN_DIR [--outline] [--minutes N] [--force] [--refs DIR]
Exit codes: 0 = deck written, unchanged, or outline printed; 1 = deck.yaml has error findings (nothing written);
2 = usage error, missing deck.yaml, missing Python package, or the PowerPoint renderer failed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
DEFAULT_REFS = SKILLS / "sa-deck" / "references"
SA_REFS = SKILLS / "sa-design" / "references"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the presentation of a sa-design design folder.")
    parser.add_argument("design_dir", type=Path)
    parser.add_argument("--outline", action="store_true", help="print a draft deck.yaml for this design")
    parser.add_argument("--minutes", type=int, default=20, help="talk length for --outline (default 20)")
    parser.add_argument("--force", action="store_true", help="render even when nothing changed")
    parser.add_argument("--refs", type=Path, default=DEFAULT_REFS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not 1 <= args.minutes <= 120:
        print("--minutes must be between 1 and 120", file=sys.stderr)
        return 2

    sys.path[:0] = [str(HERE), str(SKILLS / "sa-diagrams" / "scripts"), str(SKILLS / "sa-review" / "scripts")]
    try:
        from sadeck import run
    except ImportError as error:
        print(f"missing dependency: {error.name}; run: pip install pyyaml jsonschema", file=sys.stderr)
        return 2

    try:
        result = run.run(args.design_dir, args.refs, SA_REFS, outline=args.outline, minutes=args.minutes,
                         force=args.force)
    except run.UsageError as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print(f"cannot read or write the design folder: {error}", file=sys.stderr)
        return 2

    if args.outline:
        sys.stdout.write(result.outline)
        return 0
    if result.exit_code == 1:
        print("not rendered: deck.yaml has errors; fix them and run again:")
        print("\n".join(f"  {line}" for line in result.errors))
        return 1
    if result.exit_code == 2:
        print("\n".join(result.errors), file=sys.stderr)
        return 2
    lines = ["unchanged deck"] if result.unchanged else [f"wrote {w}" for w in result.written]
    lines += [f"warning: {w}" for w in result.warnings]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
