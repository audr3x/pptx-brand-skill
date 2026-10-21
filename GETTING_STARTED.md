# Getting started

This repository builds on-brand Workday decks in PowerPoint and Google Slides. Both skills use the same template, colors, and type. Sample copy in `examples/` is generic placeholder text. Do not put customer or confidential sentences into this repo.

Read this file first. Then use [BRAND.md](BRAND.md) if you need a color, layout, or spacing rule.

## What you need

- [Cursor](https://cursor.com) (the desktop app)
- Git
- Python 3.10 or newer (`python3-venv` and `python3-pip` on Debian or Ubuntu)
- The [Archivo](https://fonts.google.com/specimen/Archivo) font family on your computer (Regular and Light). Arial is the fallback if Archivo is missing. Do not substitute Calibri, Inter, Roboto, or Proxima Nova.

Optional, for a visual check of a `.pptx`:

- LibreOffice (`soffice`)
- `pdftoppm` (Poppler)

For Google Slides, pick one:

- Cursor **Google Drive** and **Google Slides** plugins, signed in as your Workday user, or
- [Google Workspace CLI (`gws`)](https://github.com/googleworkspace/cli), or
- Application Default Credentials for `scripts/build_slides.py --backend api`

Never commit `credentials.json`, `client_secret.json`, `.env`, or `gws` token files.

## Clone and install

```bash
git clone https://github.com/audr3x/pptx-brand-skill.git
cd pptx-brand-skill
```

You should see `GETTING_STARTED.md`, `BRAND.md`, `assets/template.pptx`, and `.cursor/skills/`. If those files are missing, the default branch is older than this guide. Check out the branch your team is using, then continue.

```bash
# Debian / Ubuntu, if `python3 -m venv` errors:
# sudo apt-get update && sudo apt-get install -y python3.12-venv python3-pip

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Open the `pptx-brand-skill` folder as the Cursor project. The skills live in `.cursor/skills/workday-pptx` and `.cursor/skills/workday-google-slides`. Cursor loads them from that folder. Restart Cursor or reopen the folder if a skill does not appear.

## PowerPoint (`workday-pptx`)

The builder starts from `assets/template.pptx` (masters and layouts only) and fills slides from a YAML or JSON outline.

### From Cursor chat

Ask for a Workday PowerPoint and name the skill. Example:

> Use the workday-pptx skill. Build a planning workshop deck from examples/outline.yaml and write it to out/planning-workshop.pptx. Follow BRAND.md. Do not invent colors or fonts.

You can also paste a brief and ask it to write the outline first, then build.

### From the terminal

```bash
source .venv/bin/activate
python3 scripts/build_deck.py examples/outline.yaml -o out/planning-workshop.pptx
```

That writes `out/planning-workshop.pptx`. To overwrite the checked-in worked example:

```bash
python3 scripts/build_deck.py examples/outline.yaml -o docs/proof/planning-workshop.pptx
```

### Check it

Open the file in PowerPoint or Keynote. Confirm Ink titles, the cover gradient (blue to cream to gold) with navy type, the gold section rail, `Workday Confidential` in the footer, and the smile on the title and closing slides only.

If LibreOffice is installed:

```bash
# Debian / Ubuntu (once):
# sudo apt-get update && sudo apt-get install -y libreoffice-impress poppler-utils
# macOS (once): brew install --cask libreoffice && brew install poppler

mkdir -p docs/proof/pptx
soffice --headless --convert-to pdf --outdir docs/proof docs/proof/planning-workshop.pptx
pdftoppm -png -r 140 docs/proof/planning-workshop.pdf docs/proof/pptx/slide
```

PNGs land in `docs/proof/pptx/` as `slide-1.png`, `slide-2.png`, and so on.

## Google Slides (`workday-google-slides`)

Google Slides does not keep every layout picture when you add a new slide. You must copy a Workday template (never a blank theme), then fill it. The cover gradient and smile are PNGs you upload once.

### One-time: import the template

Upload `assets/template.pptx` to Drive and open it with Google Slides, or:

```bash
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws
```

Save the new file ID as `WORKDAY_SLIDES_TEMPLATE_ID`. Do not commit it. Every new deck is a **copy** of that file. Never run `batchUpdate` on the template itself.

Drive plugin: upload the PPTX, open with Google Slides, then use that file ID.

### One-time: upload the cover and smile images

`createImage` needs a URL Google Slides can fetch. The upload step shares each PNG as **anyone with the link, Viewer**. These files are brand chrome (the cover wash and the lockup), not deck copy.

```bash
python3 scripts/build_slides.py --upload-assets --backend gws -o workday-slide-assets.json
```

The command prints:

```text
export WORKDAY_COVER_IMAGE_ID="..."
export WORKDAY_SMILE_IMAGE_ID="..."
```

It also writes `workday-slide-assets.json` (gitignored). Keep that file on your machine.

Drive plugin (no `gws`):

1. Upload `assets/logos/cover-gradient.png` as a PNG.
2. Upload `assets/logos/workday-smile.png` as a PNG.
3. Share both as anyone with the link, Viewer.
4. Save the two file IDs, or put them in `workday-slide-assets.json` as `WORKDAY_COVER_IMAGE_ID` and `WORKDAY_SMILE_IMAGE_ID`.

If you skip this step, the title slide is flat Ballpoint blue with white type. After the IDs are set, the cover is the real blue-to-gold gradient with navy type, and the white lockup is placed on the title and closing slides.

### From Cursor chat

Connect the Google Drive and Google Slides plugins first. Example:

> Use the workday-google-slides skill. I have Drive and Slides connected. Copy the Workday template, then build examples/outline.yaml into a new deck. Follow GETTING_STARTED.md: two-phase creates then fills, and use WORKDAY_COVER_IMAGE_ID and WORKDAY_SMILE_IMAGE_ID for the cover.

### Two-phase flow (plugins or `gws`)

Phase 1 creates slides. Phase 2 fills them. Do not send both in one all-or-nothing batch if you are still learning the IDs.

**Phase 1, write create requests**

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  -o docs/proof/slides/creates.json
```

If you already have a `presentations.get` / `read_presentation` JSON from the **copied** deck (so layout IDs are known):

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json \
  -o docs/proof/slides/creates.json
```

That replaces each `layoutName` with the real `layoutId`. If `creates.json` still has `layoutName`, match it to `layouts[].layoutProperties.displayName` (strip spaces, ignore case) and put `layoutId` in `slideLayoutReference` before you send the batch.

Send only the `requests` array to `presentations.batchUpdate` / `update_presentation` on the **copy**. Keep the planned slide IDs (`wd_s1`, `wd_s2`, …). Delete leftover template slides first.

**Phase 2, write fill requests**

After the create batch, or using the planned `wd_sN` IDs:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --smile-image-id "$WORKDAY_SMILE_IMAGE_ID" \
  -o docs/proof/slides/fills.json
```

If Google assigned different object IDs, save `read_presentation` to `get.json` and bind them:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --assets-ids workday-slide-assets.json \
  -o docs/proof/slides/fills.json
```

Send the `requests` array in `fills.json` to the same copied deck.

Without image IDs, omit `--cover-image-id` and `--smile-image-id`. The fill batch still runs. The cover stays flat Ballpoint.

### Live apply in one step (`gws` or API)

```bash
export WORKDAY_SLIDES_TEMPLATE_ID=...
export WORKDAY_COVER_IMAGE_ID=...
export WORKDAY_SMILE_IMAGE_ID=...
python3 scripts/build_slides.py examples/outline.yaml \
  --template-id "$WORKDAY_SLIDES_TEMPLATE_ID" \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --smile-image-id "$WORKDAY_SMILE_IMAGE_ID" \
  --backend gws
```

The command copies the template, creates slides, fills them, and prints the deck URL.

### Where Slides output lands

| File | What it is |
| --- | --- |
| `docs/proof/slides/creates.json` | Phase 1 `createSlide` requests |
| `docs/proof/slides/fills.json` | Phase 2 text, shapes, tables, charts, images |
| `docs/proof/slides/STEPS.md` | Click-by-click plugin steps for the worked example |
| `workday-slide-assets.json` | Your Drive image IDs (local only) |
| Google Slides URL | Printed after a live `--backend` run |

## Outline

Both builders read the same outline. [examples/outline.yaml](examples/outline.yaml) is the shared example.

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

`layout` values: `title`, `section`, `content`, `two-column`, `table`, `chart`, `closing`, plus `intro`, `photo-right`, and `blank`. Details are in the skill files and `BRAND.md`.

## Troubleshooting

**A skill does not run.** Open this repository as the Cursor project folder. Reopen the folder after a clone. Ask for the skill by name (`workday-pptx` or `workday-google-slides`).

**`ensurepip is not available` / venv fails.** On Debian or Ubuntu: `sudo apt-get install -y python3.12-venv python3-pip`. Recreate `.venv`. Or skip the venv and run `pip3 install --user -r requirements.txt`.

**`PyYAML is required`.** Activate the venv and run `pip install -r requirements.txt`.

**Cover is cream or flat blue.** Cream means the layout picture dropped and no page fill ran. Flat blue means fills ran without `WORKDAY_COVER_IMAGE_ID`. Upload the PNGs, share them anyone-with-link Viewer, and re-run phase 2 with the IDs.

**Title text is white on the gold part of the cover, or navy on flat blue.** Navy (Ink) is correct on the gradient. White (Paper) is correct only on the Ballpoint fallback. Pass the cover image ID so the builder picks Ink.

**`deleteText` errors.** Empty placeholders cannot take `deleteText ALL`. The builder skips that when the shape has no text. Do not add `deleteText` by hand on a new shape.

**`CENTER_TITLE` errors.** The Slides API name is `CENTERED_TITLE`. Use the JSON this repo writes.

**`Archivo Light` looks like a serif.** Google Slides does not have that family name. The builder sends `Archivo` plus `weightedFontFamily.weight` 300. Enable Archivo from Google Fonts in the theme if you can.

**`createImage` fails.** The Drive file must be anyone with the link, Viewer. Confirm the ID. Try the URL `https://drive.google.com/uc?export=download&id=FILE_ID` in a private window.

**Layout not found.** Import `assets/template.pptx` again. Do not start from a blank Slides theme. Match layout names after stripping spaces (`Title and Content` has a trailing space in the PPTX).

**Footer sits on the left edge.** The builder draws the footer at x = 0.50 in. Do not reuse a footer placeholder object ID for a new text box.

**Fonts look like Arial in LibreOffice.** Install Archivo on that machine and render again. The Office theme fallback is Arial.

**LibreOffice PNGs drop spaces** (`Planningworkshop`). The `.pptx` still has normal spaces. Open it in PowerPoint. LibreOffice often collapses spaces when it substitutes Archivo.

**`javaldx` / Java warning from `soffice`.** Harmless. The PDF and PNGs still write.

**`git clone` has no `GETTING_STARTED.md`.** The default branch may still be an older commit. Check out the branch your team is using for this skill.

**You edited the template file in Drive.** Make a new copy from the imported PPTX and set `WORKDAY_SLIDES_TEMPLATE_ID` to the unused template, not a finished deck.
