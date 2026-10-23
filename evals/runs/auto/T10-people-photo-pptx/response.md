I built the 5-slide Proseware intro deck: `evals/runs/auto/T10-people-photo-pptx/deck.pptx`. Outline: `outline.yaml`. PNGs are in `render/`.

The check passed with no warnings, and readback confirmed all 15 outline items are on the slides.

1. **Cover**: "Meet your Workday team", subtitle "Proseware onboarding", date "March 2027".
2. **Intro**: Dana Whitfield, Client Partner, Workday, with `examples/images/sample-photo.png` in the photo frame on the warm Intro layout.
3. **Photo-right**, "Our Chicago office": the title on the left and the same photo filling the right side. This layout has no body text area, so the slide shows only the title and the photo.
4. **Two-column**, "How Dana will help": 01 Plan, 02 Connect, 03 Review, each with your line as the body. I split each line at the colon into a short item title and a body. The half-width title wraps onto two lines, which is how this layout is designed.
5. **Closing**: the Workday bumper with the caption "Welcome to Workday".

One thing to check: `examples/images/sample-photo.png` is a generic placeholder silhouette, not a real photo of Dana or the Chicago office. Both photo slides show that silhouette. If you send real photos (PNG or JPEG saved in the repository), I'll swap them in. The photo slots crop to fit, so leave some space around faces.
