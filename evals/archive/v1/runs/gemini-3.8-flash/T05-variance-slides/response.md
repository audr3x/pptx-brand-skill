I have prepared the Google Slides request batches for the 4-slide "Budget variance review" deck using the `workday-google-slides` skill and cover option C.

### What was built

The Google Slides batch update files have been generated in `slides/`:
- `slides/creates.json`: 4 `createSlide` requests for Workday layouts.
- `slides/fills.json` (split into `fills-01.json`, `fills-02.json`, `fills-03.json` in chunks of 40): 116 fill requests.
- `preview.pptx` and rendered PNGs in `render/` for previewing.

### Slide structure

1. **Title slide**: "Budget variance review", subtitle "Operations, first half 2026", date "July 2026" (Title Slide layout, flat Ballpoint background with Paper type).
2. **Chart slide**: "Variance to budget by department (USD thousands)", drawing clustered column shapes for Facilities (45), IT (-30), HR (12), Travel (-18), and Marketing (60) with a zero baseline, Desk gridlines, and Water Cooler fill.
3. **Content slide**: "Actions", with 3 action items covering IT contracts, travel approvals, and marketing surplus reinvestment.
4. **Closing slide**: Bumper slide with "Thank you" under the Workday smile.

### Warnings and Google Slides notes

- **Title length warning**: On slide 2, the title "Variance to budget by department (USD thousands)" is 48 characters, which exceeds the layout recommendation of ~42 characters for Title Only and may wrap onto a second line. If you prefer a single-line title, you can shorten it to "Variance to budget by department ($k)".
- **Chart behavior in Google Slides**: The chart is rendered from native shapes with a value axis and gridlines, handling both positive and negative values. As noted in the skill guide, these shapes are not linked to Google Sheets and cannot be edited as live spreadsheet data.
- **Cover option C**: Rendered with flat Ballpoint background and layout smile. To add `cover-gradient.png` manually: Insert > Image > Drive, size to 10.00 x 5.625 in at 0, 0, Send to back, and change text to Ink (`#0F2E66`).
- **Applying the batches**: Run `creates.json` first via `update_presentation`, then `read_presentation`, then apply `fills-01.json`, `fills-02.json`, and `fills-03.json` in order.
