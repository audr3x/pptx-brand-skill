---
name: workday-pptx
description: Generate on-brand Workday PowerPoint (.pptx) decks from a brief or outline. Use when asked for a Workday presentation, corporate template slides, or a branded PPTX. Starts from assets/template.pptx, fills Workday layouts with python-pptx, and follows BRAND.md. Never invent off-brand colors or fonts.
---

# Workday PPTX

Build new decks from the Workday Corporate Template that lives in this repo. Team setup is in [GETTING_STARTED.md](../../../GETTING_STARTED.md). Read [BRAND.md](../../../BRAND.md) before drawing a slide. Start from [assets/template.pptx](../../../assets/template.pptx). Prefer [scripts/build_deck.py](../../../scripts/build_deck.py) over a blank `Presentation()`.

For Google Slides, use [workday-google-slides](../workday-google-slides/SKILL.md) instead of converting a finished `.pptx` by hand.

## Quick path

1. Turn the brief into a short slide list. One idea per slide.
2. Pick a layout by intent (table below). Do not invent a new master.
3. Write a JSON or YAML outline (see [examples/outline.yaml](../../../examples/outline.yaml)).
4. Validate the template and registry, then build:

```bash
python3 scripts/validate_brand.py
python3 scripts/build_deck.py examples/outline.yaml -o out/deck.pptx
```

5. Open the file. Confirm titles, footer, and colors. If you can render with LibreOffice, do that and look at the PNGs.

If the outline is the wrong tool (heavy custom drawing on `Title Only`), still start from the template, add the matching layout, and paint only with tokens from `BRAND.md`.

## Layouts by intent

| Intent | Outline `layout` | Template layout | Fill |
| --- | --- | --- | --- |
| Title / cover | `title` | Title Slide | `title`, `subtitle`, optional `date` |
| Section / divider | `section` | Section Title | `eyebrow`, `title` (drawn in the open field) |
| Content / bullets | `content` | Title and Content | `title`, `bullets` (max ~6) |
| Two-column | `two-column` | 1/2_Headline | `title` on the left, up to 3 `items` on the right |
| Table | `table` | Title Only | `title`, `headers`, `rows` |
| Chart | `chart` | Title Only | `title`, `chart.type/categories/series` |
| Closing | `closing` | Bumper Slide | optional `title` under the smile |
| One speaker | `intro` / `intro-one` | Intro_One | one entry in `speakers`, or the legacy `name` / `role` / `company` fields |
| Three speakers | `intro-three` | Intro_Three | exactly 3 `speakers` |
| Four speakers | `intro-four` | Intro_Four | exactly 4 `speakers` |
| Warm feature grid | `feature-grid` | Title Only_Alt | `title`, optional `subtitle`, 3 `items` |
| Compact half-headline | `two-column-alt` | 1/2 Headline_Alt | `title`, up to 6 `items` |
| Agenda | `agenda` | Section Title | `title`, up to 6 `items` |
| Rail content | `rail` | Layout 1 | `title`, `body` |
| Three photos | `three-photos` | 3-Photos | `title`, exactly 3 `images` |
| Photo right | `photo-right` | Photo-Right | `title`, `image`, optional `items` |
| Timeline | `timeline` | Title Only | `title`, up to 7 `items` |
| Blank | `blank` | Blank White Background | optional `title` and `body`; last resort |

`assets/brand-tokens.json` is the programmatic source for colors, exact layout names, placeholder indexes, limits, and geometry. `scripts/brand.py` validates that registry and normalizes outlines for both builders. Do not copy those values into a builder.

The content layout's XML name is `Title and Content ` with a trailing space. The registry keeps the exact template name. The builder strips whitespace only when it locates the layout.

## Outline shape

```yaml
title: Deck title
subtitle: Optional deck subtitle
date: October 2026
footer: Workday Confidential
slides:
  - layout: title
    title: Deck title
    subtitle: One-line context
    date: October 2026
  - layout: content
    title: Slide title
    bullets:
      - First point
      - text: Nested parent
        children:
          - Child point
```

Supported slide fields: `layout` (or `intent`), `title`, `subtitle` / `subhead`, `date`, `eyebrow`, `bullets` / `body`, `items` (`title` + `body`), `headers`, `rows`, `chart`, `name`, `role`, `company`, `image`, `footer`, `notes`.

Intro layouts accept `speakers`. Each speaker can contain `name`, `role`, `company`, and optional `image`. `three-photos` accepts `images`.

Chart types: `column`, `bar`, `line`, `pie`.

## Brand rules the agent must keep

- **Colors.** Only tokens in `assets/brand-tokens.json`. Core palette first. Secondary palette rarely. Blue Sky is `#9ECFFF`; do not copy the conflicting sample swatch fill.
- **Type.** Archivo for titles, Archivo Light for body. Arial is the theme fallback. Never switch to Calibri, Inter, Roboto, or Proxima Nova.
- **Sizes.** Cover title 36 pt. Slide / section title 28 pt bold Ink. Body 18 to 20 pt. Footer 8 pt Staple `#7D8B99`.
- **Bullets.** At most about 6. Ink `•` from the placeholder style. Do not type a unicode bullet into the run.
- **Footer.** `Workday Confidential` on every layout that already has the footer placeholder. Do not add slide numbers.
- **Logo.** Title Slide and Bumper Slide already carry the lockup PNG (white wordmark + orange smile `#FC5B05`). Do not recolor it or invent a second mark.
- **Tables.** Water Cooler header, Keyboard / Business Card rows, Ink body, Desk rules.
- **Charts.** Series order: Water Cooler, Lunch Break, Ballpoint, Blue Sky, Ink. Paper plot area. Ink labels.
- **Density.** 0.50 in side inset. Keep copy above y = 5.20 in. One idea per slide.

## python-pptx notes

```python
from pptx import Presentation
prs = Presentation("assets/template.pptx")
layout = next(l for l in prs.slide_layouts if l.name.strip() == "Title and Content")
slide = prs.slides.add_slide(layout)
```

- Fill placeholders. Do not delete and recreate the title or footer.
- Setting `.text` on a placeholder can drop Archivo. Prefer editing the first run, or set `run.font.name` back to `Archivo` / `Archivo Light` and `run.font.color.rgb` to a brand token.
- `scripts/build_deck.py` already does this. Extend it when a brief needs a new pattern, instead of starting from `Presentation()` with no template.
- New shapes must use Business Card `#F1F3F6` or Paper fills, Ink text, and no random shadows.

## Do not

- Do not copy customer or confidential sentences out of any reference deck into the repo or into example output.
- Do not use Office theme 2 / theme 3 colors (the notes and handout leftovers).
- Do not put a rainbow chart palette on a Workday slide.
- Do not add accent underlines under titles.
- Do not ship leftover `Click to edit` or `Insert slide title` prompts.

## Visual check

Render when LibreOffice is available:

```bash
soffice --headless --convert-to pdf --outdir /tmp out/deck.pptx
pdftoppm -png -r 140 /tmp/deck.pdf /tmp/deck-slide
```

Look at every PNG. Check contrast (Ink on Paper, Paper on Ink / Ballpoint), footer clearance, smile placement, and that no off-brand blue or gray appeared. Fix the outline or the builder, then render again.
