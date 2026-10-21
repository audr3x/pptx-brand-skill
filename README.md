# Workday brand skills (PowerPoint and Google Slides)

On-brand Workday decks from the Corporate Template. PowerPoint is the native file. Google Slides uses the same tokens after you import `assets/template.pptx` once.

**Start here: [GETTING_STARTED.md](GETTING_STARTED.md)** (clone, install, Cursor prompts, Slides auth, two-phase flow, troubleshooting).

This repository is the brand system plus two small builders. It is not a dump of a real presentation. Sample copy in `examples/` is generic placeholder text.

| Path | What it is |
| --- | --- |
| [GETTING_STARTED.md](GETTING_STARTED.md) | How to use both skills on your machine |
| [BRAND.md](BRAND.md) | Colors, type, layouts, footer, table and chart rules |
| [assets/template.pptx](assets/template.pptx) | Masters and layouts only, no sample slides |
| [assets/logos/](assets/logos) | Smile mark, `cover-gradient.png`, and decorative SVGs |
| [assets/brand-tokens.json](assets/brand-tokens.json) | Machine-readable tokens |
| [scripts/brand.py](scripts/brand.py) | Validated brand registry and outline normalizer |
| [scripts/validate_brand.py](scripts/validate_brand.py) | Template, registry, and skill validator |
| [.cursor/skills/workday-pptx/SKILL.md](.cursor/skills/workday-pptx/SKILL.md) | PowerPoint skill |
| [.cursor/skills/workday-google-slides/SKILL.md](.cursor/skills/workday-google-slides/SKILL.md) | Google Slides skill |
| [scripts/build_deck.py](scripts/build_deck.py) | Outline to `.pptx` |
| [scripts/build_slides.py](scripts/build_slides.py) | Outline to Slides API / `gws` (or a request plan) |
| [examples/outline.yaml](examples/outline.yaml) | Shared example outline |
| [docs/proof/](docs/proof/) | Worked example `.pptx`, PNG thumbnails, and Slides JSON batches |

## Quick commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# managed Python / PEP 668: use the venv. Fallback: pip3 install --break-system-packages -r requirements.txt

python3 scripts/build_deck.py examples/outline.yaml -o out/planning-workshop.pptx

python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json -o docs/proof/slides/creates.json
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json --chunk 40 -o docs/proof/slides/fills.json
```

Full auth, `--upload-assets`, and Cursor chat examples are in [GETTING_STARTED.md](GETTING_STARTED.md).

## Rules

- Start from `assets/template.pptx` or a copy of the imported Slides template. Do not build from a blank theme.
- Treat `assets/brand-tokens.json` as the programmatic source for colors, layouts, limits, and geometry.
- Archivo for titles, Archivo Light for body (in Slides: Archivo at weight 300). Arial is the fallback.
- Leave `Workday Confidential` in the footer.
- Do not put confidential customer copy into this repo.
- Do not commit Google credentials, `gws` tokens, or `.env` files.

The shared registry covers all 15 template layouts through 20 outline patterns. It includes multi-speaker intros, feature grids, compact half-headlines, agendas, rail content, photo stories, timelines, tables, and charts.

## Verify changes

```bash
python3 scripts/validate_brand.py
python3 -m unittest discover -s tests -v
```

To compare the registry with the extraction source, pass the original deck explicitly:

```bash
python3 scripts/validate_brand.py \
  --source "/path/to/Workday Corporate PowerPoint Template 2.pptx"
```
