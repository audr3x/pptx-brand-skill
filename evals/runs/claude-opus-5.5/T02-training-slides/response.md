I prepared the Google Slides request batches for the 4 slide "Manager training plan" deck. Nothing was sent to Google, because Slides is not connected in this session.

Files in `evals/runs/claude-opus-5.5/T02-training-slides/slides/`:
- `creates.json`: 4 `createSlide` requests on the Workday layouts. Send these first, then read the presentation back so the fills can bind to the new placeholder IDs.
- `fills-01.json` and `fills-02.json`: the 70 fill requests in 2 chunks of 40 at most. Send them in order, each as an inline `requests` array. `fills.json` holds the same requests in one file.

The slides:
1. Cover: "Manager training plan", subtitle "Spring 2027 cohort", date "January 2027".
2. Content, "Why we are training managers": your 3 bullets (62% with no formal training, the manager named in 4 of 10 exit interviews, 6 hours over 3 weeks).
3. Table, "Schedule": headers Week, Topic, Format, and your 3 rows.
4. Closing: "Questions" as the caption under the Workday logo.

The outline check passed with no warnings and the readback found all 21 outline items in the fills batch. Nothing was invented or cut.

What will look different from the preview PNGs in `render/` (those are rendered from a PowerPoint built from the same outline):
- Cover option C means no gradient image. The cover is flat Ballpoint blue with the title, subtitle, and date in Paper (white), plus the logo from the layout. To add the gradient later: Insert > Image > Drive with `cover-gradient.png`, size it 10 x 5.625 in at 0, 0, Arrange > Order > Send to back, then set the title, subtitle, and date to Ink `0F2E66`.
- Bullet dots in Slides follow the text size, so they look larger than in PowerPoint. To shrink them, click one dot (that selects every dot in the list) and lower the font size.

After you apply the batches, run `read_presentation` to confirm the text landed on each slide.
