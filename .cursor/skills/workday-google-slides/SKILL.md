---
name: workday-google-slides
description: Generate on-brand Workday Google Slides decks from a brief or outline. Use when asked for a Workday presentation in Google Slides, a branded Workspace deck, or to import assets/template.pptx into Slides. Copies a Workday template (never a blank theme), fills layouts through the Slides API or gws, and follows BRAND.md.
---

# Workday Google Slides

Same brand system as [workday-pptx](../workday-pptx/SKILL.md), on Google Slides. Team setup is in [GETTING_STARTED.md](../../../GETTING_STARTED.md). Read [BRAND.md](../../../BRAND.md) first. Do not invent colors, fonts, or chrome.

Workday has no canonical public Slides ID in this repo. Import [assets/template.pptx](../../../assets/template.pptx) once (Drive upload with `convertToGoogleFormat=true`, or File > Open with Google Slides), or use a template deck ID the user hands you. On a first run you may fill that imported file. Copying it is optional. Later decks should copy the unused template.

```
Workday Slides compliance:
- [ ] Read this skill and BRAND.md
- [ ] First run may fill the imported PPTX. Later decks copy the unused template. Never start from a blank theme
- [ ] Layout picked by intent (no blank slide when a Workday layout exists)
- [ ] Tokens only (core palette first). Archivo, Arial fallback
- [ ] Footer is Workday Confidential. About 6 bullets max
- [ ] Re-read the deck and check styles before calling it done
```

Writing the deck content or prompt? See [docs/PROMPTING.md](../../../docs/PROMPTING.md) and the [workday-deck-prompting](../workday-deck-prompting/SKILL.md) skill. Check outlines with `python3 scripts/check_outline.py <outline>`.

## Auth (pick one). Never commit credentials

### A. Cursor Google plugins

Install and sign in to the **Google Drive** and **Google Slides** plugins with the Workday Google account. Then:

1. Drive: upload `assets/template.pptx` with `convertToGoogleFormat=true` (or File > Open in the Drive UI). First run: this file is the deck. Copy only if you want a spare template.
2. Cover image, pick one (see "Seed the cover image" below): A, a Drive PNG shared Anyone with the link; B, a public URL; C, no image. Ask the user which one their org allows. Never place the smile on the imported template; its layouts already carry it.
3. Slides `read_presentation` / `update_presentation` on that file. `update_presentation` takes the `requests` array only, **inline** in the call. A file path or attached file arrives as a string and fails. Send fill chunks (about 40 requests) in order.
4. `read_presentation` again to verify

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

# One-time, option A: upload the PNGs and try Anyone-with-link sharing
python3 scripts/build_slides.py --upload-assets --backend gws
# writes workday-slide-assets.json and prints export WORKDAY_COVER_IMAGE_ID=...

# Two-phase connector (Drive/Slides plugins, no gws):
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json -o creates.json
# send creates.json requests via update_presentation, then save read_presentation to get.json
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --chunk 40 \
  -o fills.json
# option B: --cover-image-url https://<public host>/cover-gradient.png instead of the ID
# option C: no image option at all (flat Ballpoint cover, Paper type)
# send fills-01.json, fills-02.json, ... in order, requests array inline

# Live apply, after auth:
python3 scripts/build_slides.py examples/outline.yaml \
  --template-id "$WORKDAY_SLIDES_TEMPLATE_ID" \
  --backend gws
# or --backend api   (ADC / GOOGLE_APPLICATION_CREDENTIALS)
```

`--import-pptx assets/template.pptx` uploads the PPTX and converts it to a Google Slides file (first-time only). On that first run you may fill the imported file. Copying is optional. Save the ID as `WORKDAY_SLIDES_TEMPLATE_ID` for later copies.

`--upload-assets` uploads [cover-gradient.png](../../../assets/logos/cover-gradient.png) and [workday-smile.png](../../../assets/logos/workday-smile.png) and tries to share them. If org policy blocks link sharing it keeps the IDs and points to options B and C. Only the cover ID is used unless `--place-smile` is set.

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

In the Drive UI: upload `assets/template.pptx`, then File > Open with Google Slides. Drive plugin: upload with `convertToGoogleFormat=true`. That conversion keeps the Workday master and the 15 layouts. A clean import has no leftover slides.

If the user already has a branded Slides file, use that ID. Do not start from `presentations.create` (blank theme) unless import failed and they said so.

## Seed the cover image (one time)

Slides drops the Title Slide Day Crop gradient on import. The imported Title and Bumper layouts **keep** the white smile, so the builder does not place it (that would give two logos). `--place-smile` exists only for a template without the lockup.

`createImage` fetches the cover with no sign-in. Pick the option the user's org allows:

- **A. Drive, Anyone with the link.** Upload `cover-gradient.png`, share it in the **Drive UI** as Anyone with the link: Viewer (the Drive connector cannot create that share), pass `--cover-image-id`. "Anyone in my org" is not enough.
- **B. Public URL.** Host `cover-gradient.png` in a separate small **public** GitHub repo or any public static host (never make this repo public). Pass `--cover-image-url` or set `WORKDAY_COVER_IMAGE_URL`. The builder fetches the URL once with no sign-in: a public image is used as given and wins over a Drive ID; a GitHub raw URL answering 401/403/404 (private repo, including this one) is dropped with a warning; other failures warn. `--skip-url-check` skips the fetch.
- **C. No image.** Pass no image option. Title slide is flat Ballpoint with Paper title, subtitle, and date; the layout smile stays. The user can add the gradient by hand: Insert > Image > Drive (private files work), 10 x 5.625 in at 0, 0, Arrange > Order > Send to back, then set title, subtitle, and date to Ink `0F2E66`.

The builder ignores placeholder values such as `YOUR_COVER_IMAGE_ID` or `<cover URL>`, so default fills never contain a broken `createImage`.

```bash
# regenerate the 16:9 PNG from the PPTX SVG if needed
python3 scripts/export_cover_assets.py
```

Do not commit Drive IDs or `workday-slide-assets.json`.

## Create a deck

1. First run: use the imported file. Later: copy the unused template. Never start from a blank theme.

```bash
gws drive files copy \
  --params '{"fileId": "<TEMPLATE_ID>"}' \
  --json '{"name": "<Deliverable title>"}'
```

Drive plugin: `copy_file` with that `fileId` and the deliverable title.

2. `presentations.get` the copy. Map layout **display names** (strip whitespace, case-insensitive) to `layoutId`.

3. For each outline slide, `createSlide` with `slideLayoutReference.layoutId` (the Workday layout). Prefer this over `predefinedLayout` and over `importSlides` from a blank deck. Title placeholders come back as **`CENTERED_TITLE`**, not `CENTER_TITLE`.

4. Two-phase fill. Phase 1 is only `createSlide`. Then `read_presentation` / `presentations.get`. Phase 2 binds fills (`--phase fills --presentation get.json --chunk 40`). Send `fills-01.json`, `fills-02.json`, ... in order. `update_presentation` takes the `requests` array only.

5. Fill placeholders with `insertText` + `updateTextStyle`. Send `deleteText` **only** when the shape already has text. Empty new placeholders error on `deleteText ALL`.

6. Draw missing chrome. Title Slide: Ballpoint `pageBackgroundFill`, then `createImage` of the cover full-bleed and send to back when a real cover ID or public URL is set. The smile comes from the layout. Bumper: Ink fill; the smile comes from the layout. Section rail (2.743 in Tack / Keyboard / Lunch Break stack), half-headline items, footer box at **x = 0.50 in** (x = 3.32 in on Section Title, right of the rail), cover date, bumper caption. Cover title is bold (700). Cover type is **Ink** on the gradient, **Paper** only on the flat Ballpoint fallback.

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
| Chart | `chart` | Title Only | `title` + on-brand clustered columns with a value axis (all `chart.type` values draw as columns) |
| Closing | `closing` | Bumper Slide | optional caption under the smile |
| Intro | `intro` | Intro_One | `name`, `role`, `company` |
| Blank | `blank` | Blank White Background | last resort |

Content layout XML name is `Title and Content ` (trailing space). Match after strip.

If a Workday `layoutId` is missing (import dropped it), stop and re-import. Do not silently switch to `TITLE_AND_BODY` except as a last-resort fallback the user approved.

## Brand rules

- **Colors.** Only tokens in `BRAND.md` / `assets/brand-tokens.json`. Prefer theme slots on the copied deck (`dk1` = Ink, `accent1` = Water Cooler) when they still match. Otherwise RGB from the token file. If a hex is not in that file, do not use it.
- **Type.** `fontFamily` is always **Archivo**. Body uses `weightedFontFamily: {fontFamily: "Archivo", weight: 300}` (do not send `Archivo Light`, Google falls back to a serif). Titles use weight 400, or 700 when bold. Include `weightedFontFamily` in `fields`. Enable Archivo from Google Fonts if you can. Arial is the last-resort fallback. Never switch to Calibri, Inter, Roboto, or Proxima Nova.
- **Sizes.** Cover 36 pt. Slide / section title 28 pt bold Ink. Body 18 to 20 pt. Footer 8 pt Staple `#7D8B99` at **x = 0.50 in**; on Section Title it is Ink at x = 3.32 in, clear of the rail.
- **Title Slide.** `createImage` the cover full-bleed (`10.00 x 5.625 in`) and send it to the back when option A or B is set. Title (bold 700), subtitle, and date are **Ink** (`#0F2E66`) on that gradient, matching the PPTX. With no image (option C), keep Ballpoint `pageBackgroundFill` and those three runs Paper.
- **Bumper Slide.** Ink `pageBackgroundFill`. The smile comes from the layout. Paper caption under the mark.
- **Bullets.** At most about 6. `createParagraphBullets` `BULLET_DISC_CIRCLE_SQUARE`, 6 pt `spaceAbove` and `spaceBelow` (the PPTX spacing). The API has no bullet-size field, so the builder styles the whole box at 14 pt and the words back at 20 pt, leaving the paragraph-end newline (which Slides uses for the dot) smaller. Do not type `•` into the run.
- **Footer.** `Workday Confidential`. No slide numbers.
- **Logo.** White lockup from the imported Title and Bumper layouts. Do not add a second one. Do not recolor it or drop it on Paper.
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

Images: `createImage` needs a URL Slides can fetch with no sign-in: a Drive file shared Anyone with the link (option A, shown below) or a public URL (option B). Never a raw URL from a private repo.

```json
{
  "createImage": {
    "objectId": "wd_s1_cover",
    "url": "https://drive.google.com/uc?export=download&id=<WORKDAY_COVER_IMAGE_ID>",
    "elementProperties": {
      "pageObjectId": "wd_s1",
      "size": {
        "width": { "magnitude": 9144000, "unit": "EMU" },
        "height": { "magnitude": 5143500, "unit": "EMU" }
      },
      "transform": { "scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU" }
    }
  }
}
```

Then `updatePageElementsZOrder` `SEND_TO_BACK` on `wd_s1_cover`. Do not skip this when a cover image is set. The layout gradient does not survive the import.

Charts: the builder draws Water Cooler / Lunch Break columns, a Desk value axis, tick labels on a rounded scale, and Desk gridlines behind the columns, all as shapes, so a deck does not depend on Sheets. Bar, line, and pie draw as columns in Slides. The chart is not editable as data; change the outline and re-run. For a live data chart, create a Sheets chart with those series colors and `createSheetsChart` / `refreshSheetsChart`.

## Do not

- Do not `batchUpdate` a template you want to keep unused. First run may fill the imported PPTX.
- Do not mix blank untemplated slides into a branded deck
- Do not send placeholder type `CENTER_TITLE` (it is `CENTERED_TITLE`)
- Do not send `fontFamily: "Archivo Light"`
- Do not `deleteText` on an empty placeholder
- Do not reuse a footer placeholder id for a new text box
- Do not assume the cover gradient copied. Insert it (option A or B) or leave the Ballpoint fallback (option C). Do not insert the smile on the imported template
- Do not send placeholder image IDs, or a file reference instead of an inline `requests` array
- Do not use Paper type on the cover when the gradient image is present (Ink, like the PPTX)
- Do not use Inter, Cursor orange, GTM LIGHT2 tiles, or any other company's tokens
- Do not commit `credentials.json`, `client_secret.json`, `.env`, or `gws` token files
- Do not copy confidential sentences from a reference deck into examples

## Visual check

After a live apply, open `https://docs.google.com/presentation/d/<id>/edit` and look at every slide (plugin thumbnail or Drive export PDF). With a cover image, confirm the blue to cream to gold Day Crop, bold navy Ink title, Ink subtitle and date. With no image, confirm flat Ballpoint with bold Paper title, Paper subtitle and date. Either way there is exactly one white lockup top left. Confirm the bumper is Ink with one centered smile. Then check Ink on Paper elsewhere, a visible gold/teal section rail, footer at the 0.50 in inset (3.32 in on the section slide, clear of the rail), Archivo (not a serif fallback), and no leftover master prompts. On the table slide, check Water Cooler headers, Keyboard / Business Card rows, and a closed Desk rule. Chart month labels should sit under their bar pair, with tick numbers on the left and light gridlines behind the bars.
