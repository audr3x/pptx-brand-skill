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
# Plan only (no network). Includes slidePlans:
python3 scripts/build_slides.py examples/outline.yaml --dry-run \
  -o examples/example-slides-requests.json

# Two-phase connector (Drive/Slides plugins, no gws):
python3 scripts/build_slides.py examples/outline.yaml --phase creates -o creates.json
# send creates.json via update_presentation, then save read_presentation to get.json
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json -o fills.json

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

3. For each outline slide, `createSlide` with `slideLayoutReference.layoutId` (the Workday layout). Prefer this over `predefinedLayout` and over `importSlides` from a blank deck. Title placeholders come back as **`CENTERED_TITLE`**, not `CENTER_TITLE`.

4. Two-phase fill. Phase 1 is only `createSlide`. Then `read_presentation` / `presentations.get`. Phase 2 binds fills to the real object IDs (`scripts/build_slides.py --phase fills --presentation get.json`).

5. Fill placeholders with `insertText` + `updateTextStyle`. Send `deleteText` **only** when the shape already has text. Empty new placeholders error on `deleteText ALL`.

6. Draw missing chrome: `updatePageProperties` page fill on Title Slide (**Ballpoint**) and Bumper Slide (**Ink**) — Slides drops the Day Crop / Ink pictures and Keyboard cream shows through. Section rail (2.743 in Tack / Keyboard / Lunch Break stack), half-headline items, footer box at **x = 0.50 in**, cover date, bumper caption.

7. Read the deck again. Check fonts, fills, footer, contrast.

`scripts/build_slides.py` does this. Extend it instead of starting from a blank `presentations.create`. Do not reuse a footer placeholder objectId for a new text box. Google does not copy PPTX footer placeholders onto new slides.

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
- **Type.** `fontFamily` is always **Archivo**. Body uses `weightedFontFamily: {fontFamily: "Archivo", weight: 300}` (do not send `Archivo Light` — Google falls back to a serif). Titles use weight 400, or 700 when bold. Include `weightedFontFamily` in `fields`. Enable Archivo from Google Fonts if you can. Arial is the last-resort fallback. Never switch to Calibri, Inter, Roboto, or Proxima Nova.
- **Sizes.** Cover 36 pt. Slide / section title 28 pt bold Ink (Paper on Title Slide). Body 18–20 pt. Footer 8 pt Staple `#7D8B99` at **x = 0.50 in** (Ink on the gold section rail).
- **Title Slide.** Set `pageBackgroundFill` to Ballpoint (`#0057AE`) on the slide itself. The PPTX Day Crop picture often does not copy, and the leftover theme fill is Keyboard cream. Paper (`#FFFFFF`) for title, subtitle, and date.
- **Bumper Slide.** Set `pageBackgroundFill` to Ink (`#0F2E66`). Paper caption under the smile.
- **Bullets.** At most about 6. Use `createParagraphBullets` `BULLET_DISC_CIRCLE_SQUARE`. Do not type `•` into the run.
- **Footer.** `Workday Confidential`. No slide numbers.
- **Logo.** Title Slide and Bumper Slide already carry the white lockup. Do not recolor it or drop it on Paper.
- **Tables.** Water Cooler header, Keyboard / Business Card rows, Ink body, Desk rules.
- **Charts.** Series order: Water Cooler, Lunch Break, Ballpoint, Blue Sky, Ink. No Google default orange / green / purple.
- **Density.** 0.50 in side inset, including the footer. Keep copy above y = 5.20 in. One idea per slide. 16:9 (`10.00 × 5.625 in`, 720 × 405 pt).
- **Section Title.** The PPTX rail is `gradient-day-crop-warm.svg` at 2.743 in. If Slides drops that picture, draw the Tack / Keyboard / Lunch Break stack and send it to the back. Eyebrow and statement stay in the open field at x = 3.32 in.

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

Fill a placeholder. Skip `deleteText` when the shape is empty. Title type is `CENTERED_TITLE`.

```json
[
  { "insertText": { "objectId": "wd_s3_title", "text": "Working agreements", "insertionIndex": 0 } },
  {
    "updateTextStyle": {
      "objectId": "wd_s3_title",
      "style": {
        "fontFamily": "Archivo",
        "weightedFontFamily": { "fontFamily": "Archivo", "weight": 700 },
        "fontSize": { "magnitude": 28, "unit": "PT" },
        "bold": true,
        "foregroundColor": { "opaqueColor": { "rgbColor": { "red": 0.059, "green": 0.180, "blue": 0.400 } } }
      },
      "textRange": { "type": "ALL" },
      "fields": "fontFamily,weightedFontFamily,fontSize,bold,foregroundColor"
    }
  }
]
```

Body / Archivo Light equivalent:

```json
{
  "fontFamily": "Archivo",
  "weightedFontFamily": { "fontFamily": "Archivo", "weight": 300 }
}
```

`importSlides` from the Workday template is fine when adding slides to an existing copy (`preserveTheme`: `USE_DESTINATION_THEME`). Do not import from a customer deck.

Images: `createImage` needs a public URL. Drive uploads of the smile PNG are already on the title and bumper layouts. Do not re-place them.

Charts: the builder draws Water Cooler / Lunch Break columns so a deck does not depend on Sheets. For a live data chart, create a Sheets chart with those series colors and `createSheetsChart` / `refreshSheetsChart`.

## Do not

- Do not `batchUpdate` the template ID to "save a copy step"
- Do not mix blank untemplated slides into a branded deck
- Do not send placeholder type `CENTER_TITLE` (it is `CENTERED_TITLE`)
- Do not send `fontFamily: "Archivo Light"`
- Do not `deleteText` on an empty placeholder
- Do not reuse a footer placeholder id for a new text box
- Do not use Inter, Cursor orange, GTM LIGHT2 tiles, or any other company's tokens
- Do not commit `credentials.json`, `client_secret.json`, `.env`, or `gws` token files
- Do not copy confidential sentences from a reference deck into examples

## Visual check

After a live apply, open `https://docs.google.com/presentation/d/<id>/edit` and look at every slide (plugin thumbnail or Drive export PDF). Confirm the title slide is Ballpoint/blue (not Keyboard cream) with Paper type, the bumper is Ink, Ink on Paper elsewhere, a visible gold/teal section rail, footer at the 0.50 in inset, Archivo (not a serif fallback), smile on title and bumper only, and no leftover master prompts. On the table slide, check Water Cooler headers, Keyboard / Business Card rows, and a closed Desk rule. Chart month labels should sit under their bar pair.
