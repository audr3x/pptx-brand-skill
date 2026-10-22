#!/usr/bin/env python3
"""Check a deck outline against what build_deck.py and build_slides.py actually read.

Usage:
    python3 scripts/check_outline.py examples/outline.yaml
    python3 scripts/check_outline.py --target slides my-outline.yaml
    python3 scripts/check_outline.py --markdown docs/PROMPTING.md

Errors fail the check (exit 1); the builders refuse the same outline. Warnings print
but pass. --target picks which builder's limits to warn about: pptx, slides, or both.
The rules live in outline_rules.py.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outline_rules import KNOWN_LAYOUTS, load, prepare  # noqa: E402,F401


def check(outline: Any, target: str, label: str) -> tuple[list[str], list[str]]:
    _, errors, warnings = prepare(outline, target, label)
    return errors, warnings


def markdown_outlines(path: Path) -> list[tuple[str, Any]]:
    import yaml

    found = []
    for n, block in enumerate(re.findall(r"```yaml\n(.*?)```", path.read_text(), re.S), 1):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "slides" in data:
            found.append((f"{path.name} yaml block {n}", data))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--markdown", type=Path, action="append", default=[], help="Check every yaml block with 'slides:'")
    parser.add_argument("--target", choices=("pptx", "slides", "both"), default="both")
    args = parser.parse_args(argv)
    outlines = []
    for p in args.paths:
        try:
            outlines.append((str(p), load(p)))
        except SystemExit as exc:
            print(f"error: {exc}")
            print(f"FAIL: {p}")
            return 1
    for md in args.markdown:
        blocks = markdown_outlines(md)
        if not blocks:
            print(f"error: {md} has no yaml outline blocks", file=sys.stderr)
            return 1
        outlines.extend(blocks)
    if not outlines:
        parser.error("pass an outline or --markdown FILE")
    failed = False
    for label, data in outlines:
        errors, warnings = check(data, args.target, label)
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
        failed = failed or bool(errors)
        print(f"{'FAIL' if errors else 'ok'}: {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
