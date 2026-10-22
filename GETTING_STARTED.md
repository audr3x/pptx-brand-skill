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

A venv is required. Managed Python (PEP 668) blocks `pip install` on the system interpreter.

```bash
# Debian / Ubuntu, if `python3 -m venv` errors:
# sudo apt-get update && sudo apt-get install -y python3.12-venv python3-pip

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

If you cannot create a venv and pip says `externally-managed-environment`, the fallback is `pip3 install --break-system-packages -r requirements.txt`. Prefer the venv.

Open the `pptx-brand-skill` folder as the Cursor project. The skills live in `.cursor/skills/workday-pptx` and `.cursor/skills/workday-google-slides`. Cursor loads them from that folder. Restart Cursor or reopen the folder if a skill does not appear.

## Use it for PowerPoint

1. **Open the repo.** In Cursor, choose **File > Open Folder** and pick the `pptx-brand-skill` folder you cloned. Run the install steps above once.
2. **Pick a model.** Open a chat (Cmd+L on Mac, Ctrl+L on Windows) and pick a model in the model menu under the message box. Claude Opus 5.5 and Gemini 3.8 Flash scored best in our tests (`evals/FINDINGS.md`).
3. **Ask for the deck.** Name the skill, give every fact you want on the slides, and say where to save it. Example:

   > Use the workday-pptx skill. Build a 5 slide deck for the Contoso payroll kickoff on May 12, 2027: cover, goals (cut payroll errors by half, one pay calendar for all 6 countries), a timeline table (Design in June, Build in July to September, Go-live in October), risks (two countries still on paper timesheets), and a closing slide. Save my request to decks/contoso-kickoff-notes.md, the outline to decks/contoso-kickoff.yaml, and the deck to out/contoso-kickoff.pptx. Use only my facts and write TODO for anything missing.

4. **Find the deck.** It lands where you asked, here `out/contoso-kickoff.pptx`. If you do not name a path, the skill writes `out/deck.pptx` (outline in `out/outline.yaml`).
5. **Open it.** Right-click the file in the Cursor file list and choose **Reveal in Finder** (Mac) or **Reveal in File Explorer** (Windows), then double-click it to open in PowerPoint. Archivo must be installed for the type to match.
6. **Check the readback.** The agent should run `python3 scripts/readback.py <outline> <deck>` after building and tell you the result. `ok: all N outline items are on the N slides` means every title, bullet, and table cell from the outline is on a slide. Any `missing:` line names the slide and text that did not make it. You can run it yourself:

   ```bash
   python3 scripts/readback.py decks/contoso-kickoff.yaml out/contoso-kickoff.pptx --show
   ```

   Also read the reply for every `TODO` left in the deck and any date or number it says was not in your request. Fill or remove those before you send the deck.

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

Start from the Workday template imported from `assets/template.pptx` (never a blank theme). The imported layouts keep the white smile lockup on the Title and Bumper layouts. They lose the cover gradient, so the builder adds it back as a picture, or falls back to a flat Ballpoint cover.

### First run: import the template (this file can be the deck)

Convert `assets/template.pptx` to Google Slides. That imported file has the Workday masters and layouts. On a clean import there are no leftover slides. You can build the first deck on this file. Copying it is optional. Copy later when you want a clean template and a separate deliverable.

How to convert:

- Drive UI: upload `assets/template.pptx`, then **File > Open** with Google Slides (or right-click, Open with, Google Slides).
- Drive plugin: upload the PPTX with `convertToGoogleFormat=true` so it becomes a presentation, not a binary PPTX sitting in Drive.
- `gws` / builder:

```bash
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws
```

Save the file ID as `WORKDAY_SLIDES_TEMPLATE_ID`. Do not commit it. Do not start from a blank Slides theme.

### One-time: the cover image (pick one option)

The only picture the builder adds is `cover-gradient.png`, full bleed behind the title slide. It does not add the smile, because the imported Title and Bumper layouts already have it (placing it again duplicates the logo). Use `--place-smile` only with a template that has no lockup.

The builder adds the cover with `createImage`. `createImage` fetches the picture from a URL **with no sign-in**, so the PNG must be readable by anyone on the internet. It is brand chrome (the cover wash), not deck copy.

| Option | Use it when | Title slide result |
| --- | --- | --- |
| A. Drive, Anyone with the link | Your Google Workspace allows "Anyone with the link" sharing | Real gradient, Ink type |
| B. Public URL | Your org only allows "Anyone in my org" sharing, but you can publish the PNG somewhere public | Real gradient, Ink type |
| C. No image | You cannot publish the PNG anywhere public | Flat Ballpoint, Paper (white) type. Add the gradient by hand if you want it |

All three keep the white smile from the layout. "Anyone in my org" is not enough for A. Slides fetches the image without your sign-in, so an org-only file looks private to it.

The builder never sends a placeholder such as `YOUR_COVER_IMAGE_ID` or `<cover URL>`. It ignores those, warns, and writes the no-image batch.

#### Option A: Drive, Anyone with the link

```bash
python3 scripts/build_slides.py --upload-assets --backend gws -o workday-slide-assets.json
```

The command uploads the PNGs and tries to share them. If your org blocks link sharing, it warns, keeps the file IDs, and points you to options B and C. It prints:

```text
export WORKDAY_COVER_IMAGE_ID="..."
export WORKDAY_SMILE_IMAGE_ID="..."
```

It also writes `workday-slide-assets.json` (gitignored). Keep that file on your machine. You only need the cover ID unless you use `--place-smile`.

Drive plugin (no `gws`):

1. Upload `assets/logos/cover-gradient.png` as a PNG.
2. In the Drive UI, share it as **Anyone with the link: Viewer**. The Cursor Google Drive connector cannot create that share. If the Drive UI only offers your org, use option B or C.
3. Save the file ID as `WORKDAY_COVER_IMAGE_ID`, or put it in `workday-slide-assets.json`.

#### Option B: host the cover PNG at a public URL

Put **only** brand PNGs somewhere public: `cover-gradient.png` (and `workday-smile.png` if you want it on hand). Do not make this repository public. Good hosts:

- A separate, small **public** GitHub repository that holds just the PNGs (for example `your-org/workday-slide-assets`). The raw URL looks like `https://raw.githubusercontent.com/your-org/workday-slide-assets/main/cover-gradient.png`.
- Any public static host your company already uses (a public web bucket, a CDN, a public website folder).

Check with your brand team that the cover art may sit at a public address.

The URL must:

- Open in a private browser window with no sign-in.
- Return the PNG itself (not a web page or a sign-in page). `curl -I <url>` should show `200` and `content-type: image/png`.
- Use `https://`.

Then pass it to phase 2 (or set `WORKDAY_COVER_IMAGE_URL`):

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --cover-image-url "https://raw.githubusercontent.com/your-org/workday-slide-assets/main/cover-gradient.png" \
  --chunk 40 \
  -o fills.json
```

When is a GitHub raw URL OK? Only when the repository it points at is **public**. This skill repository is private, so its raw URLs return 404 to Google Slides. The builder fetches each image URL once, with no sign-in, before it writes the batch:

- Public URL (200, an image): used as given. A URL you pass wins over a Drive ID.
- GitHub raw URL that answers 401, 403, or 404 (a private repo): dropped with a warning. The builder falls back to the Drive ID if you gave one, otherwise to the flat cover.
- Any other non-200 answer, or a web page instead of an image: the builder uses the Drive ID if you gave one. Otherwise it keeps the URL with a warning. Fix the URL before you send the batch.
- No network on your machine: kept, with a warning. Add `--skip-url-check` to skip the fetch on purpose.

#### Option C: no image, then add the gradient by hand

Run phase 2 with no image options (no `--cover-image-id` or `--cover-image-url`, and no `WORKDAY_COVER_IMAGE_ID` or `WORKDAY_COVER_IMAGE_URL` set):

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --chunk 40 \
  -o fills.json
```

The batch has no `createImage`. The title slide gets a flat Ballpoint background with Paper (white) title, subtitle, and date, and the white smile from the layout. The closing slide gets an Ink background, the smile from the layout, and the caption. This is also what the checked-in example in `docs/proof/slides/` does (the same files are in `docs/proof/slides/noimage/`).

To add the real gradient afterwards, in Google Slides (Insert > Image > Drive works with private files, because you are signed in):

1. On the title slide, Insert > Image > Drive, pick `cover-gradient.png`.
2. Open Format options > Size and rotation. Clear "Lock aspect ratio". Set width 10 in and height 5.625 in (25.4 x 14.29 cm). Under Position set X 0 and Y 0 from the top left.
3. Arrange > Order > Send to back. The smile and the text stay on top.
4. Switch the cover text to Ink. White type does not read on the light part of the gradient. Click the title, then Text color > Custom, enter `0F2E66`. Do the same for the subtitle and the date.

Only if your template has no smile (you did not start from the imported Workday template), insert `workday-smile.png` the same way:

- Title slide: size 1.343 x 0.635 in (3.41 x 1.61 cm), position X 0.669 in, Y 0.515 in (1.70 cm, 1.31 cm).
- Closing slide: size 3.216 x 1.521 in (8.17 x 3.86 cm), position X 3.392 in, Y 1.793 in (8.62 cm, 4.55 cm).

Do not add it to the imported template. That gives you two logos.

### From Cursor chat

Connect the Google Drive and Google Slides plugins first. Example:

> Use the workday-google-slides skill. I have Drive and Slides connected. I imported assets/template.pptx (convertToGoogleFormat). Build examples/outline.yaml on that file. Follow GETTING_STARTED.md: two-phase creates then fills, chunked at 40. For the cover use image option B with this public URL: <cover URL>.

If you have no public URL, say "use image option C (no image)" instead. More prompts are in [docs/PROMPTING.md](docs/PROMPTING.md).

### Two-phase flow (plugins or `gws`)

Phase 1 creates slides. Phase 2 fills them. `update_presentation` takes the `requests` array only. Do not send the wrapper keys (`phase`, `note`, `chrome`).

With the Google Slides plugin in Cursor, put the `requests` array **inline** in the `update_presentation` call. Do not pass a file path or attach the JSON file. A file reference reaches the plugin as a plain string, not an array, and the call fails. That is why the builder writes chunks of about 40 requests: each one is small enough to paste inline.

**Phase 1, write create requests**

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json \
  -o out/slides/creates.json
```

`get.json` is `read_presentation` / `presentations.get` on the imported file (or a copy). That replaces each `layoutName` with the real `layoutId`. If `creates.json` still has `layoutName`, match it to `layouts[].layoutProperties.displayName` (strip spaces, ignore case) and put `layoutId` in `slideLayoutReference` before you send the batch.

Send only the `requests` array to `update_presentation` on that file. Keep the planned slide IDs (`wd_s1`, `wd_s2`, ...).

A clean PPTX import has no leftover slides. There is nothing to delete. Only delete leftover slides if you started from a finished deck that already had pages.

**Phase 2, write fill requests**

Save a fresh `read_presentation` after the create batch as `get.json`, then:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --chunk 40 \
  -o out/slides/fills.json
```

`--chunk 40` writes `fills.json` plus ordered paste files `fills-01.json`, `fills-02.json`, and so on (about 40 requests each). Send those chunks **in order**. Each call to `update_presentation` gets that file's `requests` array only.

That example uses option A (Drive ID). For option B use `--cover-image-url` instead. For option C leave the image option out. See the image options above.

### Live apply in one step (`gws` or API)

```bash
export WORKDAY_SLIDES_TEMPLATE_ID=...
export WORKDAY_COVER_IMAGE_ID=...   # or WORKDAY_COVER_IMAGE_URL=https://..., or neither for option C
python3 scripts/build_slides.py examples/outline.yaml \
  --template-id "$WORKDAY_SLIDES_TEMPLATE_ID" \
  --backend gws
```

`--template-id` copies that file, then fills the copy. On a first run, pass `--import-pptx assets/template.pptx` instead of `--template-id`. The builder then fills the imported file and does not copy it.

### Where Slides output lands

| File | What it is |
| --- | --- |
| `docs/proof/slides/creates.json` | Phase 1 `createSlide` requests |
| `docs/proof/slides/fills.json` | Full phase 2 batch (no image, option C) |
| `docs/proof/slides/fills-01.json` and up | Phase 2 split for `update_presentation` (send in order) |
| `docs/proof/slides/noimage/` | The same no-image batch, kept as the option C reference |
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

Check an outline before you build. It reports fields the builders ignore and limits per target:

```bash
python3 scripts/check_outline.py my-outline.yaml
```

How to ask Cursor for a deck, with copy-paste prompts: [docs/PROMPTING.md](docs/PROMPTING.md).

## Troubleshooting

**A skill does not run.** Open this repository as the Cursor project folder. Reopen the folder after a clone. Ask for the skill by name (`workday-pptx` or `workday-google-slides`).

**`ensurepip is not available` / venv fails.** On Debian or Ubuntu: `sudo apt-get install -y python3.12-venv python3-pip`. Recreate `.venv`.

**`externally-managed-environment` (PEP 668).** Do not pip-install into the system Python. Use the venv. Fallback only: `pip3 install --break-system-packages -r requirements.txt`.

**`PyYAML is required`.** Activate the venv and run `pip install -r requirements.txt`.

**Cover is cream or flat blue.** Cream means the layout picture dropped and no page fill ran. Flat blue with white type is the no-image result (option C). For the gradient, use option A or B and re-run phase 2, or insert `cover-gradient.png` by hand (option C steps).

**Title text is white on the gold part of the cover, or navy on flat blue.** Navy (Ink) is correct on the gradient. White (Paper) is correct only on the Ballpoint fallback. After a manual cover insert, set title, subtitle, and date to `0F2E66`.

**My org only allows "Anyone in my org" sharing.** Slides cannot fetch an org-only Drive file. Use option B (a public URL for the cover PNG) or option C (no image, insert by hand).

**Two Workday logos on the title or closing slide.** The imported template already has the smile. Do not pass `--place-smile`, and do not insert the smile by hand on that template.

**`warning: ignoring placeholder image value`.** You passed a doc placeholder such as `YOUR_COVER_IMAGE_ID`. Pass a real Drive file ID or public URL, or leave the option out.

**`deleteText` errors.** Empty placeholders cannot take `deleteText ALL`. The builder skips that when the shape has no text. Do not add `deleteText` by hand on a new shape.

**`CENTER_TITLE` errors.** The Slides API name is `CENTERED_TITLE`. Use the JSON this repo writes.

**`Archivo Light` looks like a serif.** Google Slides does not have that family name. The builder sends `Archivo` plus `weightedFontFamily.weight` 300. Enable Archivo from Google Fonts in the theme if you can.

**`createImage` fails.** Slides could not fetch the cover with no sign-in. Open the URL in a private window: `https://drive.google.com/uc?export=download&id=FILE_ID` for option A, or your public URL for option B. A sign-in page means it is not public. A GitHub raw URL from this repo will 404 (the builder drops those). If you cannot make it public, use option C.

**`update_presentation` rejects the batch, or says `requests` is a string.** Send the `requests` array inline, not the whole JSON and not a file reference (a file arrives as a string and fails). Use `--chunk 40` and send `fills-01.json`, `fills-02.json`, ... in order.

**The Slides chart is not an editable chart.** The builder draws columns, the value axis, tick labels, and gridlines as shapes, so it needs no Google Sheets link. Every chart type is drawn as clustered columns. To change the numbers, edit the outline and run phase 2 again on a fresh copy. Use PowerPoint for a native bar, line, or pie chart.

**Bullet dots look bigger than in PowerPoint.** In Google Slides the dot takes the size of the text, and the Slides API has no setting to change that. The builder only sets the spacing: 6 pt before and after each bullet, with list spacing set so Slides does not collapse it. To make the dots smaller, do it by hand after the fill: click one bullet dot (Slides selects every dot in that list) and lower the font size in the toolbar, or pick a smaller bullet style in Format > Bullets and numbering.

**Bullets are packed tightly together.** The fill batch is from an older build. Rebuild the fills with the current `build_slides.py` and send them again. Each bulleted box now gets an `updateParagraphStyle` request with `spacingMode` set to `NEVER_COLLAPSE`.

**Layout not found.** Import `assets/template.pptx` again. Do not start from a blank Slides theme. Match layout names after stripping spaces (`Title and Content` has a trailing space in the PPTX).

**Footer sits on the left edge.** The builder draws the footer at x = 0.50 in, and at x = 3.32 in on section slides so it clears the gold rail. Do not reuse a footer placeholder object ID for a new text box.

**Fonts look like Arial in LibreOffice.** Install Archivo on that machine and render again. The Office theme fallback is Arial.

**LibreOffice PNGs drop spaces** (`Planningworkshop`). The `.pptx` still has normal spaces. Open it in PowerPoint. LibreOffice often collapses spaces when it substitutes Archivo.

**`javaldx` / Java warning from `soffice`.** Harmless. The PDF and PNGs still write.

**`git clone` has no `GETTING_STARTED.md`.** The default branch may still be an older commit. Check out the branch your team is using for this skill.

**You edited the template file in Drive.** Make a new copy from the imported PPTX and set `WORKDAY_SLIDES_TEMPLATE_ID` to the unused template, not a finished deck.
