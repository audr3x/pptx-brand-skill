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
SECTION_RAIL_WIDTH_IN = 2.743
TITLE_PLACEHOLDER_TYPES = ("TITLE", "CENTERED_TITLE", "CENTER_TITLE")
COVER_PNG = ROOT / "assets" / "logos" / "cover-gradient.png"
SMILE_PNG = ROOT / "assets" / "logos" / "workday-smile.png"
SMILE_TITLE_BOX = (0.669, 0.515, 1.343, 0.635)
SMILE_BUMPER_BOX = (3.392, 1.793, 3.216, 1.521)


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


def google_placeholder_mappings(
    slide_id: str, normalized: NormalizedSlide
) -> list[dict[str, Any]]:
    pattern = normalized.pattern
    mappings: list[tuple[str, str]] = []
    if (
        "title" in pattern.layout.placeholders
        and pattern.composition != Composition.INTRO
    ):
        title_type = (
            "CENTERED_TITLE"
            if pattern.composition == Composition.TITLE
            else "TITLE"
        )
        mappings.append((title_type, "title"))
    if "subtitle" in pattern.layout.placeholders:
        mappings.append(("SUBTITLE", "sub"))
    if (
        "body" in pattern.layout.placeholders
        and pattern.composition == Composition.CONTENT
    ):
        mappings.append(("BODY", "body"))
    return [
        {
            "layoutPlaceholder": {"type": placeholder_type, "index": 0},
            "objectId": f"{slide_id}_{suffix}",
        }
        for placeholder_type, suffix in mappings
    ]


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
    ops.extend(
        [
            {"insertText": {"objectId": object_id, "text": text, "insertionIndex": 0}},
            {
                "updateTextStyle": {
                    "objectId": object_id,
                    "style": style,
                    "textRange": {"type": "ALL"},
                    "fields": fields,
                }
            },
        ]
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


def prefer_drive_image_url(drive_id: str | None, url: str | None) -> str | None:
    """Drive IDs win. GitHub raw URLs 404 on a private repo and are dropped."""
    if is_github_raw_url(url):
        url = None
    if drive_id:
        return drive_download_url(drive_id)
    return url


def drop_github_image_urls(requests: list[dict[str, Any]], chrome: dict[str, Any]) -> list[dict[str, Any]]:
    """When Drive IDs are set, never leave a GitHub raw URL in createImage."""
    cover_id = chrome.get("cover_id")
    smile_id = chrome.get("smile_id")
    cleaned: list[dict[str, Any]] = []
    drop_zorder_for: set[str] = set()
    for req in requests:
        img = req.get("createImage")
        if img and is_github_raw_url(img.get("url")):
            oid = img.get("objectId") or ""
            replacement = None
            if "smile" in oid and smile_id:
                replacement = drive_download_url(smile_id)
            elif cover_id:
                replacement = drive_download_url(cover_id)
            elif smile_id:
                replacement = drive_download_url(smile_id)
            if replacement:
                img = dict(img)
                img["url"] = replacement
                cleaned.append({"createImage": img})
            else:
                drop_zorder_for.add(oid)
            continue
        z = req.get("updatePageElementsZOrder")
        if z and drop_zorder_for.intersection(z.get("pageElementObjectIds") or []):
            continue
        cleaned.append(req)
    return cleaned


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
    left, top, width, height = layout.footer_region
    return create_box(
        f"{slide_id}_footer",
        slide_id,
        left,
        top,
        width,
        height,
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
            h = max(0.06, plot_h * (val / max_val))
            x = cluster_left + s * (bar_w + bar_gap)
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
    for i, (regions, speaker) in enumerate(
        zip(layout.speaker_regions, normalized.get("speakers") or [])
    ):
        for field, size, bold, font in (
            ("name", 15, True, FONT_TITLE),
            ("role", 12, False, FONT_BODY),
            ("company", 10.5, False, FONT_BODY),
        ):
            x, y, w, h = regions[field]
            ops.extend(
                create_box(
                    f"{slide_id}_speaker_{i}_{field}",
                    slide_id,
                    x,
                    y,
                    w,
                    h,
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
    index: int,
    normalized: NormalizedSlide,
    footer: str,
    chrome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = normalized.data
    pattern = normalized.pattern
    layout = pattern.layout.name
    slide_id = f"wd_s{index + 1}"
    requests: list[dict[str, Any]] = []
    create: dict[str, Any] = {
        "objectId": slide_id,
        "insertionIndex": index,
        "placeholderIdMappings": google_placeholder_mappings(slide_id, normalized),
        "slideLayoutReference": {"layoutName": layout},
    }
    if layout.strip() in PREDEFINED_FALLBACK:
        create["predefinedLayoutFallback"] = PREDEFINED_FALLBACK[layout.strip()]
    requests.append({"createSlide": create})

    chrome = chrome or {}
    cover_url = chrome.get("cover_url")
    smile_url = chrome.get("smile_url")
    if layout == "Title Slide":
        requests.extend(page_background_ops(slide_id, "ballpoint"))
        if cover_url:
            requests.extend(
                create_image_ops(
                    f"{slide_id}_cover",
                    slide_id,
                    cover_url,
                    0.0,
                    0.0,
                    10.0,
                    5.625,
                    send_back=True,
                )
            )
        if smile_url:
            requests.extend(
                create_image_ops(
                    f"{slide_id}_smile",
                    slide_id,
                    smile_url,
                    *SMILE_TITLE_BOX,
                )
            )
    elif layout == "Bumper Slide":
        requests.extend(page_background_ops(slide_id, "ink"))
        if smile_url:
            requests.extend(
                create_image_ops(
                    f"{slide_id}_smile",
                    slide_id,
                    smile_url,
                    *SMILE_BUMPER_BOX,
                )
            )

    title = spec.get("title")
    cover_color = (
        "ink"
        if layout == "Title Slide" and cover_url
        else ("paper" if layout == "Title Slide" else "ink")
    )
    mapped_title = "title" in pattern.layout.placeholders
    if title and mapped_title and pattern.composition not in {
        Composition.INTRO,
        Composition.SECTION,
        Composition.AGENDA,
        Composition.CLOSING,
    }:
        requests.extend(
            text_ops(
                f"{slide_id}_title",
                str(title),
                font=FONT_TITLE,
                size=36 if pattern.composition == Composition.TITLE else 28,
                bold=pattern.composition != Composition.TITLE,
                color=cover_color,
            )
        )
    if pattern.composition == Composition.TITLE and spec.get("subtitle") is not None:
        requests.extend(
            text_ops(
                f"{slide_id}_sub",
                str(spec["subtitle"]),
                font=FONT_TITLE,
                size=16,
                bold=False,
                color=cover_color,
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
                color=cover_color,
            )
        )
    if pattern.composition in {Composition.SECTION, Composition.AGENDA}:
        requests.extend(section_rail_ops(slide_id))
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
                    f"{slide_id}_body",
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
        "spec": dict(spec),
        "notes": notes,
        "requests": requests,
    }


def build_plan(outline: dict[str, Any], chrome: dict[str, Any] | None = None) -> dict[str, Any]:
    footer = outline.get("footer", "Workday Confidential")
    chrome = chrome or {}
    normalized = BRAND.normalize_outline(outline)
    slides = [
        slide_plan(i, spec, footer, chrome) for i, spec in enumerate(normalized)
    ]
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
                "Title Slide uses createImage of cover-gradient.png when a Drive ID/URL is set; "
                "otherwise pageBackgroundFill is Ballpoint and cover type is Paper."
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
            "fallback": BRAND.fonts["fallback"],
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
    cover_id = getattr(args, "cover_image_id", None) or os.environ.get("WORKDAY_COVER_IMAGE_ID")
    smile_id = getattr(args, "smile_image_id", None) or os.environ.get("WORKDAY_SMILE_IMAGE_ID")
    cover_url = getattr(args, "cover_image_url", None) or os.environ.get("WORKDAY_COVER_IMAGE_URL")
    smile_url = getattr(args, "smile_image_url", None) or os.environ.get("WORKDAY_SMILE_IMAGE_URL")
    ids_path = getattr(args, "assets_ids", None)
    if ids_path:
        data = json.loads(Path(ids_path).read_text())
        cover_id = cover_id or data.get("WORKDAY_COVER_IMAGE_ID") or data.get("coverImageId")
        smile_id = smile_id or data.get("WORKDAY_SMILE_IMAGE_ID") or data.get("smileImageId")
        cover_url = cover_url or data.get("coverImageUrl")
        smile_url = smile_url or data.get("smileImageUrl")
    if is_github_raw_url(cover_url) or is_github_raw_url(smile_url):
        print(
            "warning: GitHub raw URLs 404 on a private repo. "
            "Upload the PNGs to Drive and share Anyone with the link: Viewer. "
            "--cover-image-url is not a substitute.",
            file=sys.stderr,
        )
    cover_url = prefer_drive_image_url(cover_id, cover_url)
    smile_url = prefer_drive_image_url(smile_id, smile_url)
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
        except SystemExit:
            raise
        except Exception as exc:
            print(
                f"warning: could not share the PNGs as anyone-with-link ({exc}). "
                "Open each file in the Drive UI and share Anyone with the link: Viewer. "
                "The Cursor Drive connector cannot create that share. "
                "Do not use a GitHub raw URL (private repos 404).",
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
        help="Public URL for the cover PNG. Ignored when --cover-image-id is set. GitHub raw URLs 404 on a private repo.",
    )
    parser.add_argument(
        "--smile-image-url",
        default=None,
        help="Public URL for the smile PNG. Ignored when --smile-image-id is set. GitHub raw URLs 404 on a private repo.",
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
    try:
        outline = load_outline(args.outline)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    chrome = resolve_chrome(args)
    try:
        plan = build_plan(outline, chrome)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
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
        fill_requests = drop_github_image_urls(fill_requests, chrome)
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
