---
name: workday-pptx
description: Generate on-brand Workday PowerPoint (.pptx) decks from a brief or outline. Use when asked for a Workday presentation, corporate template slides, or a branded PPTX. Starts from assets/template.pptx, fills Workday layouts with python-pptx, and follows BRAND.md. Never invent off-brand colors or fonts.
---

# Workday PPTX

Build new decks from the Workday Corporate Template that lives in this repo. Team setup is in [GETTING_STARTED.md](../../../GETTING_STARTED.md). For turning a brief into an outline, see [docs/PROMPTING.md](../../../docs/PROMPTING.md) and the [workday-deck-prompting](../workday-deck-prompting/SKILL.md) skill; check outlines with `python3 scripts/check_outline.py`. Read [BRAND.md](../../../BRAND.md) before drawing a slide. Start from [assets/template.pptx](../../../assets/template.pptx). Prefer [scripts/build_deck.py](../../../scripts/build_deck.py) over a blank `Presentation()`.

For Google Slides, use [workday-google-slides](../workday-google-slides/SKILL.md) instead of converting a finished `.pptx` by hand.

## Quick path

1. If the request has no real content (numbers, names, dates, rows), ask for it first. See the guardrails below.
2. Turn the brief into a short slide list. One idea per slide.
3. Pick a layout by intent (table below). Do not invent a new master.
4. Write a JSON or YAML outline (see [examples/outline.yaml](../../../examples/outline.yaml)). Save the user's request and notes to a file, then check, build, and read back:

```bash
python3 scripts/check_outline.py --target pptx --prompt out/request.md out/outline.yaml
python3 scripts/build_deck.py out/outline.yaml -o out/deck.pptx
python3 scripts/readback.py out/outline.yaml out/deck.pptx --show
```

5. Fix every `missing:` line from readback and rebuild. Render with LibreOffice if you can and look at the PNGs: titles, the first bullet under each title, footer, and colors.
6. Report only what readback confirms (guardrails below).

If the outline is the wrong tool (heavy custom drawing on `Title Only`), still start from the template, add the matching layout, and paint only with tokens from `BRAND.md`.

## Content guardrails

- **Ask first on vague requests.** "A deck about X" with no facts gets one message asking for audience, slide count, and the real content. If the user wants a draft anyway, write `TODO` for every gap.
- **Use only what the user gave.** Never infer or invent a date, number, name, or quote. "Next month" is not a date: write `date: "TODO: date"` and ask. Leave out figures the user marks as old, a typo, or confidential. When two instructions conflict (slide count, dates), pick one or ask, and name the conflict in your reply.
- **Run the gate with the prompt.** `check_outline.py --prompt <file>` warns on every date or figure that is not in the user's text. Replace each one with the user's value or `TODO`.
- **Quote text that contains `: `.** `- "Risk: audit freeze in January"`. Unquoted, YAML reads it as a mapping.
- **Read back before you report.** `scripts/readback.py` lists every outline title, bullet, item, cell, and chart label that is not on the built slides and exits 1. Fix and rebuild until it prints `ok`.
- **Look hardest at wrapped titles and first bullets.** A title past the layout's limit wraps into the first bullet; the gate warns, and the render shows it. Shorten the title rather than accept the warning.
- **Claim only what readback confirms.** Your reply states the slide count, what each slide holds, every `TODO` left, each warning that changes what the user sees, and anything you cut, split, or changed. Write "nothing was invented" or "everything is included" only when readback passed and the prompt check showed no warnings.

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
| Intro | `intro` | Intro_One | `name`, `role`, `company`, optional `image` |
| Photo right | `photo-right` | Photo-Right | `title`, `image` |
| Blank | `blank` | Blank White Background | last resort |

Exact names, indexes, and geometry are in `BRAND.md`. The content layout's XML name is `Title and Content ` (trailing space). The builder matches names case-insensitively and strips whitespace.

Many layouts are chrome only. `Section Title` has a footer and a left gradient, not a title placeholder. `1/2_Headline` has a left title only. `Bumper Slide` has the smile and nothing else. Draw the missing copy in the positions from `BRAND.md`.

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

Chart types: `column`, `bar`, `line`, `pie`.

## Brand rules the agent must keep

- **Colors.** Only tokens in `BRAND.md` / `assets/brand-tokens.json`. Core palette first. Secondary palette rarely. If a hex is not in that file, do not use it.
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

Look at every PNG. Check that no title runs into the first bullet, then contrast (Ink on Paper, Paper on Ink / Ballpoint), footer clearance, smile placement, and that no off-brand blue or gray appeared. Fix the outline or the builder, then render again.
