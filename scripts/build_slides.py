#!/usr/bin/env python3
"""Build an on-brand Workday Google Slides deck from a JSON or YAML outline.

Usage:
    python3 scripts/build_slides.py examples/outline.yaml --dry-run -o examples/example-slides-requests.json
    python3 scripts/build_slides.py --upload-assets --backend gws
    python3 scripts/build_slides.py examples/outline.yaml --cover-image-id "$WORKDAY_COVER_IMAGE_ID" --backend gws
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outline_rules import LAYOUT_ALIASES, MAX_BULLETS, load, prepare, require  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PPTX = ROOT / "assets" / "template.pptx"
TOKENS_PATH = ROOT / "assets" / "brand-tokens.json"

CORE = {
    "after_hours": "022043",
    "ink": "0F2E66",
    "ballpoint": "0057AE",
    "water_cooler": "1C98E8",
    "blue_sky": "9ECFFF",
    "paper": "FFFFFF",
    "keyboard": "FCF8E8",
    "highlighter": "FFF3A8",
    "pencil": "FDE65E",
    "lunch_break": "FEC10B",
}
SECONDARY = {
    "tack": "6FC9D3",
    "eraser": "FFC2FD",
    "smoothie": "AB65D0",
    "happy_hour": "FD7E00",
    "thumbtack": "FC5B05",
    "laptop": "525D6A",
    "staple": "7D8B99",
    "desk": "B6C1CC",
    "business_card": "F1F3F6",
}
ALL_COLORS = {**CORE, **SECONDARY}
CHART_SERIES = [
    CORE["water_cooler"],
    CORE["lunch_break"],
    CORE["ballpoint"],
    CORE["blue_sky"],
    CORE["ink"],
]


PREDEFINED_FALLBACK = {
    "Title Slide": "TITLE",
    "Title and Content": "TITLE_AND_BODY",
    "Title Only": "TITLE_ONLY",
    "Title Only_Alt": "TITLE_ONLY",
    "1/2_Headline": "TITLE_AND_TWO_COLUMNS",
    "1/2 Headline_Alt": "TITLE_AND_TWO_COLUMNS",
    "Section Title": "SECTION_HEADER",
    "Bumper Slide": "BLANK",
    "Blank White Background": "BLANK",
    "Intro_One": "TITLE_AND_BODY",
    "Photo-Right": "TITLE_ONLY",
    "Layout 1": "BLANK",
    "3-Photos": "TITLE_ONLY",
}

# Only map placeholders that exist on that Workday layout. Extra types fail createSlide.
LAYOUT_PLACEHOLDERS = {
    "Title Slide": (("CENTERED_TITLE", "title"), ("SUBTITLE", "sub")),
    "Title and Content": (("TITLE", "title"), ("BODY", "body")),
    "Title Only": (("TITLE", "title"),),
    "Title Only_Alt": (("TITLE", "title"),),
    "1/2_Headline": (("TITLE", "title"),),
    "1/2 Headline_Alt": (("TITLE", "title"),),
    "Photo-Right": (("TITLE", "title"),),
    "3-Photos": (("TITLE", "title"),),
    "Intro_One": (("TITLE", "title"),),
}

NO_FOOTER = {"Title Slide", "Bumper Slide"}
FONT_TITLE = "Archivo"
FONT_BODY = "Archivo Light"  # logical role; the API gets Archivo + weight 300
EMU_PER_INCH = 914400
FOOTER_LEFT_IN = 0.50
SECTION_RAIL_WIDTH_IN = 2.743
SECTION_FOOTER_LEFT_IN = 3.32
BULLET_SPACE_PT = 6
TITLE_PLACEHOLDER_TYPES = ("TITLE", "CENTERED_TITLE", "CENTER_TITLE")
COVER_PNG = ROOT / "assets" / "logos" / "cover-gradient.png"
SMILE_PNG = ROOT / "assets" / "logos" / "workday-smile.png"
SMILE_TITLE_BOX = (0.669, 0.515, 1.343, 0.635)
SMILE_BUMPER_BOX = (3.392, 1.793, 3.216, 1.521)


def hex_of(name_or_hex: str) -> str:
    token = name_or_hex.strip().lstrip("#").lower().replace(" ", "_")
    if token in ALL_COLORS:
        return ALL_COLORS[token]
    h = token.upper()
    if h not in {v.upper() for v in ALL_COLORS.values()}:
        raise ValueError(
            f"Off-brand color {name_or_hex!r}. Use a named token from BRAND.md "
            f"or one of: {', '.join(sorted(ALL_COLORS))}."
        )
    return h


def rgb_frac(name_or_hex: str) -> dict[str, float]:
    h = hex_of(name_or_hex)
    return {
        "red": int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue": int(h[4:6], 16) / 255,
    }


def opaque(name_or_hex: str) -> dict[str, Any]:
    return {"opaqueColor": {"rgbColor": rgb_frac(name_or_hex)}}


def solid(name_or_hex: str) -> dict[str, Any]:
    return {"solidFill": {"color": {"rgbColor": rgb_frac(name_or_hex)}}}


def emu(inches: float) -> dict[str, Any]:
    return {"magnitude": round(inches * EMU_PER_INCH, 2), "unit": "EMU"}


def transform(x: float, y: float) -> dict[str, Any]:
    return {
        "scaleX": 1,
        "scaleY": 1,
        "shearX": 0,
        "shearY": 0,
        "translateX": round(x * EMU_PER_INCH, 2),
        "translateY": round(y * EMU_PER_INCH, 2),
        "unit": "EMU",
    }


def element_props(page: str, x: float, y: float, w: float, h: float) -> dict[str, Any]:
    return {
        "pageObjectId": page,
        "size": {"width": emu(w), "height": emu(h)},
        "transform": transform(x, y),
    }


def layout_name(intent: str) -> str:
    return LAYOUT_ALIASES.get(intent.strip().lower(), intent).strip()


def load_outline(path: Path) -> dict[str, Any]:
    return require(load(path), "slides", str(path))

def font_style(font: str, size: float, bold: bool, color: str) -> tuple[dict[str, Any], str]:
    """Archivo Light is not a Google family. Send Archivo + weight 300 instead."""
    if bold:
        weight = 700
    elif font in {FONT_BODY, "Archivo Light"}:
        weight = 300
    else:
        weight = 400
    style = {
        "fontFamily": FONT_TITLE,
        "weightedFontFamily": {"fontFamily": FONT_TITLE, "weight": weight},
        "fontSize": {"magnitude": size, "unit": "PT"},
        "bold": bold,
        "foregroundColor": opaque(color),
    }
    return style, "fontFamily,weightedFontFamily,fontSize,bold,foregroundColor"


def shape_has_text(element: dict[str, Any]) -> bool:
    text = ((element.get("shape") or {}).get("text") or {})
    for te in text.get("textElements") or []:
        content = ((te.get("textRun") or {}).get("content") or "")
        if content.strip():
            return True
    return False


def flatten_bullets(items: list[Any]) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []

    def walk(entries, level):
        for entry in entries:
            if isinstance(entry, str):
                rows.append((entry, level))
            elif isinstance(entry, dict):
                text = entry.get("text") or entry.get("title") or ""
                rows.append((text, level))
                kids = entry.get("children") or entry.get("bullets") or []
                walk(kids, min(level + 1, 2))
            else:
                rows.append((str(entry), level))

    walk(items, 0)
    if len(rows) > MAX_BULLETS:
        print(
            f"warning: {len(rows)} bullets on one slide; brand limit is about {MAX_BULLETS}. Truncating.",
            file=sys.stderr,
        )
        rows = rows[:MAX_BULLETS]
    return rows


def text_ops(
    object_id: str,
    text: str,
    *,
    font: str,
    size: float,
    bold: bool,
    color: str,
    align: str | None = None,
    bullets: bool = False,
    has_text: bool = False,
) -> list[dict[str, Any]]:
    style, fields = font_style(font, size, bold, color)
    ops: list[dict[str, Any]] = []
    if has_text:
        ops.append({"deleteText": {"objectId": object_id, "textRange": {"type": "ALL"}}})
    style_op = {
        "updateTextStyle": {
            "objectId": object_id,
            "style": style,
            "textRange": {"type": "ALL"},
            "fields": fields,
        }
    }
    ops.extend([{"insertText": {"objectId": object_id, "text": text, "insertionIndex": 0}}, style_op])
    if align:
        ops.append(
            {
                "updateParagraphStyle": {
                    "objectId": object_id,
                    "style": {"alignment": align},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            }
        )
    if bullets:
        # Lists default to COLLAPSE_LISTS, which ignores spaceAbove/spaceBelow between items.
        # The API has no request for the bullet glyph size; it follows the text size.
        ops.append(
            {
                "createParagraphBullets": {
                    "objectId": object_id,
                    "textRange": {"type": "ALL"},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            }
        )
        ops.append(
            {
                "updateParagraphStyle": {
                    "objectId": object_id,
                    "style": {
                        "spaceAbove": {"magnitude": BULLET_SPACE_PT, "unit": "PT"},
                        "spaceBelow": {"magnitude": BULLET_SPACE_PT, "unit": "PT"},
                        "spacingMode": "NEVER_COLLAPSE",
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "spaceAbove,spaceBelow,spacingMode",
                }
            }
        )
    return ops


def create_box(
    object_id: str,
    page: str,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    font: str,
    size: float,
    bold: bool,
    color: str,
    align: str | None = None,
    fill: str | None = None,
) -> list[dict[str, Any]]:
    shape: dict[str, Any] = {
        "objectId": object_id,
        "shapeType": "TEXT_BOX",
        "elementProperties": element_props(page, x, y, w, h),
    }
    ops: list[dict[str, Any]] = [{"createShape": shape}]
    if fill:
        ops.append(
            {
                "updateShapeProperties": {
                    "objectId": object_id,
                    "shapeProperties": {
                        "shapeBackgroundFill": solid(fill),
                        "outline": {"propertyState": "NOT_RENDERED"},
                    },
                    "fields": "shapeBackgroundFill,outline",
                }
            }
        )
    else:
        ops.append(
            {
                "updateShapeProperties": {
                    "objectId": object_id,
                    "shapeProperties": {"outline": {"propertyState": "NOT_RENDERED"}},
                    "fields": "outline",
                }
            }
        )
    # New shapes are empty; insert only (deleteText on empty fails).
    style, fields = font_style(font, size, bold, color)
    ops.append({"insertText": {"objectId": object_id, "text": text, "insertionIndex": 0}})
    ops.append(
        {
            "updateTextStyle": {
                "objectId": object_id,
                "style": style,
                "textRange": {"type": "ALL"},
                "fields": fields,
            }
        }
    )
    if align:
        ops.append(
            {
                "updateParagraphStyle": {
                    "objectId": object_id,
                    "style": {"alignment": align},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            }
        )
    return ops


def page_background_ops(slide_id: str, color: str) -> list[dict[str, Any]]:
    """Solid fill under a dropped layout picture. Ballpoint on the cover, Ink on the bumper."""
    return [
        {
            "updatePageProperties": {
                "objectId": slide_id,
                "pageProperties": {"pageBackgroundFill": solid(color)},
                "fields": "pageBackgroundFill",
            }
        }
    ]


def drive_download_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def is_github_raw_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    return "raw.githubusercontent.com" in lower or ("github.com/" in lower and "/raw/" in lower)


def is_placeholder_value(value: str | None) -> bool:
    """Doc placeholders such as YOUR_COVER_IMAGE_ID or <cover URL> must never reach createImage."""
    if not value:
        return False
    v = value.strip()
    if v.upper().startswith("YOUR_") or "<" in v or v in {"...", '"..."'}:
        print(f"warning: ignoring placeholder image value {v!r}. Pass a real Drive file ID or public URL.", file=sys.stderr)
        return True
    return False


def probe_url(url: str, timeout: float = 6.0) -> tuple[int | None, str]:
    """Fetch like Google Slides does: no cookies, no auth. Returns (status, content-type)."""
    import urllib.error
    import urllib.request

    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": "workday-slides-check"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            if exc.code == 405 and method == "HEAD":
                continue
            return exc.code, exc.headers.get("Content-Type", "") if exc.headers else ""
        except Exception:
            return None, ""
    return None, ""


def check_image_url(label: str, url: str | None, *, probe: bool, has_drive_id: bool = False) -> str | None:
    """Keep a public URL. Drop a GitHub raw URL that is not public, or any failing URL when a Drive ID can stand in."""
    if not url:
        return None
    if not probe:
        return url
    status, ctype = probe_url(url)
    if status is None:
        print(f"warning: could not reach {label} URL {url}. Make sure it is public before you send fills.", file=sys.stderr)
        return url
    if is_github_raw_url(url) and status in {401, 403, 404}:
        print(
            f"warning: dropped {label} URL {url} (HTTP {status}). GitHub raw URLs only work from a public repo. "
            "Host the PNG in a public repo or public static host, or use the no-image path.",
            file=sys.stderr,
        )
        return None
    if not 200 <= status < 300:
        problem = f"returned HTTP {status}. Google Slides will not be able to fetch it"
    elif ctype and not ctype.startswith("image/"):
        problem = f"returned {ctype}, not an image. A sign-in page means the file is not public"
    else:
        return url
    if has_drive_id:
        print(f"warning: {label} URL {url} {problem}. Using the Drive ID instead.", file=sys.stderr)
        return None
    print(f"warning: {label} URL {url} {problem}.", file=sys.stderr)
    return url


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def write_request_chunks(
    dest: Path,
    requests: list[dict[str, Any]],
    *,
    size: int,
    meta: dict[str, Any],
) -> list[Path]:
    """Write dest plus dest-01.json, dest-02.json, ... Send chunks in order."""
    write_json(dest, {**meta, "requests": requests})
    written = [dest]
    if size <= 0:
        return written
    chunks = [requests[i : i + size] for i in range(0, len(requests), size)] or [[]]
    count = len(chunks)
    names = [f"{dest.stem}-{i:02d}.json" for i in range(1, count + 1)]
    for stale in dest.parent.glob(f"{dest.stem}-[0-9][0-9].json"):
        if stale.name not in names:
            stale.unlink()
    for i, chunk in enumerate(chunks, 1):
        chunk_path = dest.with_name(names[i - 1])
        write_json(
            chunk_path,
            {
                **meta,
                "chunk": i,
                "chunkCount": count,
                "note": (
                    f"Chunk {i} of {count}. Send only the requests array to update_presentation. "
                    f"Send chunks in order: {', '.join(names)}."
                ),
                "requests": chunk,
            },
        )
        written.append(chunk_path)
    return written


def create_image_ops(
    object_id: str,
    page: str,
    url: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    send_back: bool = False,
) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = [
        {
            "createImage": {
                "objectId": object_id,
                "url": url,
                "elementProperties": element_props(page, x, y, w, h),
            }
        }
    ]
    if send_back:
        ops.append(
            {
                "updatePageElementsZOrder": {
                    "pageElementObjectIds": [object_id],
                    "operation": "SEND_TO_BACK",
                }
            }
        )
    return ops


def create_rect(object_id: str, page: str, x: float, y: float, w: float, h: float, fill: str) -> list[dict[str, Any]]:
    return [
        {
            "createShape": {
                "objectId": object_id,
                "shapeType": "RECTANGLE",
                "elementProperties": element_props(page, x, y, w, h),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": object_id,
                "shapeProperties": {
                    "shapeBackgroundFill": solid(fill),
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        },
    ]


def footer_ops(slide_id: str, idx: int, text: str, layout: str) -> list[dict[str, Any]]:
    """Always draw a new box. Google does not copy PPTX footer placeholders onto new slides."""
    if layout in NO_FOOTER or not text:
        return []
    color = "ink" if layout in {"Section Title", "Layout 1"} else "staple"
    return create_box(
        f"{slide_id}_footer",
        slide_id,
        SECTION_FOOTER_LEFT_IN if layout == "Section Title" else FOOTER_LEFT_IN,
        5.27,
        3.375,
        0.30,
        text,
        font=FONT_TITLE,
        size=8,
        bold=False,
        color=color,
    )


def section_rail_ops(slide_id: str) -> list[dict[str, Any]]:
    """PPTX Section Title carries a 2.743 in warm gradient rail. Slides often drops it."""
    # Approximate Day_Crop_1 with named tokens only: Tack → Keyboard → Lunch Break.
    bands = (
        ("tack", 0.00, 1.875),
        ("keyboard", 1.875, 1.875),
        ("lunch_break", 3.75, 1.875),
    )
    ops: list[dict[str, Any]] = []
    rail_ids = []
    for i, (fill, top, height) in enumerate(bands):
        oid = f"{slide_id}_rail_{i}"
        rail_ids.append(oid)
        ops.extend(create_rect(oid, slide_id, 0.0, top, SECTION_RAIL_WIDTH_IN, height, fill))
    ops.append(
        {
            "updatePageElementsZOrder": {
                "pageElementObjectIds": rail_ids,
                "operation": "SEND_TO_BACK",
            }
        }
    )
    return ops


def table_ops(slide_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    headers = [str(h) for h in spec.get("headers") or []]
    rows = spec.get("rows") or []
    if not headers:
        raise SystemExit("table slides need a 'headers' list")
    normalized = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append([str(row.get(h, "")) for h in headers])
        else:
            values = [str(v) for v in list(row)]
            values += [""] * (len(headers) - len(values))
            normalized.append(values[: len(headers)])
    n_rows = 1 + len(normalized)
    n_cols = len(headers)
    table_id = f"{slide_id}_table"
    height = max(1.70, min(3.40, 0.48 * n_rows))
    ops: list[dict[str, Any]] = [
        {
            "createTable": {
                "objectId": table_id,
                "rows": n_rows,
                "columns": n_cols,
                "elementProperties": element_props(slide_id, 0.50, 1.34, 9.00, height),
            }
        }
    ]

    def cell(r: int, c: int, text: str, fill: str, font: str, size: float, bold: bool, color: str):
        loc = {"rowIndex": r, "columnIndex": c}
        rng = {"location": loc, "rowSpan": 1, "columnSpan": 1}
        ops.append(
            {
                "updateTableCellProperties": {
                    "objectId": table_id,
                    "tableRange": rng,
                    "tableCellProperties": {
                        "tableCellBackgroundFill": solid(fill),
                        "contentAlignment": "MIDDLE",
                    },
                    "fields": "tableCellBackgroundFill,contentAlignment",
                }
            }
        )
        style, fields = font_style(font, size, bold, color)
        ops.append({"insertText": {"objectId": table_id, "cellLocation": loc, "text": text, "insertionIndex": 0}})
        ops.append(
            {
                "updateTextStyle": {
                    "objectId": table_id,
                    "cellLocation": loc,
                    "style": style,
                    "textRange": {"type": "ALL"},
                    "fields": fields,
                }
            }
        )

    row_h = {"magnitude": (height / n_rows) * 72, "unit": "PT"}
    ops.append(
        {
            "updateTableRowProperties": {
                "objectId": table_id,
                "rowIndices": list(range(n_rows)),
                "tableRowProperties": {"minRowHeight": row_h},
                "fields": "minRowHeight",
            }
        }
    )
    for c, header in enumerate(headers):
        cell(0, c, header, "water_cooler", FONT_TITLE, 12, True, "paper")
    for r, row in enumerate(normalized, start=1):
        fill = "keyboard" if r % 2 else "business_card"
        for c, value in enumerate(row):
            cell(r, c, value, fill, FONT_BODY, 11, False, "ink")
    ops.append(
        {
            "updateTableBorderProperties": {
                "objectId": table_id,
                "borderPosition": "ALL",
                "tableBorderProperties": {
                    "tableBorderFill": solid("desk"),
                    "weight": {"magnitude": 0.75, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "fields": "tableBorderFill,weight,dashStyle",
            }
        }
    )
    return ops


def axis_scale(lo: float, hi: float, max_ticks: int = 5) -> tuple[float, int, int]:
    """Round step (1, 2, 2.5, 5 x 10^k) and tick indices k_min..k_max so the axis spans lo..hi and zero."""
    lo, hi = min(0.0, lo), max(0.0, hi)
    span = (hi - lo) or 1.0
    raw = span / max_ticks
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    k_min = math.floor(lo / step + 1e-9)
    k_max = math.ceil(hi / step - 1e-9)
    if k_max == k_min:
        k_max += 1
    return step, k_min, k_max


def chart_ops(slide_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    chart = spec.get("chart") or {}
    categories = [str(c) for c in chart.get("categories") or []]
    series_list = chart.get("series") or []
    if not categories or not series_list:
        raise SystemExit("chart slides need chart.categories and chart.series")
    ops: list[dict[str, Any]] = []
    # Simple clustered columns drawn as shapes. Avoids a Sheets dependency.
    plot_x, plot_y, plot_w, plot_h = 0.95, 1.50, 6.95, 3.10
    values_all = [float(v) for series in series_list for v in (series.get("values") or [0])]
    step, k_min, k_max = axis_scale(min(values_all), max(values_all))
    unit_h = plot_h / (k_max - k_min)
    zero_y = plot_y + unit_h * k_max
    hairline = 0.75 / 72
    for t in range(k_min, k_max + 1):
        value = step * t
        y = plot_y + unit_h * (k_max - t)
        ops.extend(create_rect(f"{slide_id}_grid_{t - k_min}", slide_id, plot_x, y - hairline / 2, plot_w, hairline, "desk"))
        ops.extend(
            create_box(
                f"{slide_id}_tick_{t - k_min}",
                slide_id,
                0.30,
                y - 0.14,
                0.58,
                0.28,
                f"{value:g}",
                font=FONT_BODY,
                size=10,
                bold=False,
                color="ink",
                align="END",
            )
        )
    ops.extend(create_rect(f"{slide_id}_yaxis", slide_id, plot_x - hairline / 2, plot_y, hairline, plot_h, "desk"))
    n_cat = len(categories)
    n_ser = len(series_list)
    group_w = plot_w / n_cat
    bar_w = min(0.28, (group_w * 0.6) / max(n_ser, 1))
    bar_gap = 0.06
    cluster_w = n_ser * bar_w + max(n_ser - 1, 0) * bar_gap
    for i, cat in enumerate(categories):
        gx = plot_x + i * group_w
        cluster_left = gx + (group_w - cluster_w) / 2
        ops.extend(
            create_box(
                f"{slide_id}_cat_{i}",
                slide_id,
                gx,
                plot_y + plot_h + 0.04,
                group_w,
                0.28,
                cat,
                font=FONT_BODY,
                size=10,
                bold=False,
                color="ink",
                align="CENTER",
            )
        )
        for s, series in enumerate(series_list):
            values = series.get("values") or []
            val = float(values[i]) if i < len(values) else 0
            h = max(0.02, unit_h * abs(val) / step)
            x = cluster_left + s * (bar_w + bar_gap)
            y = zero_y - h if val >= 0 else zero_y
            ops.extend(create_rect(f"{slide_id}_bar_{i}_{s}", slide_id, x, y, bar_w, h, CHART_SERIES[s % len(CHART_SERIES)]))
    legend_x = 8.10
    for s, series in enumerate(series_list):
        y = 1.70 + s * 0.36
        ops.extend(create_rect(f"{slide_id}_legsw_{s}", slide_id, legend_x, y + 0.06, 0.18, 0.18, CHART_SERIES[s % len(CHART_SERIES)]))
        ops.extend(
            create_box(
                f"{slide_id}_leg_{s}",
                slide_id,
                legend_x + 0.26,
                y,
                1.40,
                0.30,
                str(series.get("name") or f"Series {s + 1}"),
                font=FONT_TITLE,
                size=10,
                bold=False,
                color="ink",
            )
        )
    return ops


def two_column_ops(slide_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    items = spec.get("items") or spec.get("right") or []
    if isinstance(items, dict):
        items = items.get("items") or []
    items = items[:3]
    ops: list[dict[str, Any]] = []
    top, gap = 0.76, 1.28
    for i, item in enumerate(items):
        if isinstance(item, str):
            heading, body = item, ""
        else:
            heading = item.get("title") or item.get("heading") or ""
            body = item.get("body") or item.get("text") or ""
        y = top + i * gap
        ops.extend(
            create_box(
                f"{slide_id}_n{i}",
                slide_id,
                5.00,
                y,
                0.53,
                0.44,
                f"{i + 1:02d}",
                font=FONT_TITLE,
                size=20,
                bold=True,
                color="water_cooler",
            )
        )
        ops.extend(
            create_box(
                f"{slide_id}_h{i}",
                slide_id,
                5.57,
                y,
                3.61,
                0.35,
                heading,
                font=FONT_TITLE,
                size=15,
                bold=True,
                color="ink",
            )
        )
        if body:
            ops.extend(
                create_box(
                    f"{slide_id}_b{i}",
                    slide_id,
                    5.57,
                    y + 0.32,
                    3.61,
                    0.76,
                    body,
                    font=FONT_BODY,
                    size=13,
                    bold=False,
                    color="ink",
                )
            )
    return ops


def slide_plan(index: int, spec: dict[str, Any], footer: str, chrome: dict[str, Any] | None = None) -> dict[str, Any]:
    intent = spec.get("layout") or spec.get("intent") or "content"
    layout = layout_name(intent)
    slide_id = f"wd_s{index + 1}"
    requests: list[dict[str, Any]] = []
    mappings = [
        {"layoutPlaceholder": {"type": ph_type, "index": 0}, "objectId": f"{slide_id}_{suffix}"}
        for ph_type, suffix in LAYOUT_PLACEHOLDERS.get(layout, ())
    ]
    create: dict[str, Any] = {
        "objectId": slide_id,
        "insertionIndex": index,
        "placeholderIdMappings": mappings,
        "slideLayoutReference": {"layoutName": layout},
    }
    if layout in PREDEFINED_FALLBACK:
        create["predefinedLayoutFallback"] = PREDEFINED_FALLBACK[layout]
    requests.append({"createSlide": create})
    chrome = chrome or {}
    cover_url = chrome.get("cover_url")
    smile_url = chrome.get("smile_url")
    # Layout pictures often do not copy. Solid fill is the fallback; createImage is the cover.
    if layout == "Title Slide":
        requests.extend(page_background_ops(slide_id, "ballpoint"))
        if cover_url:
            requests.extend(create_image_ops(f"{slide_id}_cover", slide_id, cover_url, 0.0, 0.0, 10.0, 5.625, send_back=True))
        if smile_url:
            requests.extend(create_image_ops(f"{slide_id}_smile", slide_id, smile_url, *SMILE_TITLE_BOX))
    elif layout == "Bumper Slide":
        requests.extend(page_background_ops(slide_id, "ink"))
        if smile_url:
            requests.extend(create_image_ops(f"{slide_id}_smile", slide_id, smile_url, *SMILE_BUMPER_BOX))

    title = spec.get("title")
    subtitle = spec.get("subtitle") or spec.get("subhead")
    # Reference cover: Ink on the cream/gold of Day Crop. Paper only on the flat Ballpoint fallback.
    cover_color = "ink" if layout == "Title Slide" and cover_url else ("paper" if layout == "Title Slide" else "ink")
    if title and layout not in {"Section Title", "Bumper Slide"}:
        requests.extend(
            text_ops(
                f"{slide_id}_title",
                str(title),
                font=FONT_TITLE,
                size=36 if layout == "Title Slide" else 28,
                bold=True,
                color=cover_color,
            )
        )
    if subtitle is not None and layout == "Title Slide":
        requests.extend(
            text_ops(
                f"{slide_id}_sub",
                str(subtitle),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color=cover_color,
            )
        )
    if layout == "Title Slide" and spec.get("date"):
        requests.extend(
            create_box(
                f"{slide_id}_date",
                slide_id,
                0.51,
                4.96,
                4.00,
                0.30,
                str(spec["date"]),
                font=FONT_TITLE,
                size=12,
                bold=False,
                color=cover_color,
            )
        )
    if layout == "Section Title":
        requests.extend(section_rail_ops(slide_id))
        eyebrow = spec.get("eyebrow") or spec.get("kicker")
        if eyebrow:
            requests.extend(
                create_box(
                    f"{slide_id}_eyebrow",
                    slide_id,
                    3.32,
                    1.08,
                    4.34,
                    0.41,
                    str(eyebrow).upper(),
                    font=FONT_TITLE,
                    size=14,
                    bold=False,
                    color="water_cooler",
                )
            )
        requests.extend(
            create_box(
                f"{slide_id}_statement",
                slide_id,
                3.32,
                1.46,
                5.61,
                2.20,
                str(title or spec.get("statement") or ""),
                font=FONT_TITLE,
                size=28,
                bold=True,
                color="ink",
            )
        )
    if layout == "Bumper Slide" and (title or spec.get("caption")):
        requests.extend(
            create_box(
                f"{slide_id}_caption",
                slide_id,
                1.50,
                3.58,
                7.00,
                0.40,
                str(title or spec.get("caption")),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color="paper",
                align="CENTER",
            )
        )
    if layout == "Title and Content":
        bullets = spec.get("bullets") or spec.get("body") or []
        if isinstance(bullets, str):
            bullets = [bullets]
        rows = flatten_bullets(bullets)
        body = "\n".join(text for text, _ in rows)
        if body:
            requests.extend(
                text_ops(
                    f"{slide_id}_body",
                    body,
                    font=FONT_BODY,
                    size=20,
                    bold=False,
                    color="ink",
                    bullets=True,
                )
            )
    if layout in {"1/2_Headline", "1/2 Headline_Alt"}:
        requests.extend(two_column_ops(slide_id, spec))
    if intent.strip().lower() == "table" or spec.get("headers"):
        requests.extend(table_ops(slide_id, spec))
    if intent.strip().lower() == "chart" or spec.get("chart"):
        requests.extend(chart_ops(slide_id, spec))
    requests.extend(footer_ops(slide_id, index, spec.get("footer", footer), layout))
    notes = spec.get("notes")
    return {
        "slideId": slide_id,
        "layout": layout,
        "intent": intent,
        "spec": spec,
        "notes": notes,
        "requests": requests,
    }


def build_plan(outline: dict[str, Any], chrome: dict[str, Any] | None = None) -> dict[str, Any]:
    outline, errors, _ = prepare(outline, "slides")
    if errors:
        raise SystemExit("Outline has errors:\n" + "\n".join(errors))
    footer = outline.get("footer", "Workday Confidential")
    chrome = chrome or {}
    slides = [slide_plan(i, spec, footer, chrome) for i, spec in enumerate(outline.get("slides") or [])]
    requests: list[dict[str, Any]] = []
    for slide in slides:
        requests.extend(slide["requests"])
    return {
        "title": outline.get("title") or "Workday presentation",
        "footer": footer,
        "chrome": {
            "coverImageId": chrome.get("cover_id"),
            "smileImageId": chrome.get("smile_id"),
            "coverImageUrl": chrome.get("cover_url"),
            "smileImageUrl": chrome.get("smile_url"),
            "coverText": "ink" if chrome.get("cover_url") else "paper",
            "note": (
                "Title Slide uses createImage of cover-gradient.png only when a real Drive ID or public URL "
                "is set; otherwise pageBackgroundFill is Ballpoint and cover type is Paper. The smile comes "
                "from the imported layouts unless --place-smile is set."
            ),
        },
        "pageSize": {
            "width": emu(10.0),
            "height": emu(5.625),
            "note": "16:9 Workday canvas (10.00 x 5.625 in)",
        },
        "fonts": {
            "title": FONT_TITLE,
            "body": FONT_TITLE,
            "bodyWeight": 300,
            "fallback": "Arial",
            "note": "Never send fontFamily Archivo Light. Use Archivo + weightedFontFamily.weight 300.",
        },
        "slides": [
            {"slideId": s["slideId"], "layout": s["layout"], "intent": s["intent"]}
            for s in slides
        ],
        "requests": requests,
        "slidePlans": slides,
    }


def resolve_create_slide(
    request: dict[str, Any],
    layouts: dict[str, str],
    allow_predefined: bool,
    *,
    require_id: bool = False,
) -> dict[str, Any]:
    create = request.get("createSlide")
    if not create:
        return request
    ref = create.get("slideLayoutReference") or {}
    name = (ref.get("layoutName") or "").strip()
    resolved = dict(create)
    fallback = resolved.pop("predefinedLayoutFallback", None)
    if not resolved.get("placeholderIdMappings"):
        resolved.pop("placeholderIdMappings", None)
    if name and name.lower() in layouts:
        resolved["slideLayoutReference"] = {"layoutId": layouts[name.lower()]}
    elif allow_predefined and fallback:
        print(
            f"warning: Workday layout {name!r} not on the template; using predefined {fallback}. Re-import the PPTX.",
            file=sys.stderr,
        )
        resolved["slideLayoutReference"] = {"predefinedLayout": fallback}
    elif require_id and name:
        raise SystemExit(
            f"Workday layout {name!r} is not on this presentation. Import assets/template.pptx or pass --template-id."
        )
    return {"createSlide": resolved}


def index_layouts(presentation: dict[str, Any]) -> dict[str, str]:
    found: dict[str, str] = {}
    for layout in presentation.get("layouts") or []:
        name = ((layout.get("layoutProperties") or {}).get("displayName") or layout.get("objectId") or "").strip()
        if name and layout.get("objectId"):
            found[name.lower()] = layout["objectId"]
    return found


# --- backends -----------------------------------------------------------------


def run_gws(args: list[str], *, params: dict | None = None, body: Any = None, upload: Path | None = None) -> Any:
    if not shutil.which("gws"):
        raise SystemExit("gws is not on PATH. Install https://github.com/googleworkspace/cli or use --backend api.")
    cmd = ["gws", *args]
    if params:
        cmd += ["--params", json.dumps(params)]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    if upload is not None:
        cmd += ["--upload", str(upload)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"gws failed ({result.returncode}): {result.stderr or result.stdout}")
    text = result.stdout.strip()
    return json.loads(text) if text else {}


def api_services():
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.auth import default
    except ImportError as exc:
        raise SystemExit(
            "google-api-python-client and google-auth are required for --backend api. pip3 install -r requirements.txt"
        ) from exc
    creds, _ = default(scopes=[
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/presentations",
    ])
    return (
        build("drive", "v3", credentials=creds, cache_discovery=False),
        build("slides", "v1", credentials=creds, cache_discovery=False),
        MediaFileUpload,
    )


def import_pptx(backend: str, path: Path, title: str) -> str:
    if backend == "gws":
        created = run_gws(
            ["drive", "files", "create"],
            body={"name": title, "mimeType": "application/vnd.google-apps.presentation"},
            upload=path,
        )
        file_id = created.get("id") or created.get("fileId")
        if not file_id:
            raise SystemExit(f"gws upload did not return an id: {created}")
        return file_id
    drive, _, MediaFileUpload = api_services()
    media = MediaFileUpload(str(path), mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation", resumable=True)
    created = (
        drive.files()
        .create(
            body={"name": title, "mimeType": "application/vnd.google-apps.presentation"},
            media_body=media,
            fields="id,webViewLink",
        )
        .execute()
    )
    return created["id"]


def copy_template(backend: str, template_id: str, title: str) -> str:
    if backend == "gws":
        copied = run_gws(["drive", "files", "copy"], params={"fileId": template_id}, body={"name": title})
        file_id = copied.get("id") or copied.get("fileId")
        if not file_id:
            raise SystemExit(f"gws copy did not return an id: {copied}")
        return file_id
    drive, _, _ = api_services()
    copied = drive.files().copy(fileId=template_id, body={"name": title}, fields="id,webViewLink").execute()
    return copied["id"]


def get_presentation(backend: str, presentation_id: str) -> dict[str, Any]:
    if backend == "gws":
        return run_gws(["slides", "presentations", "get"], params={"presentationId": presentation_id})
    _, slides, _ = api_services()
    return slides.presentations().get(presentationId=presentation_id).execute()


def batch_update(backend: str, presentation_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
    if not requests:
        return {}
    body = {"requests": requests}
    if backend == "gws":
        return run_gws(["slides", "presentations", "batchUpdate"], params={"presentationId": presentation_id}, body=body)
    _, slides, _ = api_services()
    return slides.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()


def placeholder_id(slide: dict[str, Any], *types: str) -> str | None:
    wanted = {t.upper() for t in types}
    aliases = set(wanted)
    if wanted & {"TITLE", "CENTERED_TITLE", "CENTER_TITLE"}:
        aliases.update(TITLE_PLACEHOLDER_TYPES)
    for el in slide.get("pageElements") or []:
        ph = ((el.get("shape") or {}).get("placeholder") or {})
        if str(ph.get("type") or "").upper() in aliases:
            return el.get("objectId")
    return None


def load_presentation_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    # Cursor Slides MCP sometimes wraps the presentation.
    if "presentation" in data and isinstance(data["presentation"], dict):
        return data["presentation"]
    return data


def create_phase_requests(
    plan: dict[str, Any],
    layouts: dict[str, str] | None,
    allow_predefined: bool,
) -> list[dict[str, Any]]:
    require_id = bool(layouts)
    creates = []
    for req in plan["requests"]:
        if "createSlide" not in req:
            continue
        creates.append(
            resolve_create_slide(
                req,
                layouts or {},
                allow_predefined,
                require_id=require_id,
            )
        )
    return creates


def remap_request(
    req: dict[str, Any],
    planned_id: str,
    live_id: str,
    ph_map: dict[str, str],
) -> dict[str, Any]:
    def walk(obj):
        if isinstance(obj, dict):
            out = {}
            for key, value in obj.items():
                if key in {"objectId", "pageObjectId"} and isinstance(value, str):
                    if value == planned_id:
                        out[key] = live_id
                    elif value in ph_map:
                        out[key] = ph_map[value]
                    else:
                        out[key] = value
                else:
                    out[key] = walk(value)
            return out
        if isinstance(obj, list):
            return [walk(item) for item in obj]
        return obj

    return walk(req)


def bind_fills(plan: dict[str, Any], presentation: dict[str, Any]) -> list[dict[str, Any]]:
    """Phase 2: bind planned fills to a presentations.get / read_presentation payload."""
    slides = presentation.get("slides") or []
    by_id = {s["objectId"]: s for s in slides}
    fills: list[dict[str, Any]] = []
    for index, planned in enumerate(plan["slidePlans"]):
        planned_id = planned["slideId"]
        live = by_id.get(planned_id)
        if live is None and index < len(slides):
            live = slides[index]
        if live is None:
            print(f"warning: created slide {planned_id} not in GET response", file=sys.stderr)
            continue
        live_id = live["objectId"]
        title_id = placeholder_id(live, *TITLE_PLACEHOLDER_TYPES)
        sub_id = placeholder_id(live, "SUBTITLE")
        body_id = placeholder_id(live, "BODY")
        ph_map = {}
        if title_id:
            ph_map[f"{planned_id}_title"] = title_id
            ph_map[f"{planned_id}_ctitle"] = title_id
        if sub_id:
            ph_map[f"{planned_id}_sub"] = sub_id
        if body_id:
            ph_map[f"{planned_id}_body"] = body_id
        has_text = {el.get("objectId"): shape_has_text(el) for el in live.get("pageElements") or []}
        for req in planned["requests"]:
            if "createSlide" in req:
                continue
            remapped = remap_request(req, planned_id, live_id, ph_map)
            if "deleteText" in remapped:
                oid = remapped["deleteText"].get("objectId")
                if not has_text.get(oid):
                    continue
            fills.append(remapped)
            if "insertText" in remapped:
                oid = remapped["insertText"].get("objectId")
                loc = remapped["insertText"].get("cellLocation")
                if loc is None and has_text.get(oid) and not any(
                    "deleteText" in prev and prev["deleteText"].get("objectId") == oid
                    for prev in fills[-4:]
                ):
                    fills.insert(-1, {"deleteText": {"objectId": oid, "textRange": {"type": "ALL"}}})
    return fills


def resolve_chrome(args: argparse.Namespace) -> dict[str, Any]:
    """An explicit public URL wins over a Drive ID. A private GitHub raw URL falls back to the ID."""
    cover_id = getattr(args, "cover_image_id", None) or os.environ.get("WORKDAY_COVER_IMAGE_ID")
    smile_id = getattr(args, "smile_image_id", None) or os.environ.get("WORKDAY_SMILE_IMAGE_ID")
    cover_url = getattr(args, "cover_image_url", None) or os.environ.get("WORKDAY_COVER_IMAGE_URL")
    smile_url = getattr(args, "smile_image_url", None) or os.environ.get("WORKDAY_SMILE_IMAGE_URL")
    ids_path = getattr(args, "assets_ids", None)
    if ids_path:
        data = json.loads(Path(ids_path).read_text())
        cover_id = cover_id or data.get("WORKDAY_COVER_IMAGE_ID") or data.get("coverImageId")
        smile_id = smile_id or data.get("WORKDAY_SMILE_IMAGE_ID") or data.get("smileImageId")
    cover_id, smile_id, cover_url, smile_url = (
        None if is_placeholder_value(v) else v for v in (cover_id, smile_id, cover_url, smile_url)
    )
    if not getattr(args, "place_smile", False):
        if smile_id or smile_url:
            print(
                "note: skipping the smile image. The imported Workday template already has the lockup on the "
                "Title and Bumper layouts. Add --place-smile only for a template that lacks it.",
                file=sys.stderr,
            )
        smile_id = smile_url = None
    probe = not getattr(args, "skip_url_check", False)
    cover_url = check_image_url("cover", cover_url, probe=probe, has_drive_id=bool(cover_id)) or (
        drive_download_url(cover_id) if cover_id else None
    )
    smile_url = check_image_url("smile", smile_url, probe=probe, has_drive_id=bool(smile_id)) or (
        drive_download_url(smile_id) if smile_id else None
    )
    return {
        "cover_id": cover_id,
        "smile_id": smile_id,
        "cover_url": cover_url,
        "smile_url": smile_url,
    }


def share_anyone(backend: str, file_id: str) -> None:
    body = {"type": "anyone", "role": "reader"}
    if backend == "gws":
        run_gws(["drive", "permissions", "create"], params={"fileId": file_id}, body=body)
        return
    drive, _, _ = api_services()
    drive.permissions().create(fileId=file_id, body=body).execute()


def upload_drive_png(backend: str, path: Path, name: str) -> str:
    if not path.is_file():
        raise SystemExit(f"Asset not found: {path}. Run python3 scripts/export_cover_assets.py")
    if backend == "gws":
        created = run_gws(
            ["drive", "files", "create"],
            body={"name": name, "mimeType": "image/png"},
            upload=path,
        )
        file_id = created.get("id") or created.get("fileId")
        if not file_id:
            raise SystemExit(f"gws upload did not return an id: {created}")
        return file_id
    drive, _, MediaFileUpload = api_services()
    media = MediaFileUpload(str(path), mimetype="image/png", resumable=True)
    created = drive.files().create(body={"name": name, "mimeType": "image/png"}, media_body=media, fields="id").execute()
    return created["id"]


def upload_assets(args: argparse.Namespace) -> dict[str, str]:
    backend = args.backend or "gws"
    cover_id = upload_drive_png(backend, COVER_PNG, "Workday cover gradient")
    smile_id = upload_drive_png(backend, SMILE_PNG, "Workday smile lockup")
    if not args.keep_private:
        try:
            share_anyone(backend, cover_id)
            share_anyone(backend, smile_id)
        except (SystemExit, Exception) as exc:
            # Org policy can forbid "Anyone with the link". Keep the IDs and explain the ways out.
            print(
                f"warning: could not share the PNGs as Anyone with the link ({exc}).\n"
                "  1. Share each file in the Drive UI as Anyone with the link: Viewer, if your org allows it.\n"
                "  2. If your org only allows sharing inside the org, host cover-gradient.png at a public URL and pass "
                "--cover-image-url.\n"
                "  3. Or run fills with no image options and insert the images by hand (see GETTING_STARTED.md).",
                file=sys.stderr,
            )
    payload = {
        "WORKDAY_COVER_IMAGE_ID": cover_id,
        "WORKDAY_SMILE_IMAGE_ID": smile_id,
        "coverImageId": cover_id,
        "smileImageId": smile_id,
        "coverImageUrl": drive_download_url(cover_id),
        "smileImageUrl": drive_download_url(smile_id),
        "note": (
            "createImage needs Anyone with the link: Viewer. Share both PNGs in the Drive UI. "
            "The Cursor Drive connector cannot create that share. These IDs are brand chrome, not deck copy."
        ),
    }
    dest = args.output or Path("workday-slide-assets.json")
    dest.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Uploaded cover {cover_id}")
    print(f"Uploaded smile {smile_id}")
    print(f"Wrote {dest}")
    print(f'export WORKDAY_COVER_IMAGE_ID="{cover_id}"')
    print(f'export WORKDAY_SMILE_IMAGE_ID="{smile_id}"')
    return payload


def apply(outline: dict[str, Any], plan: dict[str, Any], args: argparse.Namespace) -> str:
    backend = args.backend
    template_id = args.template_id or os.environ.get("WORKDAY_SLIDES_TEMPLATE_ID")
    if args.import_pptx:
        pptx = Path(args.import_pptx)
        if not pptx.is_file():
            raise SystemExit(f"PPTX not found: {pptx}")
        template_id = import_pptx(backend, pptx, "Workday Corporate Template")
        print(f"Imported {pptx} → {template_id}")
        print(
            "On a first run you can fill this imported file. "
            "Copying it is optional. Store the ID as WORKDAY_SLIDES_TEMPLATE_ID for later decks."
        )
    if not template_id:
        raise SystemExit("Pass --template-id, --import-pptx, or set WORKDAY_SLIDES_TEMPLATE_ID.")
    first_run_import = bool(args.import_pptx) and not args.template_id
    if first_run_import:
        deck_id = template_id
        print(f"Using the imported file as the deck {deck_id} (copy is optional on a first run).")
    else:
        deck_id = copy_template(backend, template_id, plan["title"])
        print(f"Copied template {template_id} → {deck_id}")
    presentation = get_presentation(backend, deck_id)
    layouts = index_layouts(presentation)
    leftover = [s["objectId"] for s in presentation.get("slides") or []]
    if leftover:
        batch_update(backend, deck_id, [{"deleteObject": {"objectId": sid}} for sid in leftover])
    else:
        print("No leftover slides on this file (a clean PPTX import has none). Skipping delete.")
    creates = create_phase_requests(plan, layouts, args.allow_predefined)
    batch_update(backend, deck_id, creates)
    presentation = get_presentation(backend, deck_id)
    fills = bind_fills(plan, presentation)
    batch_update(backend, deck_id, fills)
    url = f"https://docs.google.com/presentation/d/{deck_id}/edit"
    print(url)
    return deck_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Workday-branded Google Slides deck from an outline.")
    parser.add_argument("outline", type=Path, nargs="?", help="JSON or YAML outline (same shape as build_deck.py)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Write the request plan JSON here")
    parser.add_argument("--dry-run", action="store_true", help="Write the full plan, including slidePlans. No Google calls.")
    parser.add_argument(
        "--phase",
        choices=("creates", "fills"),
        default=None,
        help="Connector mode: write creates.json, or bind fills.json from a presentations.get JSON.",
    )
    parser.add_argument(
        "--presentation",
        type=Path,
        default=None,
        help="presentations.get / read_presentation JSON. Use it on --phase fills so IDs bind. Optional for --phase creates to resolve layoutIds.",
    )
    parser.add_argument(
        "--chunk",
        nargs="?",
        const=40,
        type=int,
        default=None,
        metavar="N",
        help=(
            "With --phase fills, also write dest-01.json, dest-02.json, ... with N requests each "
            "(default 40). Send only the requests array to update_presentation, in order."
        ),
    )
    parser.add_argument("--template-id", default=None, help="Existing Workday Slides template ID")
    parser.add_argument("--import-pptx", type=Path, default=None, help="Upload this PPTX and convert it to Slides")
    parser.add_argument("--backend", choices=("gws", "api"), default=None, help="Live apply via gws or the Slides API")
    parser.add_argument(
        "--allow-predefined",
        action="store_true",
        help="If a Workday layout is missing, fall back to a Google predefined layout (off-brand chrome).",
    )
    parser.add_argument(
        "--upload-assets",
        action="store_true",
        help="One-time: upload cover-gradient.png and workday-smile.png to Drive and write their IDs.",
    )
    parser.add_argument(
        "--keep-private",
        action="store_true",
        help="With --upload-assets, do not set anyone-with-link. createImage will fail unless you pass a public URL.",
    )
    parser.add_argument("--cover-image-id", default=None, help="Drive file ID for assets/logos/cover-gradient.png")
    parser.add_argument("--smile-image-id", default=None, help="Drive file ID for assets/logos/workday-smile.png")
    parser.add_argument(
        "--cover-image-url",
        default=None,
        help="Public URL for cover-gradient.png. Wins over --cover-image-id. A GitHub raw URL must be from a public repo.",
    )
    parser.add_argument(
        "--smile-image-url",
        default=None,
        help="Public URL for workday-smile.png. Wins over --smile-image-id. A GitHub raw URL must be from a public repo.",
    )
    parser.add_argument(
        "--place-smile",
        action="store_true",
        help="Also place the smile PNG. Off by default: the imported template layouts already carry the lockup.",
    )
    parser.add_argument(
        "--skip-url-check",
        action="store_true",
        help="Do not fetch the image URLs to confirm they are public (offline builds).",
    )
    parser.add_argument(
        "--assets-ids",
        type=Path,
        default=None,
        help="JSON from --upload-assets (WORKDAY_COVER_IMAGE_ID / WORKDAY_SMILE_IMAGE_ID).",
    )
    args = parser.parse_args(argv)
    if args.upload_assets:
        if not args.backend:
            raise SystemExit("--upload-assets needs --backend gws or --backend api.")
        upload_assets(args)
        return 0
    if args.outline is None:
        raise SystemExit("Pass an outline, or --upload-assets.")
    outline = load_outline(args.outline)
    chrome = resolve_chrome(args)
    plan = build_plan(outline, chrome)
    dest = args.output
    if dest is None and args.dry_run:
        dest = args.outline.with_name("example-slides-requests.json")
    if dest is None and args.phase == "creates":
        dest = Path("creates.json")
    if dest is None and args.phase == "fills":
        dest = Path("fills.json")

    if args.phase == "creates":
        layouts = index_layouts(load_presentation_json(args.presentation)) if args.presentation else None
        payload = {
            "phase": "creates",
            "title": plan["title"],
            "chrome": plan.get("chrome"),
            "note": (
                "Send these createSlide requests. If slideLayoutReference still has layoutName, "
                "replace it with layouts[].objectId from presentations.get (match displayName, strip space). "
                "Keep the planned objectId values (wd_s1, wd_s2, ...). Cover createImage requests are in --phase fills."
            ),
            "requests": create_phase_requests(plan, layouts, args.allow_predefined),
        }
        write_json(dest, payload)
        print(f"Wrote {dest} ({len(payload['requests'])} createSlide requests)")
        return 0

    if args.phase == "fills":
        if args.presentation:
            presentation = load_presentation_json(args.presentation)
            fill_requests = bind_fills(plan, presentation)
            fill_note = (
                "Send only the requests array to update_presentation after phase 1. "
                "IDs are bound to the GET payload. If you used --chunk, send fills-01, fills-02, ... in order."
            )
        else:
            fill_requests = [req for req in plan["requests"] if "createSlide" not in req]
            fill_note = (
                "Send only the requests array to update_presentation after the createSlide batch. "
                "Slide IDs are the planned wd_sN values. Re-run with --presentation get.json if IDs differ. "
                "If you used --chunk, send fills-01, fills-02, ... in order."
            )
        payload = {
            "phase": "fills",
            "title": plan["title"],
            "chrome": plan.get("chrome"),
            "note": fill_note,
        }
        chunk = args.chunk
        if chunk:
            paths = write_request_chunks(dest, fill_requests, size=chunk, meta=payload)
            print(
                f"Wrote {dest} ({len(fill_requests)} fill requests) and "
                f"{len(paths) - 1} chunks of {chunk}: "
                + ", ".join(p.name for p in paths[1:])
            )
        else:
            write_json(dest, {**payload, "requests": fill_requests})
            print(f"Wrote {dest} ({len(fill_requests)} fill requests)")
        return 0

    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        public = dict(plan)
        public["auth"] = "dry-run" if args.dry_run or not args.backend else args.backend
        dest.write_text(json.dumps(public, indent=2) + "\n")
        print(f"Wrote {dest} ({len(plan['slides'])} slides, {len(plan['requests'])} requests)")
    if args.dry_run or args.backend is None:
        if not args.dry_run and args.backend is None and (args.template_id or args.import_pptx):
            raise SystemExit("Live apply needs --backend gws or --backend api.")
        if args.dry_run or dest is not None:
            return 0
        raise SystemExit("Pass --dry-run, --phase creates|fills, or --backend with --template-id / --import-pptx.")
    apply(outline, plan, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
