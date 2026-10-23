I prepared the Google Slides request batches for the 4-slide "Manager training plan" deck, with cover option C (no image). Nothing was sent to Google, because Slides is not connected in this session.

Files in `evals/runs/auto/T02-training-slides/slides/`:
- `creates.json`: 4 `createSlide` requests on the Workday layouts. Send this first.
- `fills-01.json` and `fills-02.json`: 70 fill requests in 2 chunks of 40. After the creates, run `read_presentation`, then send these chunks in order with the `requests` array inline. `fills.json` is the same batch unchunked.

The outline check passed with no warnings. Readback on `fills.json` confirmed all 21 outline items are in the batches.

1. **Cover**: "Manager training plan", subtitle "Spring 2027 cohort", date "January 2027".
2. **Content**, "Why we are training managers": your 3 bullets (62% with no formal training, the manager named in 4 of 10 exit interviews, 6 hours over 3 weeks).
3. **Table**, "Schedule": headers Week, Topic, Format, plus your 3 rows (Week 1 Giving feedback, Workshop; Week 2 Running one-on-ones, Role play; Week 3 Planning goals, Workshop).
4. **Closing**: the Workday bumper with the caption "Questions".

What will look different from the preview PNGs in `render/`:
- **The cover will be flat Ballpoint blue, not the gradient.** You chose option C, so the title, subtitle, and date are white (Paper) and the Workday logo comes from the layout. The PNGs come from a PowerPoint preview, which shows the gradient. To add the gradient by hand: Insert > Image > Drive, choose `cover-gradient.png`, size it 10 x 5.625 in at 0, 0, use Arrange > Order > Send to back, then set the title, subtitle, and date to Ink `#0F2E66`.
- **Bullet dots follow the text size, so they look larger than in PowerPoint.** The Slides API has no setting for this. To make them smaller, click one dot (Slides selects them all) and lower the size.

After you apply the batches, check the deck with `read_presentation` to confirm the same text is there. I did not add or change any content.
