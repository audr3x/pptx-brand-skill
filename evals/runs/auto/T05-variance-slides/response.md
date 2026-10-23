I prepared the Google Slides request batches for the 4-slide "Budget variance review" deck, with cover option C (no image). Nothing was sent to Google, because Slides is not connected in this session.

Files in `evals/runs/auto/T05-variance-slides/slides/`:
- `creates.json`: 4 `createSlide` requests. Send this first, then run `read_presentation`.
- `fills-01.json`, `fills-02.json`, `fills-03.json`: 116 fill requests in 3 chunks of 40. Send them in order with the `requests` array inline. `fills.json` is the same batch unchunked.

Readback on `fills.json` confirmed all 15 outline items are in the batches.

1. **Cover**: "Budget variance review", subtitle "Operations, first half 2026", date "July 2026".
2. **Chart**, "Variance by department (USD thousands)": Facilities 45, IT -30, HR 12, Travel -18, Marketing 60. The value axis runs from -40 to 60 with a zero line, so IT and Travel hang below zero.
3. **Content**, "Actions": your 3 bullets.
4. **Closing**: the Workday bumper with the caption "Thank you".

What I changed and what you will see:
- **I shortened the chart title.** "Variance to budget by department (USD thousands)" is 48 characters, and the check warned that it would wrap into the chart. The slide now says "Variance by department (USD thousands)". If you want "to budget" back, I can move it into the subtitle instead.
- **The chart is drawn from shapes, not a live chart.** In Google Slides the builder draws columns, axis ticks, and gridlines as shapes. You can't edit the numbers in Slides. To change a value, update the outline and rebuild, or replace it by hand with a Sheets chart. The PNGs in `render/` come from a PowerPoint preview, so the axis there is slightly different (it tops out at 80).
- **The cover will be flat Ballpoint blue with white text**, because you chose option C. The PNG preview shows the gradient, which Slides will not have unless you add `cover-gradient.png` by hand (Insert > Image, 10 x 5.625 in at 0, 0, Send to back, then switch the cover text to Ink `#0F2E66`).
- Bullet dots in Slides follow the text size, so they look larger than in PowerPoint. Click one dot and lower its size if you want them smaller.

One question: the third action says "Reinvest 40 of the marketing surplus". I kept your wording. Did you mean USD 40 thousand (matching the chart units) or 40%? I can make it explicit once you confirm.
