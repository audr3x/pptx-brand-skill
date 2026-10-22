"""What an outline may contain, shared by check_outline.py, build_deck.py, and build_slides.py.

prepare() normalizes an outline (YAML dates and numbers to text, string bullets to lists,
dict table rows to ordered lists) and returns it with errors and warnings. Builders refuse
to build when there are errors, so a bad outline fails with a message instead of a traceback.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_ALIASES = {
    "title": "Title Slide",
    "cover": "Title Slide",
    "title-slide": "Title Slide",
    "section": "Section Title",
    "section-title": "Section Title",
    "divider": "Section Title",
    "content": "Title and Content",
    "title-and-content": "Title and Content",
    "bullets": "Title and Content",
    "two-column": "1/2_Headline",
    "two-col": "1/2_Headline",
    "headline": "1/2_Headline",
    "table": "Title Only",
    "chart": "Title Only",
    "closing": "Bumper Slide",
    "bumper": "Bumper Slide",
    "close": "Bumper Slide",
    "intro": "Intro_One",
    "intro-one": "Intro_One",
    "intro-three": "Intro_Three",
    "intro-four": "Intro_Four",
    "blank": "Blank White Background",
    "title-only": "Title Only",
    "title-only-alt": "Title Only_Alt",
    "photo-right": "Photo-Right",
    "photos": "3-Photos",
    "layout-1": "Layout 1",
}

COMMON_FIELDS = {"layout", "intent", "notes", "footer"}
INTRO_FIELDS = {"title", "name", "role", "subtitle", "company", "org", "image"}
# Fields each layout draws. Anything else on that slide is dropped by both builders.
LAYOUT_FIELDS = {
    "Title Slide": {"title", "subtitle", "subhead", "date"},
    "Section Title": {"eyebrow", "kicker", "title", "statement"},
    "Title and Content": {"title", "bullets", "body"},
    "1/2_Headline": {"title", "items", "right"},
    "1/2 Headline_Alt": {"title", "items", "right"},
    "Title Only": {"title", "headers", "rows", "chart"},
    "Title Only_Alt": {"title", "headers", "rows", "chart"},
    "Bumper Slide": {"title", "caption"},
    "Intro_One": INTRO_FIELDS,
    "Intro_Three": INTRO_FIELDS,
    "Intro_Four": INTRO_FIELDS,
    "Photo-Right": {"title", "image"},
    "3-Photos": {"title", "image"},
    "Blank White Background": set(),
    "Layout 1": {"title"},
}
KNOWN_LAYOUTS = {name.lower() for name in LAYOUT_FIELDS}
SLIDE_FIELDS = COMMON_FIELDS | set().union(*LAYOUT_FIELDS.values())
TOP_FIELDS = {"title", "subtitle", "date", "author", "subject", "footer", "slides"}
TEXT_FIELDS = SLIDE_FIELDS - {"layout", "intent", "bullets", "body", "items", "right", "headers", "rows", "chart", "image"}

MAX_BULLETS = 6
MAX_ITEMS = 3
MAX_TABLE_ROWS = 6
MAX_TABLE_COLS = 6
MAX_SERIES = 5
MAX_CATEGORIES = 12
CHART_TYPES = {"column", "bar", "line", "pie"}
PICTURE_LAYOUTS = {"intro_one", "intro_three", "intro_four", "photo-right", "3-photos"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}
# Characters before a title wraps past the space its layout gives it (measured on renders).
TITLE_LIMITS = {
    "Title Slide": 60,
    "Section Title": 70,
    "Title and Content": 42,
    "Title Only": 42,
    "Title Only_Alt": 42,
    "1/2_Headline": 45,
    "1/2 Headline_Alt": 45,
    "Photo-Right": 45,
}
EYEBROW_LIMIT = 40
BULLET_LIMIT = 120
ITEM_BODY_LIMIT = 120


def canonical_layout(spec: dict[str, Any]) -> str:
    intent = str(spec.get("layout") or spec.get("intent") or "content")
    name = LAYOUT_ALIASES.get(intent.strip().lower(), intent).strip()
    for known in LAYOUT_FIELDS:
        if known.lower() == name.lower():
            return known
    return name


def load(path: Path) -> Any:
    """Read YAML or JSON. Syntax errors become one readable line."""
    text = Path(path).read_text()
    try:
        if Path(path).suffix.lower() in {".yaml", ".yml"}:
            import yaml

            return yaml.safe_load(text)
        return json.loads(text)
    except ImportError as exc:
        raise SystemExit("PyYAML is required for .yaml outlines. pip install -r requirements.txt") from exc
    except Exception as exc:  # yaml.YAMLError or json.JSONDecodeError
        first = str(exc).strip().splitlines()
        mark = getattr(exc, "problem_mark", None)
        where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark is not None else ""
        raise SystemExit(f"{path}: not valid {'YAML' if str(path).endswith(('yml', 'yaml')) else 'JSON'}{where}: "
                         f"{getattr(exc, 'problem', None) or (first[0] if first else exc)}. "
                         "Quote text that contains a colon, and close every bracket.")


def _text(value: Any, where: str, field: str, errors: list[str]) -> Any:
    if value is None or isinstance(value, str):
        return value if value is None or field == "notes" else re.sub(r"[\t\r\n]+", " ", value)
    if isinstance(value, bool):
        errors.append(f"{where}: {field} {value!r} came from an unquoted yes/no/on/off/true/false. Put it in quotes")
        return str(value)
    if isinstance(value, (int, float)):
        return f"{value:g}" if isinstance(value, float) else str(value)
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    if field == "notes" and isinstance(value, list):
        return "\n".join(str(v) for v in value)
    errors.append(f"{where}: {field} must be text, not {type(value).__name__}")
    return str(value)


def _bullets(value: Any, where: str, errors: list[str]) -> list[Any]:
    if isinstance(value, (str, int, float, bool, _dt.date)):
        value = [value]
    if not isinstance(value, list):
        errors.append(f"{where}: bullets must be a list")
        return []
    out = []
    for b in value:
        if isinstance(b, dict):
            kids = b.get("children") or b.get("bullets") or []
            node = {"text": _text(b.get("text") or b.get("title") or "", where, "bullet", errors)}
            if kids:
                node["children"] = _bullets(kids, where, errors)
            out.append(node)
        else:
            out.append(_text(b, where, "bullet", errors))
    return out


def count_bullets(items: Any) -> int:
    if isinstance(items, str):
        return 1
    total = 0
    for entry in items or []:
        total += 1
        if isinstance(entry, dict):
            total += count_bullets(entry.get("children") or entry.get("bullets") or [])
    return total


def _bullet_texts(items: list[Any]) -> list[str]:
    out = []
    for b in items:
        if isinstance(b, dict):
            out.append(str(b.get("text") or ""))
            out.extend(_bullet_texts(b.get("children") or []))
        else:
            out.append(str(b))
    return out


def _image_errors(image: Any, where: str) -> list[str]:
    raw = str(image)
    if re.match(r"^[a-z]+://", raw, re.I):
        return [f"{where}: image must be a file in the repository, not a URL ({raw}). Download it first"]
    path = Path(raw) if Path(raw).is_absolute() else ROOT / raw
    if not path.is_file():
        return [f"{where}: image not found: {raw}"]
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return [f"{where}: image must be PNG, JPEG, or GIF: {raw}"]
    try:
        from PIL import Image

        with Image.open(path) as im:
            im.verify()
    except ImportError:
        pass
    except Exception:
        return [f"{where}: image file cannot be read as a picture: {raw}"]
    return []


def _chart(spec: dict[str, Any], where: str, slides_target: bool, errors: list[str], warnings: list[str]) -> None:
    chart = spec.get("chart")
    if not isinstance(chart, dict):
        errors.append(f"{where}: chart needs chart.categories and chart.series (a mapping)")
        return
    cats = chart.get("categories")
    series = chart.get("series")
    if not isinstance(cats, list) or not cats or not isinstance(series, list) or not series:
        errors.append(f"{where}: chart needs chart.categories and chart.series lists")
        return
    chart["categories"] = [_text(c, where, "category", errors) for c in cats]
    kind = str(chart.get("type") or "column").lower()
    if kind not in CHART_TYPES:
        errors.append(f"{where}: chart type {kind!r} not supported (column, bar, line, pie)")
    else:
        chart["type"] = kind
        if slides_target and kind != "column":
            warnings.append(f"{where}: Google Slides draws {kind!r} as clustered columns")
    if len(series) > MAX_SERIES:
        warnings.append(f"{where}: {len(series)} series; colors repeat after {MAX_SERIES} and the legend gets crowded")
    if len(cats) > MAX_CATEGORIES:
        warnings.append(f"{where}: {len(cats)} categories; labels get crowded after about {MAX_CATEGORIES}")
    if kind == "pie" and len(series) > 1:
        warnings.append(f"{where}: a pie shows only the first series")
    for s in series:
        if not isinstance(s, dict):
            errors.append(f"{where}: each series needs a name and values, like {{name: Revenue, values: [1, 2]}}")
            continue
        s["name"] = _text(s.get("name") or "", where, "series name", errors)
        values = s.get("values")
        if not isinstance(values, list) or len(values) != len(cats):
            n = len(values) if isinstance(values, list) else 0
            errors.append(f"{where}: series {s['name']!r} has {n} values for {len(cats)} categories")
            continue
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            errors.append(f"{where}: series {s['name']!r} values must be plain numbers (write 12, not \"12%\" or null)")
            continue
        if kind == "pie" and any(v < 0 for v in values):
            errors.append(f"{where}: pie values cannot be negative; use a column chart")


def _table(spec: dict[str, Any], where: str, errors: list[str], warnings: list[str]) -> None:
    headers = spec.get("headers")
    if not isinstance(headers, list) or not headers:
        errors.append(f"{where}: table slides need a 'headers' list")
        return
    headers = spec["headers"] = [_text(h, where, "header", errors) for h in headers]
    rows = spec.get("rows") or []
    if not isinstance(rows, list):
        errors.append(f"{where}: rows must be a list of rows")
        return
    fixed = []
    for n, row in enumerate(rows, 1):
        if isinstance(row, dict):
            extra = [k for k in row if k not in headers]
            if extra:
                warnings.append(f"{where}: row {n} keys {extra} are not headers and are dropped")
            row = [row.get(h, "") for h in headers]
        elif not isinstance(row, list):
            row = [row]
        if len(row) > len(headers):
            warnings.append(f"{where}: row {n} has {len(row)} cells for {len(headers)} headers; extra cells are dropped")
        cells = [("" if c is None else _text(c, where, "cell", errors)) for c in row[: len(headers)]]
        fixed.append(cells + [""] * (len(headers) - len(cells)))
    spec["rows"] = fixed
    if len(fixed) > MAX_TABLE_ROWS:
        warnings.append(f"{where}: {len(fixed)} table rows; about {MAX_TABLE_ROWS} fit. Split the table, rows past the slide are cut off")
    if len(headers) > MAX_TABLE_COLS:
        warnings.append(f"{where}: {len(headers)} columns; text gets very small past {MAX_TABLE_COLS}")


def _leaf_text(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [s for v in value.values() for s in _leaf_text(v)]
    if isinstance(value, list):
        return [s for v in value for s in _leaf_text(v)]
    return [value] if isinstance(value, str) else []


def prepare(outline: Any, target: str = "both", label: str = "outline") -> tuple[Any, list[str], list[str]]:
    """Normalize in place where safe. Return (outline, errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    slides_target = target in {"slides", "both"}
    if not isinstance(outline, dict) or not isinstance(outline.get("slides"), list) or not outline["slides"]:
        return outline, [f"{label}: outline needs a top-level 'slides' list (each item starts with '- layout:')"], warnings
    for key in list(outline):
        if key not in TOP_FIELDS:
            warnings.append(f"{label}: top-level '{key}' is not read by either builder")
        elif key != "slides":
            outline[key] = _text(outline[key], label, key, errors)
    covers = 0
    for i, spec in enumerate(outline["slides"], 1):
        where = f"{label} slide {i}"
        if not isinstance(spec, dict):
            errors.append(f"{where}: each slide must be a mapping like '- layout: content', not {type(spec).__name__}")
            continue
        layout = canonical_layout(spec)
        if layout.lower() not in KNOWN_LAYOUTS:
            errors.append(
                f"{where}: unknown layout {spec.get('layout') or spec.get('intent')!r}. Use one of: "
                + ", ".join(sorted(k for k in LAYOUT_ALIASES if "-" not in k or k in {"two-column", "photo-right"}))
            )
            continue
        drawn = LAYOUT_FIELDS[layout] | COMMON_FIELDS
        for key in list(spec):
            if key not in SLIDE_FIELDS:
                errors.append(f"{where}: field '{key}' is not read by either builder")
            elif key not in drawn:
                warnings.append(f"{where}: '{key}' is not shown on the {layout} layout and is dropped")
            elif key in TEXT_FIELDS:
                spec[key] = _text(spec[key], where, key, errors)
        if not any(spec.get(k) for k in drawn - {"layout", "intent", "footer", "notes"}) and layout != "Blank White Background":
            warnings.append(f"{where}: slide has no content")
        if layout == "Title Slide":
            covers += 1
            if i != 1:
                warnings.append(f"{where}: cover slide is not first")
        for keep, alt in (("bullets", "body"), ("items", "right")):
            if spec.get(keep) and spec.get(alt) and keep in drawn:
                warnings.append(f"{where}: has both {keep} and {alt}; only {keep} is shown and {alt} is dropped. "
                                f"Merge them into {keep}")
        bullets = spec.get("bullets") if spec.get("bullets") is not None else spec.get("body")
        if bullets is not None and "bullets" in drawn:
            key = "bullets" if spec.get("bullets") is not None else "body"
            if key == "body" and isinstance(bullets, str):
                spec[key] = _text(bullets, where, key, errors)
            else:
                spec[key] = bullets = _bullets(bullets, where, errors)
                if slides_target and any(isinstance(b, dict) and b.get("children") for b in bullets):
                    warnings.append(f"{where}: Google Slides shows nested bullets at the top level")
                if count_bullets(bullets) > MAX_BULLETS:
                    warnings.append(f"{where}: {count_bullets(bullets)} bullets, builders keep the first {MAX_BULLETS}")
                long = [b for b in _bullet_texts(bullets) if len(b) > BULLET_LIMIT]
                if long:
                    warnings.append(f"{where}: {len(long)} bullet(s) over {BULLET_LIMIT} characters; split them")
        items = spec.get("items") if spec.get("items") is not None else spec.get("right")
        if items is not None and "items" in drawn:
            if not isinstance(items, list):
                errors.append(f"{where}: items must be a list of {{title, body}} mappings")
            else:
                norm = []
                for it in items:
                    if isinstance(it, dict) and set(it) - {"title", "heading", "body", "text"}:
                        warnings.append(
                            f"{where}: item keys {sorted(set(it) - {'title', 'heading', 'body', 'text'})} are dropped. "
                            "Inside {...}, put text with commas in quotes"
                        )
                    if isinstance(it, dict):
                        norm.append({"title": _text(it.get("title") or it.get("heading") or "", where, "item title", errors),
                                     "body": _text(it.get("body") or it.get("text") or "", where, "item body", errors)})
                    else:
                        norm.append({"title": _text(it, where, "item title", errors), "body": ""})
                spec["items"] = norm
                spec.pop("right", None)
                if len(norm) > MAX_ITEMS:
                    warnings.append(f"{where}: {len(norm)} items, builders keep the first {MAX_ITEMS}")
                if any(len(it["body"] or "") > ITEM_BODY_LIMIT for it in norm):
                    warnings.append(f"{where}: an item body is over {ITEM_BODY_LIMIT} characters and will overflow")
        intent = str(spec.get("layout") or spec.get("intent") or "").strip().lower()
        if intent == "table" or spec.get("headers") is not None or (spec.get("rows") is not None and intent != "chart"):
            _table(spec, where, errors, warnings)
        if intent == "chart" or spec.get("chart") is not None:
            _chart(spec, where, slides_target, errors, warnings)
        limit = TITLE_LIMITS.get(layout)
        title = spec.get("title") or spec.get("statement")
        if limit and isinstance(title, str) and len(title) > limit:
            warnings.append(f"{where}: title is {len(title)} characters; over about {limit} it wraps into the content below")
        eyebrow = spec.get("eyebrow") or spec.get("kicker")
        if isinstance(eyebrow, str) and len(eyebrow) > EYEBROW_LIMIT:
            warnings.append(f"{where}: eyebrow is {len(eyebrow)} characters; over {EYEBROW_LIMIT} it runs into the title")
        if layout == "3-Photos":
            warnings.append(f"{where}: 3-photos fills only the first photo slot from 'image'")
        image = spec.get("image")
        if image:
            if layout.lower() in PICTURE_LAYOUTS:
                errors.extend(_image_errors(image, where))
            if slides_target:
                warnings.append(f"{where}: Google Slides ignores 'image'; insert it by hand (Insert > Image)")
        if slides_target and spec.get("notes"):
            warnings.append(f"{where}: speaker notes are written to PowerPoint only")
        if slides_target and layout.startswith("Intro_") and any(spec.get(k) for k in ("name", "role", "company")):
            warnings.append(f"{where}: Google Slides fills only 'title' on intro layouts")
        if any("TODO" in s for s in _leaf_text(spec)):
            warnings.append(f"{where}: still has TODO text, which prints on the slide as is")
    if covers > 1:
        warnings.append(f"{label}: {covers} cover slides; a deck usually has one")
    return outline, errors, warnings


def require(outline: Any, target: str, label: str) -> Any:
    """For builders: print warnings, stop on errors, return the normalized outline."""
    import sys

    outline, errors, warnings = prepare(outline, target, label)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        raise SystemExit(f"{label}: fix the {len(errors)} error(s) above, or run python3 scripts/check_outline.py on it")
    return outline
