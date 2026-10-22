I have prepared the Google Slides request batches for the "Litware sales kickoff" presentation using the `workday-google-slides` skill and cover option C.

### What was built

The Google Slides API request batches are located in `slides/`:
- `slides/creates.json`: 4 `createSlide` requests matching Workday layouts.
- `slides/fills.json` (chunked into `fills-01.json`, `fills-02.json`, and `fills-03.json`): 82 fill requests.
- `preview.pptx` and preview PNGs in `render/` for visual verification.

### Slide structure

1. **Title slide**: "Litware sales kickoff", date "February 2027" (Title Slide layout, flat Ballpoint background with Paper type).
2. **Pipeline chart**: "Pipeline by segment", comparing Enterprise (55), Mid-market (30), and Small business (15).
3. **Team introduction**: "Meet the team", using the `photo-right` layout.
4. **Closing slide**: Bumper slide featuring "Thank you" under the Workday smile.

### Platform limits and brand guidelines

Several requested elements have specific platform constraints or brand limitations:

1. **Orange slide titles**:
   - The Workday brand system does not permit changing title text to orange. The template enforces Ink (`#0F2E66`) bold Archivo typography across all slides to ensure consistent contrast and brand integrity. Custom color overrides are rejected by the builder.

2. **Pie chart in Google Slides**:
   - Google Slides cannot generate native editable charts via API without a linked Google Spreadsheet. The builder renders all chart data as clustered column shapes with a value axis. If an actual pie chart is required, we recommend generating the deck in PowerPoint (where pie charts are natively supported) or linking a Google Sheet chart manually.

3. **Team photo placement**:
   - The Google Slides API cannot populate local image files into slide layout placeholders. On slide 3 ("Meet the team"), please insert `examples/images/sample-photo.png` manually in Google Slides via **Insert > Image > Upload from computer** (or Drive).

4. **Speaker notes**:
   - Speaker notes are supported in PowerPoint but are not written to Google Slides by the builder API. Speaker notes can be typed directly into Google Slides or authored natively via the `workday-pptx` skill.

5. **Cover gradient (Option C)**:
   - The cover currently uses flat Ballpoint fill with Paper text and the layout smile. To add the Day Crop gradient: select **Insert > Image > Drive** (`cover-gradient.png`), size to 10.00 x 5.625 in at position 0, 0, select **Arrange > Order > Send to Back**, and change the title and date font color to Ink (`#0F2E66`).

### Applying the request batches

1. Run `creates.json` via `update_presentation`.
2. Call `read_presentation` to map created slide IDs.
3. Send `fills-01.json`, `fills-02.json`, and `fills-03.json` sequentially with the requests array inline.
