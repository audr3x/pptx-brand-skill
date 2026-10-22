---
name: workday-deck-prompting
description: Turn a brief, notes, or a vague deck request into a Workday outline that the workday-pptx and workday-google-slides builders fully support. Use when someone asks for a Workday deck without a ready outline, asks how to prompt for a deck, wants to fix one slide, or asks for something the builders may not support (photos, chart types, speaker notes, custom formatting).
---

# Workday deck prompting

The full guide for people is [docs/PROMPTING.md](../../../docs/PROMPTING.md). This skill is the short version for Cursor. Build with [workday-pptx](../workday-pptx/SKILL.md) or [workday-google-slides](../workday-google-slides/SKILL.md) once the outline is agreed.

## Workflow

1. Ask for whatever is missing, in one message: target (PowerPoint or Google Slides), audience, goal, slide count, and the real content (bullets, numbers, table rows, names). For Google Slides also ask which cover image option the org allows (A Drive link share, B public URL, C no image).
2. Write the outline as YAML (shape of [examples/outline.yaml](../../../examples/outline.yaml)). Use only facts the user gave. Write `TODO` for anything missing. Never invent numbers, names, or quotes.
3. Run the gate and fix every error:

   ```bash
   python3 scripts/check_outline.py --target pptx|slides <outline>
   ```

   Tell the user about each warning that changes what they will see. Every warning and limit is explained in [docs/LIMITS.md](../../../docs/LIMITS.md).
4. Show the outline. Build only after the user agrees, unless they asked to build straight away.
5. After the build, render or read back every slide and compare with the outline.

## What the outline can hold

| `layout` | Fields | Limits |
| --- | --- | --- |
| `title` | `title`, `subtitle`, `date` | First slide |
| `section` | `eyebrow`, `title` | About 8 words |
| `content` | `title`, `bullets` or `body` | 6 bullets (sub-bullets count) |
| `two-column` | `title`, `items: [{title, body}]` | 3 items |
| `table` | `title`, `headers`, `rows` | About 6 rows |
| `chart` | `title`, `chart: {type, categories, series: [{name, values}]}` | Numbers, one per category |
| `closing` | `title` (caption) | |
| `intro` | `name`, `role`, `company`, `image` | |
| `photo-right` | `title`, `image` | No bullets |
| `photos` | `title`, `image` | Only the first photo slot |

Any slide: `notes`, `footer`. Deck: `title`, `subtitle`, `date`, `author`, `subject`, `footer`.

Google Slides differences: every chart draws as clustered columns (shapes, not editable data); `image` and `notes` are ignored; `intro` fills only `title`; nested bullets show at one level. If the user needs those, recommend PowerPoint or a manual step, and say so before building.

## Translate requests the outline cannot hold

| Request | Do this |
| --- | --- |
| A color, font, size, position, background, animation, slide number | Explain the template sets it. Do not add fields the builders ignore |
| More than 6 bullets | Split into two `content` slides |
| Photo beside bullets | `photo-right` then `content` |
| Logo on other slides | Decline. Cover and closing carry it |
| A long title or a paragraph as a title | Cut to one line (about 50 characters) that states the point; move the rest to bullets |
| A table longer than about 6 rows or wider than 6 columns | Split rows across slides; drop or merge columns |
| A chart with more than 5 series or about 12 categories | Keep the series that matter, group categories |
| Both `bullets` and `body` on one slide | Merge them into `bullets` |
| "Make a deck about X" with no facts | Ask for the facts. If the user wants a draft anyway, write `TODO` for each missing fact and do not build until every `TODO` is filled (the gate warns on any `TODO`) |
| Negative values in a pie chart | Use a column chart |
| Pie, line, or bar chart in Google Slides | Offer PowerPoint, a column chart, or a Sheets chart added by hand |
| "Fix slide N" | Change only that slide's fields in the outline, re-run the gate, rebuild. In Google Slides, rebuild on a fresh copy, or edit only the `wd_sN_*` objects with a targeted `update_presentation` the user approved |

## Tone

Sentence-case titles that state the point, one line. Bullets are one idea, under about 12 words, no ending periods. Plain language, real numbers. No em dashes in deck copy.
