I prepared the Google Slides request batches for a 3-slide Litware "Open enrollment kickoff" deck. **The cover date is still a TODO**, because "next month" doesn't tell me the exact date. Nothing was sent to Google, because Slides is not connected in this session.

Files in `evals/runs/auto/T15-missing-date-slides/slides/`: `creates.json` (3 `createSlide` requests, send first, then `read_presentation`), then `fills-01.json` (20 fill requests), with the `requests` array inline. Readback on `fills.json` confirmed all 7 outline items are in the batches.

1. **Cover**: "Open enrollment kickoff", subtitle "Litware", date **"TODO: date"**.
2. **Content**, "What changes this year": dental moves to a new carrier. The HSA employer match rises to $750. Enrollment happens fully in the Workday app.
3. **Closing**: the Workday bumper, no caption. The check warns that this slide "has no content", which is expected, because you didn't give a caption.

Before you apply these batches, I need two answers:
1. **What date goes on the cover?** You said the kickoff is next month, but I won't guess the day or the month. Right now the cover would print "TODO: date". Send the date (for example "November 2026", or the exact day) and I'll regenerate the fills.
2. **Which cover image option does your org allow?** A (Drive file shared "Anyone with the link"), B (public URL), or C (no image). I built with **option C**, so the cover will be flat Ballpoint blue with white text, not the gradient in the preview PNGs in `render/`.

Also note: I used "Litware" as the subtitle. If you want a different subtitle (for example the plan year), tell me. Bullet dots in Slides follow the text size, so they look larger than in PowerPoint.
