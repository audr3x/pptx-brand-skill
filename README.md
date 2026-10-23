# Workday brand skills (PowerPoint and Google Slides)

On-brand Workday decks from the Corporate Template. PowerPoint is the native file. Google Slides uses the same tokens after you import `assets/template.pptx` once.

**Start here: [GETTING_STARTED.md](GETTING_STARTED.md)** (clone, install, Cursor prompts, Slides auth, two-phase flow, troubleshooting).

**Writing the prompt: [docs/PROMPTING.md](docs/PROMPTING.md)** (what to include, layouts per slide, images, charts, copy-paste prompts, checklist).

## Which model to use

Use **Claude Opus 5.5** or **Gemini 3.8 Flash** in Cursor. Both scored top marks in our 16-task eval (`evals/FINDINGS.md`): every fact kept, nothing invented, and replies that match the deck.

Avoid the other models we tested for decks you send to customers:

- **Composer 2.5** invented cover dates (for example "October 2026" when no date was given) and did not say so.
- **Gemini 3.1 Pro** dropped content (a next-step owner, a deck it was asked to build) and once misreported which chart value it changed.

Whatever the model, read its reply for any `TODO` and check the readback result before you send a deck.

This repository is the brand system plus two small builders. It is not a dump of a real presentation. Sample copy in `examples/` is generic placeholder text.

| Path | What it is |
| --- | --- |
| [GETTING_STARTED.md](GETTING_STARTED.md) | How to use both skills on your machine |
| [BRAND.md](BRAND.md) | Colors, type, layouts, footer, table and chart rules |
| [assets/template.pptx](assets/template.pptx) | Masters and layouts only, no sample slides |
| [assets/logos/](assets/logos) | Smile mark, `cover-gradient.png`, and decorative SVGs |
| [assets/brand-tokens.json](assets/brand-tokens.json) | Machine-readable tokens |
| [.cursor/skills/workday-pptx/SKILL.md](.cursor/skills/workday-pptx/SKILL.md) | PowerPoint skill |
| [.cursor/skills/workday-google-slides/SKILL.md](.cursor/skills/workday-google-slides/SKILL.md) | Google Slides skill |
| [.cursor/skills/workday-deck-prompting/SKILL.md](.cursor/skills/workday-deck-prompting/SKILL.md) | Brief to outline skill (what the builders support) |
| [docs/PROMPTING.md](docs/PROMPTING.md) | Prompting guide with copy-paste prompts |
| [docs/LIMITS.md](docs/LIMITS.md) | What the check refuses, warns about, and what the builders cannot do |
| [scripts/build_deck.py](scripts/build_deck.py) | Outline to `.pptx` |
| [scripts/build_slides.py](scripts/build_slides.py) | Outline to Slides API / `gws` (or a request plan) |
| [scripts/check_outline.py](scripts/check_outline.py) | Checks an outline against what both builders read |
| [examples/outline.yaml](examples/outline.yaml) | Shared example outline |
| [examples/images/](examples/images) | Sample photo for `intro` and `photo-right` |
| [tests/](tests) | `python3 -m unittest discover -s tests` |
| [docs/proof/](docs/proof/) | Worked example `.pptx`, PNG thumbnails, and Slides JSON batches |

## Quick commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# managed Python / PEP 668: use the venv. Fallback: pip3 install --break-system-packages -r requirements.txt

python3 scripts/build_deck.py examples/outline.yaml -o out/planning-workshop.pptx

python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json -o out/slides/creates.json
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json --chunk 40 -o out/slides/fills.json
```

Full auth, `--upload-assets`, and Cursor chat examples are in [GETTING_STARTED.md](GETTING_STARTED.md).

## Rules

- Start from `assets/template.pptx` or a copy of the imported Slides template. Do not build from a blank theme.
- Use only colors in `BRAND.md`.
- Archivo for titles, Archivo Light for body (in Slides: Archivo at weight 300). Arial is the fallback.
- Leave `Workday Confidential` in the footer.
- Do not put confidential customer copy into this repo.
- Do not commit Google credentials, `gws` tokens, or `.env` files.
