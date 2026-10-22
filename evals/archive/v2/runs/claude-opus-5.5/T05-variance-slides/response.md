I prepared the Google Slides request batches for the 4 slide "Budget variance review" deck with cover option C (no image). Nothing was sent to Google, because Slides isn't connected in this session.

Files in `evals/runs/claude-opus-5.5/T05-variance-slides/slides/`:

- `creates.json`: 4 `createSlide` requests. Send this first.
- `fills-01.json`, `fills-02.json`, and `fills-03.json`: 116 fill requests, chunked at 40. Send them in order, passing each `requests` array inline. `fills.json` holds the same requests in one file.

What the slides hold (readback found all 15 outline items in the fills):

1. Cover: "Budget variance review", "Operations, first half 2026", July 2026.
2. Chart: one "Variance" series for Facilities 45, IT -30, HR 12, Travel -18, and Marketing 60. The negative bars hang below a zero line on a -40 to 60 axis.
3. Content, "Actions": your 3 actions as written. I kept "Reinvest 40 of the marketing surplus" without adding a unit, because the request didn't give one.
4. Closing: "Thank you".

Things that change what you will see:

- **Chart title shortened.** "Variance to budget by department (USD thousands)" is 48 characters, and on the first build it wrapped onto the chart. I changed it to "Variance by department (USD thousands)". Tell me if you want different wording that fits on one line, about 42 characters.
- **The chart is shapes, not a chart object.** Google Slides draws it as blue columns with a value axis and gridlines. You can't edit the data in Slides. To change a number, change the outline and rebuild the batches, or add a Sheets chart by hand. The chart has one series, so there is no legend, and no data labels are drawn on the bars.
- **Cover:** with option C the cover is flat Ballpoint blue with white title, subtitle, and date, not the gradient in the `render/` preview PNGs. Those PNGs come from a PowerPoint built from the same outline, so treat them as a layout check only.
- **Layout IDs:** `createSlide` names each layout by `layoutName`. Before sending, swap each one for the `layoutId` from `presentations.get` on your imported Workday template.

After the title change, the outline check passed with no warnings, and no figures or dates outside your request were added.
