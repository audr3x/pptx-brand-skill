#!/usr/bin/env python3
"""Build an on-brand Workday Google Slides deck from a JSON or YAML outline.

Usage:
    python3 scripts/build_slides.py examples/outline.yaml --dry-run -o examples/example-slides-requests.json
    python3 scripts/build_slides.py examples/outline.yaml --template-id "$WORKDAY_SLIDES_TEMPLATE_ID" --backend gws
    python3 scripts/build_slides.py examples/outline.yaml --import-pptx assets/template.pptx --backend api
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from brand import BRAND, Composition, NormalizedSlide, load_outline

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PPTX = ROOT / "assets" / "template.pptx"

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
    "Intro_Three": "TITLE_AND_BODY",
    "Intro_Four": "TITLE_AND_BODY",
    "Photo-Right": "TITLE_ONLY",
    "Layout 1": "BLANK",
    "3-Photos": "TITLE_ONLY",
}

MAX_BULLETS = BRAND.limits["bullets"]
CHART_SERIES = BRAND.chart_series
FONT_TITLE = BRAND.fonts["title"]
FONT_BODY = BRAND.fonts["body"]
EMU_PER_INCH = 914400


def hex_of(name_or_hex: str) -> str:
    return BRAND.color_hex(name_or_hex)


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
) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = [
        {"deleteText": {"objectId": object_id, "textRange": {"type": "ALL"}}},
        {"insertText": {"objectId": object_id, "text": text, "insertionIndex": 0}},
        {
            "updateTextStyle": {
                "objectId": object_id,
                "style": {
                    "fontFamily": font,
                    "fontSize": {"magnitude": size, "unit": "PT"},
                    "bold": bold,
                    "foregroundColor": opaque(color),
                },
                "textRange": {"type": "ALL"},
                "fields": "fontFamily,fontSize,bold,foregroundColor",
            }
        },
    ]
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
        ops.append(
            {
                "createParagraphBullets": {
                    "objectId": object_id,
                    "textRange": {"type": "ALL"},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
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
    ops.append({"insertText": {"objectId": object_id, "text": text, "insertionIndex": 0}})
    ops.append(
        {
            "updateTextStyle": {
                "objectId": object_id,
                "style": {
                    "fontFamily": font,
                    "fontSize": {"magnitude": size, "unit": "PT"},
                    "bold": bold,
                    "foregroundColor": opaque(color),
                },
                "textRange": {"type": "ALL"},
                "fields": "fontFamily,fontSize,bold,foregroundColor",
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


def placeholder_object_id(slide_id: str, idx: int) -> str:
    return f"{slide_id}_ph_{idx}"


def placeholder_mappings(slide_id: str, normalized: NormalizedSlide) -> list[dict[str, Any]]:
    layout = normalized.pattern.layout
    entries: dict[int, str] = {}
    for role, idx in layout.placeholders.items():
        if role == "title":
            kind = "CENTER_TITLE" if layout.name == "Title Slide" else "TITLE"
        else:
            kind = {
                "subtitle": "SUBTITLE",
                "body": "BODY",
                "footer": "FOOTER",
            }[role]
        entries[idx] = kind
    for slot in layout.speaker_slots:
        for role in ("name", "role", "company"):
            entries[slot[role]] = "BODY"
        entries[slot["picture"]] = "PICTURE"
    for idx in layout.picture_slots:
        entries[idx] = "PICTURE"
    return [
        {
            "layoutPlaceholder": {"type": kind, "index": idx},
            "objectId": placeholder_object_id(slide_id, idx),
        }
        for idx, kind in sorted(entries.items())
    ]


def image_url(image: Any) -> str:
    if isinstance(image, dict):
        image = image.get("url")
    if not isinstance(image, str) or not image.startswith(("https://", "http://")):
        raise ValueError("Google Slides images need a public http or https URL")
    return image


def create_image(
    object_id: str,
    page: str,
    image: Any,
    x: float,
    y: float,
    w: float,
    h: float,
) -> dict[str, Any]:
    return {
        "createImage": {
            "objectId": object_id,
            "url": image_url(image),
            "elementProperties": element_props(page, x, y, w, h),
        }
    }


def footer_ops(
    slide_id: str, text: str, normalized: NormalizedSlide
) -> list[dict[str, Any]]:
    layout = normalized.pattern.layout
    if not layout.footer:
        return []
    color = "ink" if layout.name in {"Section Title", "Layout 1"} else "staple"
    return text_ops(
        placeholder_object_id(slide_id, layout.placeholders["footer"]),
        text,
        font=FONT_TITLE,
        size=8,
        bold=False,
        color=color,
    )


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
                    "tableCellProperties": {"tableCellBackgroundFill": solid(fill)},
                    "fields": "tableCellBackgroundFill",
                }
            }
        )
        ops.append({"insertText": {"objectId": table_id, "cellLocation": loc, "text": text, "insertionIndex": 0}})
        ops.append(
            {
                "updateTextStyle": {
                    "objectId": table_id,
                    "cellLocation": loc,
                    "style": {
                        "fontFamily": font,
                        "fontSize": {"magnitude": size, "unit": "PT"},
                        "bold": bold,
                        "foregroundColor": opaque(color),
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "fontFamily,fontSize,bold,foregroundColor",
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


def chart_ops(slide_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    chart = spec.get("chart") or {}
    categories = [str(c) for c in chart.get("categories") or []]
    series_list = chart.get("series") or []
    if not categories or not series_list:
        raise SystemExit("chart slides need chart.categories and chart.series")
    ops: list[dict[str, Any]] = []
    # Simple clustered columns. Avoids a Sheets dependency.
    plot_x, plot_y, plot_w, plot_h = 0.50, 1.50, 7.40, 3.10
    max_val = max(float(v) for series in series_list for v in (series.get("values") or [1])) or 1
    n_cat = len(categories)
    n_ser = len(series_list)
    group_w = plot_w / n_cat
    bar_w = min(0.28, (group_w * 0.6) / max(n_ser, 1))
    for i, cat in enumerate(categories):
        gx = plot_x + i * group_w
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
            h = max(0.06, plot_h * (val / max_val))
            x = gx + 0.16 + s * (bar_w + 0.06)
            y = plot_y + plot_h - h
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


def item_copy(item: Any) -> tuple[str, str]:
    if isinstance(item, str):
        return item, ""
    return (
        item.get("title") or item.get("heading") or "",
        item.get("body") or item.get("text") or "",
    )


def two_column_ops(
    slide_id: str, items: list[Any], *, compact: bool
) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    stack = "two_column_compact" if compact else "two_column_numbered"
    for i, item in enumerate(items):
        heading, body = item_copy(item)
        if not compact:
            x, y, w, h = BRAND.stack_region(stack, "number", i)
            ops.extend(
                create_box(
                    f"{slide_id}_n{i}",
                    slide_id,
                    x,
                    y,
                    w,
                    h,
                    f"{i + 1:02d}",
                    font=FONT_TITLE,
                    size=20,
                    bold=True,
                    color="water_cooler",
                )
            )
        x, y, w, h = BRAND.stack_region(stack, "heading", i)
        ops.extend(
            create_box(
                f"{slide_id}_h{i}",
                slide_id,
                x,
                y,
                w,
                h,
                heading,
                font=FONT_TITLE,
                size=13 if compact else 15,
                bold=True,
                color="ink",
            )
        )
        if body:
            x, y, w, h = BRAND.stack_region(stack, "body", i)
            ops.extend(
                create_box(
                    f"{slide_id}_b{i}",
                    slide_id,
                    x,
                    y,
                    w,
                    h,
                    body,
                    font=FONT_BODY,
                    size=11 if compact else 13,
                    bold=False,
                    color="ink",
                )
            )
    return ops


def feature_grid_ops(slide_id: str, spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    subtitle = spec.get("subtitle")
    if subtitle:
        x, y, w, h = BRAND.region("title_alt_subhead")
        ops.extend(
            create_box(
                f"{slide_id}_subhead",
                slide_id,
                x,
                y,
                w,
                h,
                str(subtitle),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color="ink",
            )
        )
    for i, item in enumerate(spec.get("items") or []):
        heading, body = item_copy(item)
        x, y, w, h = BRAND.stack_region("feature_grid", "heading", i)
        ops.extend(
            create_box(
                f"{slide_id}_feature_h{i}",
                slide_id,
                x,
                y,
                w,
                h,
                heading,
                font=FONT_TITLE,
                size=15,
                bold=True,
                color="ink",
            )
        )
        if body:
            x, y, w, h = BRAND.stack_region("feature_grid", "body", i)
            ops.extend(
                create_box(
                    f"{slide_id}_feature_b{i}",
                    slide_id,
                    x,
                    y,
                    w,
                    h,
                    body,
                    font=FONT_BODY,
                    size=11,
                    bold=False,
                    color="ink",
                )
            )
    return ops


def photo_right_ops(slide_id: str, spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    x, y, w, h = BRAND.patterns["photo-right"].layout.picture_regions[0]
    ops.append(create_image(f"{slide_id}_image", slide_id, spec["image"], x, y, w, h))
    for i, item in enumerate(spec.get("items") or []):
        heading, body = item_copy(item)
        x, y, w, h = BRAND.stack_region("photo_right_items", "heading", i)
        ops.extend(
            create_box(
                f"{slide_id}_photo_h{i}",
                slide_id,
                x,
                y,
                w,
                h,
                heading,
                font=FONT_TITLE,
                size=13,
                bold=True,
                color="ink",
            )
        )
        if body:
            x, y, w, h = BRAND.stack_region("photo_right_items", "body", i)
            ops.extend(
                create_box(
                    f"{slide_id}_photo_b{i}",
                    slide_id,
                    x,
                    y,
                    w,
                    h,
                    body,
                    font=FONT_BODY,
                    size=11,
                    bold=False,
                    color="ink",
                )
            )
    return ops


def intro_ops(slide_id: str, normalized: NormalizedSlide) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    layout = normalized.pattern.layout
    for i, (slot, speaker) in enumerate(
        zip(layout.speaker_slots, normalized.get("speakers") or [])
    ):
        for field, size, bold, font in (
            ("name", 15, True, FONT_TITLE),
            ("role", 12, False, FONT_BODY),
            ("company", 10.5, False, FONT_BODY),
        ):
            ops.extend(
                text_ops(
                    placeholder_object_id(slide_id, slot[field]),
                    str(speaker.get(field) or ""),
                    font=font,
                    size=size,
                    bold=bold,
                    color="ink",
                )
            )
        if speaker.get("image"):
            x, y, w, h = layout.picture_regions[i]
            ops.append(
                create_image(
                    f"{slide_id}_speaker_image_{i}",
                    slide_id,
                    speaker["image"],
                    x,
                    y,
                    w,
                    h,
                )
            )
    return ops


def photos_ops(slide_id: str, normalized: NormalizedSlide) -> list[dict[str, Any]]:
    return [
        create_image(
            f"{slide_id}_image_{i}",
            slide_id,
            image,
            *normalized.pattern.layout.picture_regions[i],
        )
        for i, image in enumerate(normalized.get("images") or [])
    ]


def freeform_ops(slide_id: str, normalized: NormalizedSlide) -> list[dict[str, Any]]:
    spec = normalized.data
    layout_name = normalized.pattern.layout.name
    if layout_name == "Layout 1":
        title_region, body_region = "rail_title", "rail_body"
    elif layout_name == "Blank White Background":
        title_region, body_region = "blank_title", "blank_body"
    else:
        title_region, body_region = "standard_title", "standard_body"
    ops: list[dict[str, Any]] = []
    if "title" not in normalized.pattern.layout.placeholders and spec.get("title"):
        x, y, w, h = BRAND.region(title_region)
        ops.extend(
            create_box(
                f"{slide_id}_drawn_title",
                slide_id,
                x,
                y,
                w,
                h,
                str(spec["title"]),
                font=FONT_TITLE,
                size=28,
                bold=True,
                color="ink",
            )
        )
    if layout_name == "Title Only_Alt" and spec.get("subtitle"):
        x, y, w, h = BRAND.region("title_alt_subhead")
        ops.extend(
            create_box(
                f"{slide_id}_subhead",
                slide_id,
                x,
                y,
                w,
                h,
                str(spec["subtitle"]),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color="ink",
            )
        )
    body = spec.get("body") or spec.get("bullets")
    if body:
        if isinstance(body, list):
            body = "\n".join(
                item
                if isinstance(item, str)
                else str(item.get("text") or item.get("title") or "")
                for item in body
            )
        x, y, w, h = BRAND.region(body_region)
        ops.extend(
            create_box(
                f"{slide_id}_body_copy",
                slide_id,
                x,
                y,
                w,
                h,
                str(body),
                font=FONT_BODY,
                size=18,
                bold=False,
                color="ink",
            )
        )
    return ops


def agenda_ops(slide_id: str, spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    x, y, w, h = BRAND.region("section_eyebrow")
    ops = create_box(
        f"{slide_id}_agenda_title",
        slide_id,
        x,
        y,
        w,
        h,
        str(spec.get("title") or "").upper(),
        font=FONT_TITLE,
        size=14,
        bold=False,
        color="water_cooler",
    )
    for i, item in enumerate(spec.get("items") or []):
        heading, body = item_copy(item)
        number = str(item.get("number") if isinstance(item, dict) else i + 1)
        x, y, w, h = BRAND.stack_region("agenda_items", "number", i)
        ops.extend(
            create_box(
                f"{slide_id}_agenda_n{i}",
                slide_id,
                x,
                y,
                w,
                h,
                number.zfill(2),
                font=FONT_TITLE,
                size=13,
                bold=True,
                color="water_cooler",
            )
        )
        x, y, w, h = BRAND.stack_region("agenda_items", "heading", i)
        text = heading if not body else f"{heading}\n{body}"
        ops.extend(
            create_box(
                f"{slide_id}_agenda_h{i}",
                slide_id,
                x,
                y,
                w,
                h + (0.2 if body else 0),
                text,
                font=FONT_TITLE if not body else FONT_BODY,
                size=13 if not body else 11,
                bold=not body,
                color="ink",
            )
        )
    return ops


def timeline_ops(slide_id: str, items: list[Any]) -> list[dict[str, Any]]:
    ops = create_rect(f"{slide_id}_timeline", slide_id, 0.75, 2.73, 8.5, 0.03, "desk")
    step = 8.2 / max(len(items) - 1, 1)
    for i, item in enumerate(items):
        heading, body = item_copy(item)
        x = 0.55 + i * step
        above = i % 2 == 1
        ops.extend(
            create_box(
                f"{slide_id}_timeline_h{i}",
                slide_id,
                x,
                2.15 if above else 2.9,
                1.15,
                0.28,
                heading,
                font=FONT_TITLE,
                size=10,
                bold=True,
                color="water_cooler",
                align="CENTER",
            )
        )
        if body:
            ops.extend(
                create_box(
                    f"{slide_id}_timeline_b{i}",
                    slide_id,
                    x,
                    1.45 if above else 3.2,
                    1.15,
                    0.65,
                    body,
                    font=FONT_BODY,
                    size=9,
                    bold=False,
                    color="ink",
                    align="CENTER",
                )
            )
    return ops


def slide_plan(
    index: int, normalized: NormalizedSlide, footer: str
) -> dict[str, Any]:
    spec = normalized.data
    pattern = normalized.pattern
    layout = pattern.layout.name
    slide_id = f"wd_s{index + 1}"
    requests: list[dict[str, Any]] = []
    create: dict[str, Any] = {
        "objectId": slide_id,
        "insertionIndex": index,
        "placeholderIdMappings": placeholder_mappings(slide_id, normalized),
        "slideLayoutReference": {"layoutName": layout},
    }
    if layout.strip() in PREDEFINED_FALLBACK:
        create["predefinedLayoutFallback"] = PREDEFINED_FALLBACK[layout.strip()]
    requests.append({"createSlide": create})

    title = spec.get("title")
    title_idx = pattern.layout.placeholders.get("title")
    if title and title_idx is not None:
        requests.extend(
            text_ops(
                placeholder_object_id(slide_id, title_idx),
                str(title),
                font=FONT_TITLE,
                size=36 if pattern.composition == Composition.TITLE else 28,
                bold=pattern.composition != Composition.TITLE,
                color="ink",
            )
        )
    if pattern.composition == Composition.TITLE and spec.get("subtitle") is not None:
        subtitle_idx = pattern.layout.placeholders["subtitle"]
        requests.extend(
            text_ops(
                placeholder_object_id(slide_id, subtitle_idx),
                str(spec["subtitle"]),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color="ink",
            )
        )
    if pattern.composition == Composition.TITLE and spec.get("date"):
        x, y, w, h = BRAND.region("cover_date")
        requests.extend(
            create_box(
                f"{slide_id}_date",
                slide_id,
                x,
                y,
                w,
                h,
                str(spec["date"]),
                font=FONT_TITLE,
                size=12,
                bold=False,
                color="ink",
            )
        )
    if pattern.composition == Composition.SECTION:
        eyebrow = spec.get("eyebrow") or spec.get("kicker")
        if eyebrow:
            x, y, w, h = BRAND.region("section_eyebrow")
            requests.extend(
                create_box(
                    f"{slide_id}_eyebrow",
                    slide_id,
                    x,
                    y,
                    w,
                    h,
                    str(eyebrow).upper(),
                    font=FONT_TITLE,
                    size=14,
                    bold=False,
                    color="water_cooler",
                )
            )
        x, y, w, h = BRAND.region("section_title")
        requests.extend(
            create_box(
                f"{slide_id}_statement",
                slide_id,
                x,
                y,
                w,
                h,
                str(title or ""),
                font=FONT_TITLE,
                size=28,
                bold=True,
                color="ink",
            )
        )
    if pattern.composition == Composition.CLOSING and (
        title or spec.get("caption")
    ):
        x, y, w, h = BRAND.region("closing_caption")
        requests.extend(
            create_box(
                f"{slide_id}_caption",
                slide_id,
                x,
                y,
                w,
                h,
                str(title or spec.get("caption")),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color="paper",
                align="CENTER",
            )
        )
    if pattern.composition == Composition.INTRO:
        requests.extend(intro_ops(slide_id, normalized))
    elif pattern.composition == Composition.CONTENT:
        rows = flatten_bullets(spec.get("bullets") or [])
        body = "\n".join(("\t" * level) + text for text, level in rows)
        if body:
            requests.extend(
                text_ops(
                    placeholder_object_id(
                        slide_id, pattern.layout.placeholders["body"]
                    ),
                    body,
                    font=FONT_BODY,
                    size=20,
                    bold=False,
                    color="ink",
                    bullets=True,
                )
            )
    elif pattern.composition == Composition.FREEFORM:
        requests.extend(freeform_ops(slide_id, normalized))
    elif pattern.composition == Composition.FEATURE_GRID:
        requests.extend(feature_grid_ops(slide_id, spec))
    elif pattern.composition == Composition.TWO_COLUMN:
        items = list(spec.get("items") or [])
        requests.extend(two_column_ops(slide_id, items, compact=len(items) > 3))
    elif pattern.composition == Composition.AGENDA:
        requests.extend(agenda_ops(slide_id, spec))
    elif pattern.composition == Composition.PHOTOS:
        requests.extend(photos_ops(slide_id, normalized))
    elif pattern.composition == Composition.PHOTO_RIGHT:
        requests.extend(photo_right_ops(slide_id, spec))
    elif pattern.composition == Composition.TABLE:
        requests.extend(table_ops(slide_id, spec))
    elif pattern.composition == Composition.CHART:
        requests.extend(chart_ops(slide_id, spec))
    elif pattern.composition == Composition.TIMELINE:
        requests.extend(timeline_ops(slide_id, list(spec.get("items") or [])))
    requests.extend(footer_ops(slide_id, spec.get("footer") or footer, normalized))
    notes = spec.get("notes")
    return {
        "slideId": slide_id,
        "layout": layout,
        "intent": pattern.name,
        "spec": spec,
        "notes": notes,
        "requests": requests,
    }


def build_plan(outline: dict[str, Any]) -> dict[str, Any]:
    footer = outline.get("footer", "Workday Confidential")
    normalized = BRAND.normalize_outline(outline)
    slides = [slide_plan(i, spec, footer) for i, spec in enumerate(normalized)]
    requests: list[dict[str, Any]] = []
    for slide in slides:
        requests.extend(slide["requests"])
    return {
        "title": outline.get("title") or "Workday presentation",
        "footer": footer,
        "pageSize": {
            "width": emu(10.0),
            "height": emu(5.625),
            "note": "16:9 Workday canvas (10.00 x 5.625 in)",
        },
        "fonts": {
            "title": FONT_TITLE,
            "body": FONT_BODY,
            "fallback": BRAND.fonts["fallback"],
        },
        "slides": [
            {"slideId": s["slideId"], "layout": s["layout"], "intent": s["intent"]}
            for s in slides
        ],
        "requests": requests,
        "slidePlans": slides,
    }


def resolve_create_slide(request: dict[str, Any], layouts: dict[str, str], allow_predefined: bool) -> dict[str, Any]:
    create = request.get("createSlide")
    if not create:
        return request
    ref = create.get("slideLayoutReference") or {}
    name = (ref.get("layoutName") or "").strip()
    resolved = dict(create)
    fallback = resolved.pop("predefinedLayoutFallback", None)
    if name and name.lower() in layouts:
        resolved["slideLayoutReference"] = {"layoutId": layouts[name.lower()]}
    elif allow_predefined and fallback:
        print(
            f"warning: Workday layout {name!r} not on the template; using predefined {fallback}. Re-import the PPTX.",
            file=sys.stderr,
        )
        resolved["slideLayoutReference"] = {"predefinedLayout": fallback}
    elif name:
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


def bind_requests(requests: list[dict[str, Any]], layouts: dict[str, str], allow_predefined: bool) -> list[dict[str, Any]]:
    bound = []
    for req in requests:
        if "createSlide" in req:
            bound.append(resolve_create_slide(req, layouts, allow_predefined))
        else:
            bound.append(req)
    return bound


def placeholder_ids(slide: dict[str, Any]) -> dict[int, str]:
    found: dict[int, str] = {}
    for el in slide.get("pageElements") or []:
        ph = ((el.get("shape") or {}).get("placeholder") or {})
        if ph.get("index") is not None and el.get("objectId"):
            found[int(ph["index"])] = el["objectId"]
    return found


def rewrite_slide_requests(
    planned: dict[str, Any], live: dict[str, Any]
) -> list[dict[str, Any]]:
    slide_id = planned["slideId"]
    live_placeholders = placeholder_ids(live)
    rewritten: list[dict[str, Any]] = []
    for request in planned["requests"]:
        if "createSlide" in request:
            continue
        blob = json.dumps(request)
        for idx, object_id in live_placeholders.items():
            blob = blob.replace(placeholder_object_id(slide_id, idx), object_id)
        if f"{slide_id}_ph_" in blob:
            raise ValueError(f"Slide {slide_id} is missing a required placeholder")
        rewritten.append(json.loads(blob))
    return rewritten


def apply(outline: dict[str, Any], plan: dict[str, Any], args: argparse.Namespace) -> str:
    backend = args.backend
    template_id = args.template_id or os.environ.get("WORKDAY_SLIDES_TEMPLATE_ID")
    if args.import_pptx:
        pptx = Path(args.import_pptx)
        if not pptx.is_file():
            raise SystemExit(f"PPTX not found: {pptx}")
        template_id = import_pptx(backend, pptx, "Workday Corporate Template")
        print(f"Imported {pptx} → template {template_id}")
        print("Store this as WORKDAY_SLIDES_TEMPLATE_ID and copy it for later decks.")
    if not template_id:
        raise SystemExit("Pass --template-id, --import-pptx, or set WORKDAY_SLIDES_TEMPLATE_ID.")
    deck_id = copy_template(backend, template_id, plan["title"])
    print(f"Copied template {template_id} → {deck_id}")
    presentation = get_presentation(backend, deck_id)
    layouts = index_layouts(presentation)
    leftover = [s["objectId"] for s in presentation.get("slides") or []]
    if leftover:
        batch_update(backend, deck_id, [{"deleteObject": {"objectId": sid}} for sid in leftover])
    creates = []
    for req in plan["requests"]:
        if "createSlide" not in req:
            continue
        bound = resolve_create_slide(req, layouts, args.allow_predefined)
        bound["createSlide"].pop("placeholderIdMappings", None)
        creates.append(bound)
    batch_update(backend, deck_id, creates)
    presentation = get_presentation(backend, deck_id)
    slides_by_id = {s["objectId"]: s for s in presentation.get("slides") or []}
    fills: list[dict[str, Any]] = []
    for planned in plan["slidePlans"]:
        slide_id = planned["slideId"]
        live = slides_by_id.get(slide_id)
        if live is None:
            print(f"warning: created slide {slide_id} not in GET response", file=sys.stderr)
            continue
        try:
            fills.extend(rewrite_slide_requests(planned, live))
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    batch_update(backend, deck_id, fills)
    url = f"https://docs.google.com/presentation/d/{deck_id}/edit"
    print(url)
    return deck_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Workday-branded Google Slides deck from an outline.")
    parser.add_argument("outline", type=Path, help="JSON or YAML outline (same shape as build_deck.py)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Write the request plan JSON here")
    parser.add_argument("--dry-run", action="store_true", help="Write the plan only. No Google calls.")
    parser.add_argument("--template-id", default=None, help="Existing Workday Slides template ID")
    parser.add_argument("--import-pptx", type=Path, default=None, help="Upload this PPTX and convert it to Slides")
    parser.add_argument("--backend", choices=("gws", "api"), default=None, help="Live apply via gws or the Slides API")
    parser.add_argument(
        "--allow-predefined",
        action="store_true",
        help="If a Workday layout is missing, fall back to a Google predefined layout (off-brand chrome).",
    )
    args = parser.parse_args(argv)
    try:
        outline = load_outline(args.outline)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    try:
        plan = build_plan(outline)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    dest = args.output
    if dest is None and args.dry_run:
        dest = args.outline.with_name("example-slides-requests.json")
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        public = {k: v for k, v in plan.items() if k != "slidePlans"}
        public["auth"] = "dry-run" if args.dry_run or not args.backend else args.backend
        dest.write_text(json.dumps(public, indent=2) + "\n")
        print(f"Wrote {dest} ({len(plan['slides'])} slides, {len(plan['requests'])} requests)")
    if args.dry_run or args.backend is None:
        if not args.dry_run and args.backend is None and (args.template_id or args.import_pptx):
            raise SystemExit("Live apply needs --backend gws or --backend api.")
        if args.dry_run or dest is not None:
            return 0
        raise SystemExit("Pass --dry-run, or --backend with --template-id / --import-pptx.")
    apply(outline, plan, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
