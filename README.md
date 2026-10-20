# Workday PPTX brand skill

A reusable Cursor skill that builds on-brand PowerPoint decks from the Workday Corporate Template.

This repository is the brand system plus a small builder. It is not a dump of a real presentation. Sample copy in `examples/` is generic placeholder text.

| Path | What it is |
| --- | --- |
| [BRAND.md](BRAND.md) | Colors, type, layouts, footer, table and chart rules |
| [assets/template.pptx](assets/template.pptx) | Masters and layouts only, no sample slides |
| [assets/logos/](assets/logos) | Smile mark and decorative gradients |
| [assets/brand-tokens.json](assets/brand-tokens.json) | Machine-readable tokens |
| [.cursor/skills/workday-pptx/SKILL.md](.cursor/skills/workday-pptx/SKILL.md) | Instructions Cursor follows to make a deck |
| [scripts/build_deck.py](scripts/build_deck.py) | Outline to `.pptx` |
| [examples/outline.yaml](examples/outline.yaml) | Example outline |
| [examples/example-deck.pptx](examples/example-deck.pptx) | Example output from that outline |

## Install the skill in Cursor

The skill is the folder `.cursor/skills/workday-pptx/`. Cursor loads project skills from `.cursor/skills/` and personal skills from `~/.cursor/skills/`.

### Project skill (recommended for Workday repos)

Copy this repository's `.cursor/skills` directory into the repo that should produce decks, and keep `BRAND.md`, `assets/`, and `scripts/` beside it so the relative paths in the skill resolve.

```bash
cp -R .cursor/skills/workday-pptx <your-repo>/.cursor/skills/workday-pptx
cp -R BRAND.md assets scripts examples <your-repo>/
```

Or add this repository as a subtree / submodule and point the skill paths at it.

### Personal skill

```bash
mkdir -p ~/.cursor/skills
cp -R .cursor/skills/workday-pptx ~/.cursor/skills/workday-pptx
```

A personal copy still needs the template and `BRAND.md`. Keep the rest of this repo on disk and either leave the relative links as-is (if you cloned the whole repo into `~/.cursor/skills/workday-pptx-repo`) or edit the skill to use absolute paths to `BRAND.md` and `assets/template.pptx`.

After a copy, restart Cursor or reopen the folder so the skill is indexed. Ask Cursor to "make a Workday deck" or "use the workday-pptx skill".

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

## Fonts

Designed type is **Archivo** and **Archivo Light**. The Office theme fallback is Arial. Archivo is not embedded in the template. Install it from [Google Fonts](https://fonts.google.com/specimen/Archivo) on any machine that will author or render decks. If Archivo Light is missing, use Archivo. Do not substitute Proxima Nova (licensed, not bundled) or Calibri.

## Rules of the road

- Start from `assets/template.pptx`. Do not build a Workday deck from a blank theme.
- Use only colors in `BRAND.md`.
- Leave `Workday Confidential` in the footer placeholder.
- Do not put confidential customer copy into this repo.
