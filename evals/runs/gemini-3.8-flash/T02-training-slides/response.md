I have prepared the Google Slides request batches for the 4-slide "Manager training plan" presentation using the `workday-google-slides` skill and cover option C (no image).

### What was built

The Google Slides API request batches are located in `slides/`:
- `slides/creates.json`: 4 `createSlide` requests matching Workday layouts.
- `slides/fills.json` (chunked into `slides/fills-01.json` and `slides/fills-02.json`): 70 fill requests formatted in chunks of 40.
- `preview.pptx` and rendered slide images in `render/` for visual verification.

### Slide structure

1. **Title slide**: "Manager training plan", subtitle "Spring 2027 cohort", date "January 2027".
2. **Content slide**: "Why we are training managers", featuring 3 bullets on training statistics and duration.
3. **Table slide**: "Schedule", with a 3x3 table (Week, Topic, Format) styled with Water Cooler header, alternating Keyboard/Business Card rows, and Desk borders.
4. **Closing slide**: Bumper slide with caption "Questions" under the Workday smile.

### Application steps & cover option C notes

- **Applying the batches**:
  1. Send `creates.json` via `update_presentation`.
  2. Call `read_presentation` to resolve created slide and shape IDs.
  3. Send `fills-01.json` and `fills-02.json` in order with the requests array inline.
- **Cover option C**: The cover uses a flat Ballpoint (`#0057AE`) background with Paper text and the layout's white Workday smile. If you wish to apply the Day Crop gradient later in Google Slides:
  1. Select Insert > Image > Drive and choose `cover-gradient.png` (size 10.00 x 5.625 in at position 0, 0).
  2. Choose Arrange > Order > Send to Back.
  3. Change the title, subtitle, and date text color to Ink (`#0F2E66`).
