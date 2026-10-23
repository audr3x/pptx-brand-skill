I have prepared the Google Slides request batches for the 3-slide Litware open enrollment kickoff presentation using the `workday-google-slides` skill and cover option C.

### What was built

Because Google Slides is not connected in this session, the request files are located in `slides/`:
- `slides/creates.json`: 3 `createSlide` requests for Workday layouts.
- `slides/fills.json` (`slides/fills-01.json`): 23 fill requests formatted inline for the Slides API.
- `preview.pptx` and rendered slide PNGs in `render/` for previewing.

### Slide structure

1. **Title slide**: "Open enrollment kickoff", date marked as `TODO`.
2. **Content slide**: "What changes this year", with 3 bullets detailing the carrier change for dental, the HSA match increase to $750, and full enrollment in the Workday app.
3. **Closing slide**: Bumper slide with "Thank you" under the Workday smile.

### Missing date clarification

- The prompt specified "next month" without a specific month, day, or year. Under Workday brand and prompting guidelines, dates are never assumed or invented, so the cover date has been set to `TODO`.
- **Question for the user**: Which exact date (e.g., "November 2026") should be placed on the cover?

### How to apply the request batches

1. Send `creates.json` via `update_presentation`.
2. Run `read_presentation` to resolve slide and placeholder IDs.
3. Send `fills-01.json` inline via `update_presentation`.
4. Cover option C uses a flat Ballpoint (`#0057AE`) background. To add `cover-gradient.png` manually: choose **Insert > Image > Drive**, size to 10.00 x 5.625 in at position 0, 0, choose **Arrange > Order > Send to Back**, and change text color to Ink (`#0F2E66`).
