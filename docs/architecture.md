# Brand system architecture

## Problem

The first builders copied colors, fonts, aliases, layout limits, and geometry into two scripts. Several template layouts then gained only partial support. A change in one builder could not prove that the other builder or the skills still matched the template.

## Usage

Authors choose a pattern and provide its content:

```yaml
slides:
  - layout: intro-three
    speakers:
      - {name: Alex, role: Engineer, company: Workday, image: alex.png}
      - {name: Blake, role: Designer, company: Workday, image: blake.png}
      - {name: Casey, role: Product, company: Workday, image: casey.png}
  - layout: two-column-alt
    title: Six priorities
    items:
      - {title: Priority one, body: Supporting detail}
```

`build_deck.py` accepts local image paths. `build_slides.py` accepts public image URLs.

## Shape

`assets/brand-tokens.json` owns the theme, template layout registry, pattern registry, placeholder indexes, capacities, and named geometry. `scripts/brand.py` validates that file and converts each raw outline slide into a `NormalizedSlide`.

Each pattern selects one closed `Composition` value. The PowerPoint and Google Slides builders implement the same composition set with format-specific functions. The builders do not own aliases, limits, placeholder indexes, geometry, fonts, or colors.

Validation happens when `brand.py` loads the registry and when it normalizes an outline. Renderer functions trust the normalized slide. `validate_brand.py` compares the registry with `template.pptx`, checks skill links, rejects copied hex literals in the builders, and can compare an external source deck.

## Synthesis decision

The design comparison selected a data registry over a Python-only registry. The data registry keeps every brand fact in one reviewable file. The Python-only candidate contributed the closed composition enum and explicit renderer functions. Those functions prevent the registry from becoming a general drawing language.

## Tradeoffs accepted

- The JSON registry is larger in exchange for removing synchronized constants from two builders.
- Each renderer still has one function per composition in exchange for keeping format APIs out of the registry.
- Google Slides requires public image URLs because the Slides API fetches image content by URL.
- `BRAND.md` remains a human reference. The validator and tests, not prose, enforce the programmatic contract.

## Alternatives considered

A Python-only layout registry was smaller. It split colors and typography from layout facts, so maintainers still had to reconcile two sources.

A generic JSON drawing language could describe every shape. It would move renderer logic into untyped data and make the registry harder to review than the current code.

## Open risks

Live Google Slides import can change placeholder object IDs. `rewrite_slide_requests()` resolves IDs by placeholder index after slide creation. The unit test covers that rewrite, but a signed-in integration run remains the final API check.

## Next implementation step

Add a new pattern to `brand-tokens.json`, implement its closed composition in both builders, and extend the all-patterns test.
