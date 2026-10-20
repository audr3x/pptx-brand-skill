---
name: workday-google-slides
description: Generate on-brand Workday Google Slides decks from a brief or outline. Use when asked for a Workday presentation in Google Slides, a branded Workspace deck, or to import assets/template.pptx into Slides. Copies a Workday template (never a blank theme), fills layouts through the Slides API or gws, and follows BRAND.md.
---

# Workday Google Slides

Same brand system as [workday-pptx](../workday-pptx/SKILL.md), on Google Slides. Read [BRAND.md](../../../BRAND.md) first. Do not invent colors, fonts, or chrome.

Workday has no canonical public Slides ID in this repo. You either import [assets/template.pptx](../../../assets/template.pptx) once, or the user hands you a template deck ID. After that, **copy the template and edit only the copy**.

```
Workday Slides compliance:
- [ ] Read this skill and BRAND.md
- [ ] Template is a copy (or a first-time PPTX import), never the master
- [ ] Layout picked by intent (no blank slide when a Workday layout exists)
- [ ] Tokens only (core palette first). Archivo, Arial fallback
- [ ] Footer is Workday Confidential. About 6 bullets max
- [ ] Re-read the deck and check styles before calling it done
```

## Auth (pick one). Never commit credentials

### A. Cursor Google plugins (closest to Anina's GTM skill)

Install and sign in to the **Google Drive** and **Google Slides** plugins with the Workday Google account. Then:

1. Drive `copy_file` on the template ID
2. Slides `read_presentation` / `update_presentation` (`batchUpdate`) on the **new** ID only
3. `read_presentation` again to verify

If either plugin is missing or unauthenticated, stop and ask the user to connect it. Do not invent a Runtime Secret.

### B. Google Workspace CLI (`gws`)

```bash
# install: https://github.com/googleworkspace/cli
npm install -g @googleworkspace/cli
# or: brew install googleworkspace-cli

gws auth setup          # once, needs gcloud or a Cloud project
gws auth login -s drive,slides
```

Manual OAuth (no gcloud): Desktop-app client JSON at `~/.config/gws/client_secret.json`, add the Workday user as a test user, then `gws auth login -s drive,slides`. Enable the Drive and Slides APIs on the Cloud project.

Headless / CI: `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` or `GOOGLE_APPLICATION_CREDENTIALS` pointing at a file **outside the repo**. Never write `credentials.json`, `client_secret.json`, or tokens into this project.

### C. Python builder (this repo)

```bash
pip3 install -r requirements.txt
# Plan only (no network). Safe to run anywhere:
python3 scripts/build_slides.py examples/outline.yaml --dry-run \
  -o examples/example-slides-requests.json

# Live apply, after auth:
python3 scripts/build_slides.py examples/outline.yaml \
  --template-id "$WORKDAY_SLIDES_TEMPLATE_ID" \
  --backend gws
# or --backend api   (ADC / GOOGLE_APPLICATION_CREDENTIALS)
```

`--import-pptx assets/template.pptx` uploads the PPTX and converts it to a Google Slides template (first-time only). Save that ID as `WORKDAY_SLIDES_TEMPLATE_ID` and copy it for every new deck.

## Seed the Workday template

The PPTX in this repo is masters and layouts only. Import it once so those layouts exist in Slides.

```bash
# gws: upload + convert
gws drive files create \
  --json '{"name": "Workday Corporate Template", "mimeType": "application/vnd.google-apps.presentation"}' \
  --upload assets/template.pptx

# or the builder
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws
```

In the Drive UI: upload `assets/template.pptx` → Open with Google Slides. That conversion keeps the Workday master and the 15 layouts.

If the user already has a branded Slides file, use that ID. Do not start from `presentations.create` (blank theme) unless import failed and they said so.

## Create a deck

1. Copy the template. Never `batchUpdate` the template ID.

```bash
gws drive files copy \
  --params '{"fileId": "<TEMPLATE_ID>"}' \
  --json '{"name": "<Deliverable title>"}'
```

Drive plugin: `copy_file` with that `fileId` and the deliverable title.

2. `presentations.get` the copy. Map layout **display names** (strip whitespace, case-insensitive) to `layoutId`.

3. For each outline slide, `createSlide` with `slideLayoutReference.layoutId` (the Workday layout). Prefer this over `predefinedLayout` and over `importSlides` from a blank deck.

4. Fill placeholders (`deleteText` + `insertText` + `updateTextStyle`). Draw missing chrome (section title, half-headline items, footer, cover date, bumper caption) at the inch positions in `BRAND.md`.

5. Delete leftover `Click to edit` / `Insert slide title` prompts.

6. Read the deck again. Check fonts, fills, footer, contrast.

`scripts/build_slides.py` does steps 1–5. Extend it instead of starting from a blank `presentations.create`.

## Layouts by intent

Same map as the PPTX skill. Google remaps placeholder object IDs on import; resolve them by layout name, then by placeholder type.

| Intent | Outline `layout` | Workday layout | Fill |
| --- | --- | --- | --- |
| Title / cover | `title` | Title Slide | `title`, `subtitle`, optional `date` |
| Section / divider | `section` | Section Title | `eyebrow` + `title` in the open field (no title placeholder) |
| Content / bullets | `content` | Title and Content | `title`, `bullets` (max ~6) |
| Two-column | `two-column` | 1/2_Headline | left title, up to 3 numbered `items` |
| Table | `table` | Title Only | `title`, `headers`, `rows` |
| Chart | `chart` | Title Only | `title` + on-brand columns (or a Sheets chart) |
| Closing | `closing` | Bumper Slide | optional caption under the smile |
| Intro | `intro` | Intro_One | `name`, `role`, `company` |
| Blank | `blank` | Blank White Background | last resort |

Content layout XML name is `Title and Content ` (trailing space). Match after strip.

If a Workday `layoutId` is missing (import dropped it), stop and re-import. Do not silently switch to `TITLE_AND_BODY` except as a last-resort fallback the user approved.

## Brand rules

- **Colors.** Only tokens in `BRAND.md` / `assets/brand-tokens.json`. Prefer theme slots on the copied deck (`dk1` = Ink, `accent1` = Water Cooler) when they still match. Otherwise RGB from the token file. If a hex is not in that file, do not use it.
- **Type.** Archivo titles, Archivo Light body. Google Slides will substitute Arial when Archivo is not in the account. Enable Archivo from Google Fonts in the theme if you can. Never switch to Calibri, Inter, Roboto, or Proxima Nova.
- **Sizes.** Cover 36 pt. Slide / section title 28 pt bold Ink. Body 18–20 pt. Footer 8 pt Staple `#7D8B99` (Ink on the gold section rail).
- **Bullets.** At most about 6. Use `createParagraphBullets` `BULLET_DISC_CIRCLE_SQUARE`. Do not type `•` into the run.
- **Footer.** `Workday Confidential`. No slide numbers.
- **Logo.** Title Slide and Bumper Slide already carry the white lockup. Do not recolor it or drop it on Paper.
- **Tables.** Water Cooler header, Keyboard / Business Card rows, Ink body, Desk rules.
- **Charts.** Series order: Water Cooler, Lunch Break, Ballpoint, Blue Sky, Ink. No Google default orange / green / purple.
- **Density.** 0.50 in side inset. Keep copy above y = 5.20 in. One idea per slide. 16:9 (`10.00 × 5.625 in`, 720 × 405 pt).

## Outline

Same shape as the PPTX builder. [examples/outline.yaml](../../../examples/outline.yaml) is the shared example.

```yaml
title: Planning workshop
footer: Workday Confidential
slides:
  - layout: title
    title: Planning workshop
    subtitle: Sample deck
    date: October 2026
  - layout: content
    title: Working agreements
    bullets:
      - One idea per slide
      - Six bullets at most
```

## API recipes (gws or Slides `batchUpdate`)

`createSlide` on a Workday layout:

```json
{
  "createSlide": {
    "objectId": "wd_s3",
    "slideLayoutReference": { "layoutId": "<Title and Content layoutId>" }
  }
}
```

Replace leftover prompt text, then style:

```json
[
  { "deleteText": { "objectId": "wd_s3_title", "textRange": { "type": "ALL" } } },
  { "insertText": { "objectId": "wd_s3_title", "text": "Working agreements", "insertionIndex": 0 } },
  {
    "updateTextStyle": {
      "objectId": "wd_s3_title",
      "style": {
        "fontFamily": "Archivo",
        "fontSize": { "magnitude": 28, "unit": "PT" },
        "bold": true,
        "foregroundColor": { "opaqueColor": { "rgbColor": { "red": 0.059, "green": 0.180, "blue": 0.400 } } }
      },
      "textRange": { "type": "ALL" },
      "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
  }
]
```

`importSlides` from the Workday template is fine when adding slides to an existing copy (`preserveTheme`: `USE_DESTINATION_THEME`). Do not import from a customer deck.

Images: `createImage` needs a public URL. Drive uploads of the smile PNG are already on the title and bumper layouts. Do not re-place them.

Charts: the builder draws Water Cooler / Lunch Break columns so a deck does not depend on Sheets. For a live data chart, create a Sheets chart with those series colors and `createSheetsChart` / `refreshSheetsChart`.

## Do not

- Do not `batchUpdate` the template ID to "save a copy step"
- Do not mix blank untemplated slides into a branded deck
- Do not use Inter, Cursor orange, GTM LIGHT2 tiles, or any other company's tokens
- Do not commit `credentials.json`, `client_secret.json`, `.env`, or `gws` token files
- Do not copy confidential sentences from a reference deck into examples

## Visual check

After a live apply, open `https://docs.google.com/presentation/d/<id>/edit` and look at every slide (plugin thumbnail or Drive export PDF). Confirm Ink on Paper, Paper on Ink / Ballpoint, footer clearance, smile on title and bumper only, and no leftover master prompts.
