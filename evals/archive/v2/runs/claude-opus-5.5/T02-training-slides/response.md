I prepared the Google Slides request batches for the 4 slide "Manager training plan" deck with cover option C (no image). Nothing was sent to Google, because Slides isn't connected in this session.

Files in `evals/runs/claude-opus-5.5/T02-training-slides/slides/`:

- `creates.json`: 4 `createSlide` requests on the Workday layouts. Send this first.
- `fills-01.json` and `fills-02.json`: the 70 fill requests in two chunks of 40 or fewer. Send them in that order, after the creates, passing each `requests` array inline. `fills.json` holds the same requests in one file.

What the slides hold (readback found all 21 outline items in the fills):

1. Cover: "Manager training plan", "Spring 2027 cohort", January 2027.
2. Content, "Why we are training managers": 62% of new managers have had no formal training; exit interviews name the manager in 4 of 10 cases; the program takes 6 hours over 3 weeks.
3. Table, "Schedule": headers Week, Topic, and Format, with your 3 rows.
4. Closing: "Questions" under the Workday logo.

The outline check passed with no warnings. Everything is included and nothing was invented.

Things that change what you will see:

- **Cover:** with option C the cover is flat Ballpoint blue with white (Paper) title, subtitle, and date, not the gradient in the preview PNGs. The PNGs in `render/` come from a PowerPoint built from the same outline, because Slides can't be rendered offline. To add the gradient by hand: Insert > Image > Drive, choose `cover-gradient.png`, size it to 10 x 5.625 in at 0, 0, use Arrange > Order > Send to back, then set the title, subtitle, and date to Ink `#0F2E66`.
- **Layout IDs:** the batches were planned without a live presentation, so `createSlide` names each layout by `layoutName`. Before sending, replace each `layoutName` with the matching `layoutId` from `presentations.get` on your imported template. Alternatively, re-run the fills with `--presentation get.json` once the deck exists.
- **Bullets:** in Slides, bullet dots follow the text size, so they look a little larger than in PowerPoint.
