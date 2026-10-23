I prepared the Google Slides request batches for the 4 slide "Budget variance review" deck. Nothing was sent to Google, because Slides is not connected in this session.

Files in `evals/runs/claude-opus-5.5/T05-variance-slides/slides/`:
- `creates.json`: 4 `createSlide` requests on the Workday layouts. Send it first, then read the presentation back.
- `fills-01.json`, `fills-02.json`, and `fills-03.json`: the 116 fill requests in chunks of 40. Send them in order, each as an inline `requests` array. `fills.json` holds the same requests in one file.

The slides:
1. Cover: "Budget variance review", subtitle "Operations, first half 2026", date "July 2026".
2. Chart: Facilities 45, IT -30, HR 12, Travel -18, Marketing 60, one "Variance" series. The value axis runs from -40 to 60. IT and Travel hang below the zero line.
3. Content, "Actions": your 3 bullets as written.
4. Closing: "Thank you" under the Workday logo.

One change: I shortened the chart title from "Variance to budget by department (USD thousands)" to "Variance by department (USD thousands)". The original is 48 characters, and this layout fits about 42 before the title wraps into the chart. Tell me if you want the full title back and I will accept the wrap.

The outline check passed with no warnings, and the readback found all 15 outline items in the fills batch. No TODOs are left.

What will look different from the preview PNGs in `render/` (those come from a PowerPoint built from the same outline):
- The chart is drawn from shapes: columns, a value axis, tick labels, and gridlines. It is not an editable data chart. To change a number, change the outline and rebuild the slide. For a live chart, add a Google Sheets chart by hand.
- Cover option C means no gradient image. The cover is flat Ballpoint blue with white title, subtitle, and date. To add the gradient later: Insert > Image > Drive with `cover-gradient.png`, 10 x 5.625 in at 0, 0, Send to back, then switch the three cover text runs to Ink `0F2E66`.
- Bullet dots in Slides follow the text size, so they look larger than in PowerPoint.

One question: "Reinvest 40 of the marketing surplus" has no unit. Should it say 40 thousand USD, to match the chart, or 40%? I left it as you wrote it.
