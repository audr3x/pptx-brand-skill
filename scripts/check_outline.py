#!/usr/bin/env python3
"""Check a deck outline against what build_deck.py and build_slides.py actually read.

Usage:
    python3 scripts/check_outline.py examples/outline.yaml
    python3 scripts/check_outline.py --target slides my-outline.yaml
    python3 scripts/check_outline.py --markdown docs/PROMPTING.md
    python3 scripts/check_outline.py --prompt request.md --prompt notes.txt my-outline.yaml

Errors fail the check (exit 1); the builders refuse the same outline. Warnings print
but pass. --target picks which builder's limits to warn about: pptx, slides, or both.
--prompt points at what the user gave you (their message saved to a file, their notes);
dates and figures in the outline that are not in it are warned about. The rules live in
outline_rules.py and provenance.py.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outline_rules import KNOWN_LAYOUTS, drawn_strings, load, prepare  # noqa: E402,F401
from provenance import unsourced_dates, unsourced_figures  # noqa: E402


def check(outline: Any, target: str, label: str, source: str | None = None) -> tuple[list[str], list[str]]:
    outline, errors, warnings = prepare(outline, target, label)
    if source is not None and not errors:
        warnings += unsourced(outline, source, label)
    return errors, warnings


def unsourced(outline: dict[str, Any], source: str, label: str) -> list[str]:
    """Dates and figures on the slides (or in notes) that the source text never mentions."""
    out = []
    for i, spec in enumerate(outline["slides"], 1):
        if not isinstance(spec, dict):
            continue
        text = " ".join(t for _, t in drawn_strings(spec, "pptx")) + " " + str(spec.get("notes") or "")
        for d in unsourced_dates(text, source):
            out.append(f"{label} slide {i}: date '{d}' is not in the prompt. Write TODO and ask unless the user gave it")
        for n in unsourced_figures(text, source):
            out.append(f"{label} slide {i}: figure {n:g} is not in the prompt. Use only numbers the user gave")
    return out


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
    parser.add_argument("--prompt", type=Path, action="append", default=[],
                        help="File with the user's request or notes (repeatable). Warns on dates and figures not in it")
    args = parser.parse_args(argv)
    source = "\n".join(p.read_text() for p in args.prompt) if args.prompt else None
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
        errors, warnings = check(data, args.target, label, source)
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
        failed = failed or bool(errors)
        print(f"{'FAIL' if errors else 'ok'}: {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
