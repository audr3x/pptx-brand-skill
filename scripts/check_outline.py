#!/usr/bin/env python3
"""Check a deck outline against what build_deck.py and build_slides.py actually read.

Usage:
    python3 scripts/check_outline.py examples/outline.yaml
    python3 scripts/check_outline.py --target slides my-outline.yaml
    python3 scripts/check_outline.py --markdown docs/PROMPTING.md

Errors fail the check (exit 1). Warnings print but pass. --target picks which
builder's limits to warn about: pptx, slides, or both (default).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_slides import LAYOUT_ALIASES, MAX_BULLETS  # noqa: E402

KNOWN_LAYOUTS = {v.lower() for v in LAYOUT_ALIASES.values()}
TOP_FIELDS = {"title", "subtitle", "date", "author", "subject", "footer", "slides"}
SLIDE_FIELDS = {
    "layout", "intent", "title", "subtitle", "subhead", "date", "eyebrow", "kicker",
    "statement", "caption", "bullets", "body", "items", "right", "headers", "rows",
    "chart", "name", "role", "company", "org", "image", "footer", "notes",
}
CHART_TYPES_PPTX = {"column", "bar", "line", "pie"}
MAX_ITEMS = 3
MAX_TABLE_ROWS = 6
PICTURE_LAYOUTS = {"intro_one", "intro_three", "intro_four", "photo-right", "3-photos"}


def resolve_layout(spec: dict[str, Any]) -> str:
    intent = str(spec.get("layout") or spec.get("intent") or "content")
    return LAYOUT_ALIASES.get(intent.strip().lower(), intent).strip()


def count_bullets(items: Any) -> int:
    if isinstance(items, str):
        return 1
    total = 0
    for entry in items or []:
        total += 1
        if isinstance(entry, dict):
            total += count_bullets(entry.get("children") or entry.get("bullets") or [])
    return total


def check(outline: Any, target: str, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    slides_target = target in {"slides", "both"}
    if not isinstance(outline, dict) or not isinstance(outline.get("slides"), list) or not outline["slides"]:
        return [f"{label}: outline needs a top-level 'slides' list"], warnings
    for key in outline:
        if key not in TOP_FIELDS:
            warnings.append(f"{label}: top-level '{key}' is not read by either builder")
    for i, spec in enumerate(outline["slides"], 1):
        where = f"{label} slide {i}"
        if not isinstance(spec, dict):
            errors.append(f"{where}: each slide must be a mapping")
            continue
        layout = resolve_layout(spec)
        if layout.lower() not in KNOWN_LAYOUTS:
            errors.append(f"{where}: unknown layout {spec.get('layout') or spec.get('intent')!r}")
        for key in spec:
            if key not in SLIDE_FIELDS:
                errors.append(f"{where}: field '{key}' is not read by either builder")
        bullets = spec.get("bullets") if spec.get("bullets") is not None else spec.get("body")
        if slides_target and isinstance(bullets, list) and any(
            isinstance(b, dict) and (b.get("children") or b.get("bullets")) for b in bullets
        ):
            warnings.append(f"{where}: Google Slides shows nested bullets at the top level")
        if bullets is not None and count_bullets(bullets) > MAX_BULLETS:
            warnings.append(f"{where}: {count_bullets(bullets)} bullets, builders keep the first {MAX_BULLETS}")
        items = spec.get("items") or spec.get("right")
        if items is not None:
            if not isinstance(items, list) or not all(isinstance(it, dict) for it in items):
                errors.append(f"{where}: items must be a list of {{title, body}} mappings")
            elif len(items) > MAX_ITEMS:
                warnings.append(f"{where}: {len(items)} items, builders keep the first {MAX_ITEMS}")
        intent = str(spec.get("layout") or spec.get("intent") or "").strip().lower()
        if intent == "table" or spec.get("headers") is not None:
            headers = spec.get("headers")
            if not headers:
                errors.append(f"{where}: table slides need 'headers'")
            rows = spec.get("rows") or []
            if len(rows) > MAX_TABLE_ROWS:
                warnings.append(f"{where}: {len(rows)} table rows, split the table (about {MAX_TABLE_ROWS} rows fit)")
        if intent == "chart" or spec.get("chart") is not None:
            chart = spec.get("chart") or {}
            cats = chart.get("categories") or []
            series = chart.get("series") or []
            if not cats or not series:
                errors.append(f"{where}: chart needs chart.categories and chart.series")
            kind = str(chart.get("type") or "column").lower()
            if kind not in CHART_TYPES_PPTX:
                errors.append(f"{where}: chart type {kind!r} not supported (column, bar, line, pie)")
            elif slides_target and kind != "column":
                warnings.append(f"{where}: Google Slides draws {kind!r} as clustered columns")
            for s in series:
                values = s.get("values") or []
                if len(values) != len(cats):
                    errors.append(f"{where}: series {s.get('name')!r} has {len(values)} values for {len(cats)} categories")
                if not all(isinstance(v, (int, float)) for v in values):
                    errors.append(f"{where}: series {s.get('name')!r} values must be numbers")
        if layout.lower() == "photo-right" and (spec.get("bullets") or spec.get("body")):
            warnings.append(f"{where}: photo-right has no body area; bullets are dropped")
        if layout.lower() == "3-photos":
            warnings.append(f"{where}: 3-photos fills only the first photo slot from 'image'")
        image = spec.get("image")
        if image:
            if layout.lower() not in PICTURE_LAYOUTS:
                warnings.append(f"{where}: 'image' only fills a picture placeholder (intro, photo-right); ignored on {layout}")
            path = Path(str(image))
            if not path.is_file() and not (ROOT / str(image)).is_file():
                errors.append(f"{where}: image not found: {image}")
            if slides_target:
                warnings.append(f"{where}: Google Slides ignores 'image'; insert it by hand (Insert > Image)")
        if slides_target and spec.get("notes"):
            warnings.append(f"{where}: speaker notes are written to PowerPoint only")
        if slides_target and layout.lower().startswith("intro_") and any(spec.get(k) for k in ("name", "role", "company")):
            warnings.append(f"{where}: Google Slides fills only 'title' on intro layouts")
    return errors, warnings


def load(path: Path) -> Any:
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


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
    outlines = [(str(p), load(p)) for p in args.paths]
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
