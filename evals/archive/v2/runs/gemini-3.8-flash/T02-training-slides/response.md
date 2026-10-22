I have prepared the Google Slides request batches for the 4-slide "Manager training plan" deck using the `workday-google-slides` skill and cover option C (no image).

### What was built

Because Google Slides is not connected in this session, the request batches are prepared in `slides/`:
- `slides/creates.json`: 4 `createSlide` requests referencing the imported Workday layouts.
- `slides/fills.json` (split into `slides/fills-01.json` and `slides/fills-02.json` in chunks of 40): 70 fill requests formatted inline for the Slides API.
- `preview.pptx` and rendered slide PNGs in `render/` for previewing.

### Slide structure

1. **Title slide**: "Manager training plan", subtitle "Spring 2027 cohort", date "January 2027".
2. **Content slide**: "Why we are training managers", with 3 bullet points on manager training statistics and program duration.
3. **Table slide**: "Schedule", displaying a 3x3 table with headers `Week`, `Topic`, and `Format` styled with Water Cooler header, alternating Keyboard/Business Card rows, and Desk borders.
4. **Closing slide**: Bumper slide featuring caption "Questions" under the Workday smile.

### How to apply the batches & cover option C instructions

- **Application steps**:
  1. Send `creates.json` via `update_presentation`.
  2. Call `read_presentation` to resolve created slide and shape IDs.
  3. Send `fills-01.json` and `fills-02.json` sequentially with the `requests` array inline.
- **Cover option C (no image)**:
  - The cover uses a flat Ballpoint (`#0057AE`) background with Paper type and the layout's white Workday smile.
  - To add `cover-gradient.png` manually: choose **Insert > Image > Drive**, set dimensions to 10.00 x 5.625 in at position 0, 0, select **Arrange > Order > Send to Back**, and change the title, subtitle, and date font color to Ink (`#0F2E66`).
