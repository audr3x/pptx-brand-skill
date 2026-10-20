# Workday brand skills (PowerPoint and Google Slides)

Reusable Cursor skills that build on-brand decks from the Workday Corporate Template. PowerPoint is the native surface. Google Slides is the same brand system after you import `assets/template.pptx` once (or pass a template deck ID).

This repository is the brand system plus two small builders. It is not a dump of a real presentation. Sample copy in `examples/` is generic placeholder text.

| Path | What it is |
| --- | --- |
| [BRAND.md](BRAND.md) | Colors, type, layouts, footer, table and chart rules |
| [assets/template.pptx](assets/template.pptx) | Masters and layouts only, no sample slides |
| [assets/logos/](assets/logos) | Smile mark, `cover-gradient.png`, and decorative SVGs |
| [assets/brand-tokens.json](assets/brand-tokens.json) | Machine-readable tokens |
| [.cursor/skills/workday-pptx/SKILL.md](.cursor/skills/workday-pptx/SKILL.md) | How Cursor builds a `.pptx` |
| [.cursor/skills/workday-google-slides/SKILL.md](.cursor/skills/workday-google-slides/SKILL.md) | How Cursor builds a Google Slides deck |
| [scripts/build_deck.py](scripts/build_deck.py) | Outline to `.pptx` |
| [scripts/build_slides.py](scripts/build_slides.py) | Outline to Slides API / `gws` (or a dry-run request plan) |
| [examples/outline.yaml](examples/outline.yaml) | Shared example outline |
| [examples/example-deck.pptx](examples/example-deck.pptx) | Example PowerPoint from that outline |
| [examples/example-slides-requests.json](examples/example-slides-requests.json) | Example Slides `batchUpdate` plan from the same outline |

## Install the skills in Cursor

The skills are the folders under `.cursor/skills/`. Cursor loads project skills from `.cursor/skills/` and personal skills from `~/.cursor/skills/`.

### Project skill (recommended for Workday repos)

Copy this repository's `.cursor/skills` directory into the repo that should produce decks, and keep `BRAND.md`, `assets/`, and `scripts/` beside it so the relative paths in the skill resolve.

```bash
cp -R .cursor/skills/workday-pptx <your-repo>/.cursor/skills/workday-pptx
cp -R .cursor/skills/workday-google-slides <your-repo>/.cursor/skills/workday-google-slides
cp -R BRAND.md assets scripts examples <your-repo>/
```

Or add this repository as a subtree / submodule and point the skill paths at it.

### Personal skill

```bash
mkdir -p ~/.cursor/skills
cp -R .cursor/skills/workday-pptx ~/.cursor/skills/workday-pptx
cp -R .cursor/skills/workday-google-slides ~/.cursor/skills/workday-google-slides
```

A personal copy still needs the template and `BRAND.md`. Keep the rest of this repo on disk and either leave the relative links as-is (if you cloned the whole repo into `~/.cursor/skills/workday-pptx-repo`) or edit the skills to use absolute paths to `BRAND.md` and `assets/template.pptx`.

After a copy, restart Cursor or reopen the folder so the skills are indexed. Ask Cursor to "make a Workday deck", "use the workday-pptx skill", or "make this as Google Slides".

## Use the builder directly

```bash
pip3 install -r requirements.txt
python3 scripts/build_deck.py examples/outline.yaml -o examples/example-deck.pptx
```

The outline can be YAML or JSON. Each slide names a `layout` from the intent map in the skill (`title`, `section`, `content`, `two-column`, `table`, `chart`, `closing`, and a few extras).

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

The builder opens `assets/template.pptx`, adds slides from the real Workday layouts, and paints tables and charts with the named tokens. It refuses unknown hex colors.

## Use the Google Slides builder

Same outline. Copy a Workday Slides template (never a blank theme), then fill layouts through `gws` or the Slides API.

```bash
# No Google account required. Writes the batchUpdate plan (includes slidePlans):
python3 scripts/build_slides.py examples/outline.yaml --dry-run \
  -o examples/example-slides-requests.json

# One-time: upload cover-gradient.png and the smile lockup
python3 scripts/build_slides.py --upload-assets --backend gws
export WORKDAY_COVER_IMAGE_ID=...   # printed; also written to workday-slide-assets.json
export WORKDAY_SMILE_IMAGE_ID=...

# Two-phase connector for the Slides plugin:
python3 scripts/build_slides.py examples/outline.yaml --phase creates -o creates.json
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --smile-image-id "$WORKDAY_SMILE_IMAGE_ID" \
  -o fills.json

# First time: import the PPTX so Workday masters exist in Drive
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws

# Later decks: copy that template ID
export WORKDAY_SLIDES_TEMPLATE_ID=...   # not committed
python3 scripts/build_slides.py examples/outline.yaml \
  --template-id "$WORKDAY_SLIDES_TEMPLATE_ID" --backend gws
```

Auth options (never commit the files):

1. Cursor **Google Drive** + **Google Slides** plugins, signed in as the Workday user. The skill then uses `copy_file` and `update_presentation`.
2. [Google Workspace CLI](https://github.com/googleworkspace/cli): `gws auth setup` then `gws auth login -s drive,slides`.
3. `--backend api` with Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS` pointing outside the repo.

Details, layout map, and `batchUpdate` recipes are in the [Google Slides skill](.cursor/skills/workday-google-slides/SKILL.md).

## Fonts

Designed type is **Archivo** and **Archivo Light**. The Office theme fallback is Arial. Archivo is not embedded in the template. Install it from [Google Fonts](https://fonts.google.com/specimen/Archivo) on any machine that will author or render decks. If Archivo Light is missing, use Archivo. Do not substitute Proxima Nova (licensed, not bundled) or Calibri.

## Rules of the road

- Start from `assets/template.pptx` (PowerPoint) or a copy of the imported Slides template. Do not build a Workday deck from a blank theme.
- Use only colors in `BRAND.md`.
- Leave `Workday Confidential` in the footer placeholder.
- Do not put confidential customer copy into this repo.
- Do not commit Google credentials, `gws` tokens, or `.env` files.
