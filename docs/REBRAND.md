# Replace branding / master deck

How to point this repo at **your** corporate template instead of Workday’s. The builders do not auto-discover a new brand from a PPTX alone — you swap assets, then keep names and tokens in sync with the code.

If you only need Workday decks, stop here and use [GETTING_STARTED.md](../GETTING_STARTED.md).

## What you are swapping

| Asset | Role |
| --- | --- |
| `assets/template.pptx` | Slide master + layouts the PowerPoint builder starts from |
| `assets/logos/` | Cover gradient, lockup / smile, decorative SVGs |
| `assets/brand-tokens.json` | Documented palette, type, footer defaults (source of truth for humans and skills) |
| `BRAND.md` | Human brand rules the skills must follow |
| `scripts/build_deck.py` / `scripts/build_slides.py` | **Hardcoded** hex map, chart series order, font names, and some layout geometry |
| `.cursor/skills/workday-*` | Skill names and “use only BRAND.md tokens” instructions |

`brand-tokens.json` is **not** loaded by the builders today. Editing only that file will not change chart colors or fonts in the `.pptx`. Update the Python maps too (or teach the builders to read the JSON — not done yet).

## Hard constraint: layout names

`scripts/outline_rules.py` maps outline intents to **exact** layout names (case-insensitive, trailing spaces stripped), for example:

| Outline `layout` | Required template layout name |
| --- | --- |
| `title` | `Title Slide` |
| `section` | `Section Title` |
| `content` | `Title and Content` (trailing space in the PPTX is OK) |
| `two-column` | `1/2_Headline` |
| `table` / `chart` | `Title Only` |
| `closing` | `Bumper Slide` |
| `intro` | `Intro_One` |
| `photo-right` | `Photo-Right` |
| `blank` | `Blank White Background` |

**Best path:** keep those layout **names** (and roughly the same placeholders) in your new master. Restyle colors, logos, and backgrounds inside the layouts.

If you rename layouts, you must update `LAYOUT_ALIASES` / `LAYOUT_FIELDS` in `scripts/outline_rules.py` and any layout-specific branches in `build_deck.py` / `build_slides.py` (cover, section rail, bumper caption, footer inset, intro placeholders). Missing a name → `Unknown layout` and a failed build.

## Checklist (same layout names)

Do these in order.

### 1. Drop in the master

1. Export your corporate template as a **16:9** `.pptx` with **masters only** (no sample narrative slides).
2. Replace `assets/template.pptx`.
3. Confirm every name in the table above still exists:

   ```bash
   python3 - <<'PY'
   from pptx import Presentation
   prs = Presentation("assets/template.pptx")
   for i, ly in enumerate(prs.slide_layouts):
       print(f"{i}: {ly.name!r}")
   PY
   ```

4. Slide size should stay **10.00 × 5.625 in**. Geometry in `BRAND.md` and the builders assumes that canvas.

### 2. Logos and cover art

| File | Used for |
| --- | --- |
| `assets/logos/workday-smile.png` | PPTX title/bumper chrome (embedded in template) and optional Slides smile |
| `assets/logos/cover-gradient.png` | Google Slides cover image options A/B |

Replace the PNGs with your lockup and cover art, **or** edit the pictures already sitting on `Title Slide` / `Bumper Slide` inside the new `template.pptx` and leave the repo PNGs unused for PowerPoint.

For Google Slides: re-import the new PPTX once, re-upload cover assets, and refresh any saved template / cover file IDs (`WORKDAY_SLIDES_TEMPLATE_ID`, cover image ID). See [GETTING_STARTED.md](../GETTING_STARTED.md).

Regenerate `cover-gradient.png` from the new title layout if you still use that helper:

```bash
python3 scripts/export_cover_assets.py
```

(That script reads `Title Slide` from `assets/template.pptx`. If your cover art is not that layout’s background, replace the PNG by hand instead.)

### 3. Colors and type

1. Rewrite the **Core** / **Secondary** tables in `BRAND.md` to your palette. Delete hex values you will not allow.
2. Mirror the same hex values in `assets/brand-tokens.json` (`core`, `secondary`, `chart_series`, `fonts`, `footer`).
3. In **both** `scripts/build_deck.py` and `scripts/build_slides.py`, update the `CORE` / `SECONDARY` dicts, `CHART_SERIES` list, and `FONT_TITLE` / `FONT_BODY` (and Slides weight handling if you drop Archivo).
4. Default footer string is `Workday Confidential` in the builders and outlines — change the default in code and in `brand-tokens.json` → `footer.text`, or always set `footer:` in each outline.
5. Install your title/body fonts on every machine that builds or opens decks. Theme fallback remains Arial unless you change the template theme.

### 4. Skills and docs

1. Edit `.cursor/skills/workday-pptx/SKILL.md`, `workday-google-slides/SKILL.md`, and `workday-deck-prompting/SKILL.md` so they name **your** brand, point at the updated `BRAND.md`, and do not tell the agent to invent off-brand colors.
2. Optionally rename the skill directories (and the `name:` frontmatter) so prompts say `acme-pptx` instead of `workday-pptx`. Cursor loads whatever folders sit under `.cursor/skills/`.
3. Update README / GETTING_STARTED examples so the external team is not told to “follow Workday” after you rebranded.

### 5. Prove it

```bash
python3 scripts/check_outline.py --target pptx examples/outline.yaml
python3 scripts/build_deck.py examples/outline.yaml -o out/rebrand-smoke.pptx
python3 scripts/readback.py examples/outline.yaml out/rebrand-smoke.pptx --show
python3 -m unittest discover -s tests
```

Open `out/rebrand-smoke.pptx` in PowerPoint. Check cover, one content slide, table, chart, and bumper: correct logo, no leftover Workday smile, footer text, and chart series colors from your palette.

For Slides, re-import the new template and run the usual two-phase flow on a copy.

## Harder: different layout set

If your master uses different names or fewer layouts:

1. Map each outline intent you still want (`title`, `content`, …) to a real layout name in `LAYOUT_ALIASES`.
2. Keep or rewrite `LAYOUT_FIELDS` so the check knows which outline keys each layout draws.
3. Fix builder branches that special-case Workday chrome (`Title Slide`, `Section Title`, `Bumper Slide`, section footer at x = 3.32 in, bumper caption under the smile, intro placeholder order).
4. Expect to edit tests under `tests/` and proof assets under `docs/proof/`.

If the new master is blank or has only one layout, this repo is the wrong starting point — you would be rewriting the builders, not rebranding.

## What not to do

- Do not build from a blank Office theme and hope the skills “pick up” brand from a PDF style guide.
- Do not change only `brand-tokens.json` and assume charts/fonts follow.
- Do not leave Workday logos on `Title Slide` / `Bumper Slide` after swapping colors — the template embeds them.
- Do not commit customer decks or confidential copy while you rebrand; keep samples generic (`examples/`).

## Minimal “colors only” path

If the Workday layout structure is fine and you only need a different palette + logo:

1. Replace pictures on the existing layouts in `assets/template.pptx` (or swap PNGs in `assets/logos/` and re-embed).
2. Update hex + fonts in `BRAND.md`, `brand-tokens.json`, and both builders.
3. Smoke-test with `examples/outline.yaml` as above.

That is the smallest change that still produces on-brand output.
