#!/usr/bin/env python3
"""Build an on-brand Workday deck from a JSON or YAML outline.

Usage:
    python3 scripts/build_deck.py examples/outline.yaml -o examples/example-deck.pptx
    python3 scripts/build_deck.py outline.json --template assets/template.pptx
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.table import Table
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "assets" / "template.pptx"
TOKENS_PATH = ROOT / "assets" / "brand-tokens.json"

# Official Workday Corporate Template tokens. Never invent a hex.
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

MAX_BULLETS = 6
FONT_TITLE = "Archivo"
FONT_BODY = "Archivo Light"
FONT_FALLBACK = "Arial"


def rgb(name_or_hex: str) -> RGBColor:
    token = name_or_hex.strip().lstrip("#").lower().replace(" ", "_")
    if token in ALL_COLORS:
        h = ALL_COLORS[token]
    else:
        h = token.upper()
        allowed = {v.upper() for v in ALL_COLORS.values()}
        if h not in allowed:
            raise ValueError(
                f"Off-brand color {name_or_hex!r}. Use a named token from BRAND.md "
                f"or one of: {', '.join(sorted(ALL_COLORS))}."
            )
    return RGBColor.from_string(h)


def load_outline(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise SystemExit("PyYAML is required for .yaml outlines. pip3 install pyyaml") from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict) or "slides" not in data:
        raise SystemExit("Outline must be an object with a top-level 'slides' list.")
    return data


def find_layout(prs: Presentation, name: str):
    wanted = LAYOUT_ALIASES.get(name.strip().lower(), name).strip().lower()
    for layout in prs.slide_layouts:
        if layout.name.strip().lower() == wanted:
            return layout
    available = [f"{i}:{ly.name!r}" for i, ly in enumerate(prs.slide_layouts)]
    raise SystemExit(f"Unknown layout {name!r}. Available: {available}")


def iter_placeholders(slide):
    for shape in slide.shapes:
        if shape.is_placeholder:
            yield shape


def placeholder_of_types(slide, types):
    for shape in iter_placeholders(slide):
        if shape.placeholder_format.type in types:
            return shape
    return None


def set_run_font(run, *, name=FONT_TITLE, size=None, bold=None, color=None):
    run.font.name = name
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = rgb(color)


def replace_text(shape, text: str | None, *, keep_format=True):
    """Replace placeholder text. Empty string clears the prompt."""
    value = "" if text is None else str(text)
    tf = shape.text_frame
    if keep_format and tf.paragraphs and tf.paragraphs[0].runs:
        tf.paragraphs[0].runs[0].text = value
        for run in tf.paragraphs[0].runs[1:]:
            run.text = ""
        # Drop leftover paragraphs by emptying them.
        for para in tf.paragraphs[1:]:
            if para.runs:
                para.runs[0].text = ""
                for run in para.runs[1:]:
                    run.text = ""
            else:
                para.text = ""
        return
    shape.text = value


def add_textbox(
    slide,
    left,
    top,
    width,
    height,
    text,
    *,
    font=FONT_TITLE,
    size=16,
    bold=False,
    color="ink",
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}[anchor])
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, name=font, size=size, bold=bold, color=color)
    return box


NO_FOOTER_LAYOUTS = {"Title Slide", "Bumper Slide"}


def fill_footer(slide, text: str | None, layout_name: str):
    """python-pptx does not clone footer placeholders. Draw the brand footer ourselves."""
    if text is None or layout_name in NO_FOOTER_LAYOUTS:
        return
    # Staple on Paper. Ink on the gold rails so the line still reads.
    color = "ink" if layout_name in {"Section Title", "Layout 1"} else "staple"
    footer = placeholder_of_types(slide, {PP_PLACEHOLDER.FOOTER})
    if footer is not None:
        replace_text(footer, text)
        if footer.has_text_frame:
            for para in footer.text_frame.paragraphs:
                for run in para.runs:
                    set_run_font(run, name=FONT_TITLE, size=8, bold=False, color=color)
        return
    left = 0.50
    add_textbox(
        slide,
        left,
        5.27,
        3.375,
        0.30,
        text,
        font=FONT_TITLE,
        size=8,
        bold=False,
        color=color,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def fill_title(slide, text: str | None):
    title = placeholder_of_types(
        slide,
        {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.VERTICAL_TITLE},
    )
    if title is not None and text is not None:
        replace_text(title, text)


def fill_subtitle(slide, text: str | None):
    sub = placeholder_of_types(slide, {PP_PLACEHOLDER.SUBTITLE})
    if sub is not None:
        replace_text(sub, text or "")


def body_placeholder(slide):
    for shape in iter_placeholders(slide):
        kind = shape.placeholder_format.type
        if kind in {PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT} and shape.has_text_frame:
            # Skip footer / title-like bodies already handled.
            if kind == PP_PLACEHOLDER.FOOTER:
                continue
            return shape
    return None


def set_bullets(shape, items: list[Any]):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True

    def walk(entries, level):
        rows = []
        for entry in entries:
            if isinstance(entry, str):
                rows.append((entry, level))
            elif isinstance(entry, dict):
                text = entry.get("text") or entry.get("title") or ""
                rows.append((text, level))
                kids = entry.get("children") or entry.get("bullets") or []
                rows.extend(walk(kids, min(level + 1, 2)))
            else:
                rows.append((str(entry), level))
        return rows

    rows = walk(items, 0)
    if len(rows) > MAX_BULLETS:
        print(
            f"warning: {len(rows)} bullets on one slide; brand limit is about {MAX_BULLETS}. Truncating.",
            file=sys.stderr,
        )
        rows = rows[:MAX_BULLETS]
    if not rows:
        rows = [("", 0)]
    for i, (text, level) in enumerate(rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.alignment = PP_ALIGN.LEFT
        # One run so the layout bullet style can attach.
        if p.runs:
            p.runs[0].text = text
            set_run_font(
                p.runs[0],
                name=FONT_BODY,
                size=20 if level == 0 else 16,
                bold=False,
                color="ink",
            )
        else:
            run = p.add_run()
            run.text = text
            set_run_font(
                run,
                name=FONT_BODY,
                size=20 if level == 0 else 16,
                bold=False,
                color="ink",
            )


def add_picture_if_given(slide, spec: dict[str, Any]):
    image = spec.get("image")
    if not image:
        return
    path = Path(image)
    if not path.is_file():
        path = (ROOT / image).resolve()
    pic = placeholder_of_types(slide, {PP_PLACEHOLDER.PICTURE})
    if pic is None:
        return
    if not path.is_file():
        print(f"warning: image not found: {image}", file=sys.stderr)
        return
    pic.insert_picture(str(path))


def _set_cell_border(cell, *, color_hex: str, width_emu: int, edges=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for edge in edges or ("lnL", "lnR", "lnT", "lnB"):
        ln = tcPr.find(qn(f"a:{edge}"))
        if ln is None:
            ln = tcPr.makeelement(qn(f"a:{edge}"), {})
            tcPr.append(ln)
        ln.set("w", str(width_emu))
        for child in list(ln):
            ln.remove(child)
        sf = ln.makeelement(qn("a:solidFill"), {})
        sf.append(sf.makeelement(qn("a:srgbClr"), {"val": color_hex}))
        ln.append(sf)


def style_table(table: Table, headers: list[str], rows: list[list[Any]]):
    def paint(cell, *, fill, text, font, size, bold, color):
        cell.text = ""
        tf = cell.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.10)
        tf.margin_right = Inches(0.08)
        tf.margin_top = Inches(0.08)
        tf.margin_bottom = Inches(0.08)
        try:
            tf._txBody.bodyPr.set("anchor", "ctr")
        except Exception:
            pass
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = "" if text is None else str(text)
        set_run_font(run, name=font, size=size, bold=bold, color=color)
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(fill)

    n_cols = len(headers)
    last_row = len(rows)
    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        paint(
            cell,
            fill="water_cooler",
            text=header,
            font=FONT_TITLE,
            size=12,
            bold=True,
            color="paper",
        )
        # Header reads as one bar. Hairline Paper between cells, Desk rule under.
        _set_cell_border(cell, color_hex=CORE["water_cooler"], width_emu=6350)
        _set_cell_border(cell, color_hex=SECONDARY["desk"], width_emu=19050, edges=("lnB",))
        if col < n_cols - 1:
            _set_cell_border(cell, color_hex=CORE["paper"], width_emu=6350, edges=("lnR",))
    for r, row in enumerate(rows, start=1):
        # Keyboard (cream) on odd body rows so they do not vanish into Paper.
        fill = "keyboard" if r % 2 else "business_card"
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            paint(
                cell,
                fill=fill,
                text=value,
                font=FONT_BODY,
                size=11,
                bold=False,
                color="ink",
            )
            _set_cell_border(cell, color_hex=SECONDARY["desk"], width_emu=6350)
            if r == last_row:
                _set_cell_border(cell, color_hex=SECONDARY["desk"], width_emu=12700, edges=("lnB",))


def add_table_slide(slide, spec: dict[str, Any]):
    headers = [str(h) for h in spec.get("headers") or []]
    rows = spec.get("rows") or []
    if not headers:
        raise SystemExit("table slides need a 'headers' list")
    n_rows = 1 + len(rows)
    n_cols = len(headers)
    normalized = []
    for row in rows:
        values = [row.get(h, "") if isinstance(row, dict) else (row[i] if i < len(row) else "") for i, h in enumerate(headers)]
        if isinstance(row, dict):
            values = [row.get(h, "") for h in headers]
        else:
            values = list(row) + [""] * (n_cols - len(row))
            values = values[:n_cols]
        normalized.append(values)
    # Keep rows even. Short tables stay compact rather than stretching the last row.
    height = max(1.70, min(3.40, 0.48 * n_rows))
    table_shape = slide.shapes.add_table(
        n_rows,
        n_cols,
        Inches(0.50),
        Inches(1.34),
        Inches(9.00),
        Inches(height),
    )
    table = table_shape.table
    row_h = int(table_shape.height / n_rows)
    for row in table.rows:
        row.height = row_h
    style_table(table, headers, normalized)


def add_chart_slide(slide, spec: dict[str, Any]):
    chart_spec = spec.get("chart") or {}
    categories = chart_spec.get("categories") or []
    series_list = chart_spec.get("series") or []
    if not categories or not series_list:
        raise SystemExit("chart slides need chart.categories and chart.series")
    kind_name = (chart_spec.get("type") or "column").lower()
    kinds = {
        "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "bar": XL_CHART_TYPE.BAR_CLUSTERED,
        "line": XL_CHART_TYPE.LINE_MARKERS,
        "pie": XL_CHART_TYPE.PIE,
    }
    if kind_name not in kinds:
        raise SystemExit(f"Unsupported chart type {kind_name!r}. Use column, bar, line, or pie.")
    data = CategoryChartData()
    data.categories = categories
    for series in series_list:
        data.add_series(series.get("name") or "Series", series.get("values") or [])
    chart = slide.shapes.add_chart(
        kinds[kind_name],
        Inches(0.50),
        Inches(1.28),
        Inches(9.00),
        Inches(3.70),
        data,
    ).chart
    chart.has_legend = len(series_list) > 1
    if chart.has_legend:
        chart.legend.include_in_layout = True
        chart.legend.position = XL_LEGEND_POSITION.RIGHT
        chart.legend.font.size = Pt(10)
        chart.legend.font.color.rgb = rgb("ink")
        chart.legend.font.name = FONT_TITLE
    plot = chart.plots[0]
    plot.has_data_labels = False
    for i, series in enumerate(chart.series):
        color = CHART_SERIES[i % len(CHART_SERIES)]
        try:
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = RGBColor.from_string(color)
        except Exception:
            pass
        try:
            series.format.line.color.rgb = RGBColor.from_string(color)
        except Exception:
            pass
    def _axis_font(axis):
        try:
            axis.tick_labels.font.size = Pt(10)
            axis.tick_labels.font.color.rgb = rgb("ink")
            axis.tick_labels.font.name = FONT_BODY
        except Exception:
            pass
        try:
            axis.format.line.color.rgb = rgb("desk")
        except Exception:
            pass
    try:
        _axis_font(chart.category_axis)
        _axis_font(chart.value_axis)
    except Exception:
        pass
    try:
        chart.value_axis.has_major_gridlines = True
        chart.value_axis.major_gridlines.format.line.color.rgb = rgb("desk")
    except Exception:
        pass
    # Plot / wall stay Paper when the format API allows it.
    try:
        chart.plot_area.format.fill.solid()
        chart.plot_area.format.fill.fore_color.rgb = rgb("paper")
    except Exception:
        pass


def add_section_copy(slide, spec: dict[str, Any]):
    eyebrow = spec.get("eyebrow") or spec.get("kicker")
    title = spec.get("title") or spec.get("statement") or ""
    if eyebrow:
        add_textbox(
            slide,
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
    add_textbox(
        slide,
        3.32,
        1.46,
        5.61,
        2.20,
        title,
        font=FONT_TITLE,
        size=28,
        bold=True,
        color="ink",
        anchor=MSO_ANCHOR.TOP,
    )


def add_two_column_items(slide, spec: dict[str, Any]):
    items = spec.get("items") or spec.get("right") or []
    if isinstance(items, dict):
        items = items.get("items") or []
    items = items[:3]
    top = 0.76
    gap = 1.28
    for i, item in enumerate(items):
        if isinstance(item, str):
            heading, body = item, ""
        else:
            heading = item.get("title") or item.get("heading") or ""
            body = item.get("body") or item.get("text") or ""
        y = top + i * gap
        add_textbox(
            slide,
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
        add_textbox(
            slide,
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
        if body:
            add_textbox(
                slide,
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


def add_cover_date(slide, date_text: str | None):
    if not date_text:
        return
    add_textbox(
        slide,
        0.51,
        4.96,
        4.00,
        0.30,
        date_text,
        font=FONT_TITLE,
        size=12,
        bold=False,
        color="ink",
    )


def add_closing_caption(slide, text: str | None):
    if not text:
        return
    # Layout lockup occupies 1.79–3.31 in. Keep the caption clear of the wordmark.
    add_textbox(
        slide,
        1.50,
        3.58,
        7.00,
        0.40,
        text,
        font=FONT_TITLE,
        size=16,
        bold=False,
        color="paper",
        align=PP_ALIGN.CENTER,
    )


def fill_intro(slide, spec: dict[str, Any]):
    # Intro layouts expose body placeholders in name / title / company order.
    bodies = [
        shape
        for shape in iter_placeholders(slide)
        if shape.placeholder_format.type == PP_PLACEHOLDER.BODY
    ]
    values = [
        spec.get("name") or spec.get("title") or "",
        spec.get("role") or spec.get("item_title") or spec.get("subtitle") or "",
        spec.get("company") or spec.get("org") or "",
    ]
    # Intro_One: idx 10 name, 11 title, 12 company
    by_idx = {shape.placeholder_format.idx: shape for shape in bodies}
    mapping = [(10, values[0]), (11, values[1]), (12, values[2])]
    if all(idx in by_idx for idx, _ in mapping):
        for idx, value in mapping:
            replace_text(by_idx[idx], value)
    elif bodies:
        for shape, value in zip(bodies, values):
            replace_text(shape, value)
    add_picture_if_given(slide, spec)


def add_notes(slide, notes: str | None):
    if not notes:
        return
    slide.notes_slide.notes_text_frame.text = notes


def build_slide(prs: Presentation, spec: dict[str, Any], footer: str):
    intent = spec.get("layout") or spec.get("intent") or "content"
    layout = find_layout(prs, intent)
    slide = prs.slides.add_slide(layout)
    layout_name = layout.name.strip()

    fill_footer(slide, spec.get("footer", footer), layout_name)

    if layout_name == "Title Slide":
        fill_title(slide, spec.get("title"))
        fill_subtitle(slide, spec.get("subtitle") or spec.get("subhead"))
        add_cover_date(slide, spec.get("date"))
    elif layout_name == "Section Title":
        add_section_copy(slide, spec)
    elif layout_name == "Bumper Slide":
        add_closing_caption(slide, spec.get("title") or spec.get("caption"))
    elif layout_name.startswith("Intro_"):
        fill_intro(slide, spec)
    elif intent.strip().lower() in {"table"}:
        fill_title(slide, spec.get("title"))
        add_table_slide(slide, spec)
    elif intent.strip().lower() in {"chart"}:
        fill_title(slide, spec.get("title"))
        add_chart_slide(slide, spec)
    elif layout_name in {"1/2_Headline", "1/2 Headline_Alt"}:
        fill_title(slide, spec.get("title"))
        title = placeholder_of_types(
            slide, {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE}
        )
        if title is not None and title.has_text_frame:
            # Middle-align the short title with the first numbered item.
            try:
                title.text_frame._txBody.bodyPr.set("anchor", "ctr")
            except Exception:
                pass
        add_two_column_items(slide, spec)
    else:
        fill_title(slide, spec.get("title"))
        fill_subtitle(slide, spec.get("subtitle") or spec.get("subhead"))
        bullets = spec.get("bullets") or spec.get("body")
        body = body_placeholder(slide)
        if bullets and body is not None:
            if isinstance(bullets, str):
                bullets = [bullets]
            set_bullets(body, bullets)
        elif spec.get("body") and body is not None and isinstance(spec.get("body"), str):
            set_bullets(body, [spec["body"]])
        add_picture_if_given(slide, spec)
        if spec.get("headers"):
            add_table_slide(slide, spec)
        if spec.get("chart"):
            add_chart_slide(slide, spec)

    add_notes(slide, spec.get("notes"))
    return slide


def apply_core_props(prs: Presentation, outline: dict[str, Any]):
    title = outline.get("title") or "Workday presentation"
    prs.core_properties.title = title
    prs.core_properties.author = outline.get("author") or "Workday"
    prs.core_properties.last_modified_by = "Workday PPTX skill"
    if outline.get("subject"):
        prs.core_properties.subject = outline["subject"]


def build(outline: dict[str, Any], template: Path, dest: Path):
    prs = Presentation(str(template))
    if len(prs.slides) != 0:
        print("warning: template already contains slides; new slides will be appended.", file=sys.stderr)
    footer = outline.get("footer", "Workday Confidential")
    for spec in outline.get("slides") or []:
        build_slide(prs, spec, footer)
    apply_core_props(prs, outline)
    dest.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(dest))
    print(f"Wrote {dest} ({len(prs.slides)} slides) from {template.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Workday-branded PPTX from an outline.")
    parser.add_argument("outline", type=Path, help="JSON or YAML outline")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .pptx path")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Masters-only template")
    args = parser.parse_args(argv)
    if not args.template.is_file():
        raise SystemExit(f"Template not found: {args.template}")
    outline = load_outline(args.outline)
    dest = args.output
    if dest is None:
        dest = args.outline.with_suffix(".pptx")
    build(outline, args.template, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
