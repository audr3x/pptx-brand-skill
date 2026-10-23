I prepared the Google Slides request batches for the Woodgrove Bank "Manager training kickoff" deck. The deck has **5 slides, not 4**, and the cover date is **April 8, 2027, not March 2027**. Your request had two conflicts, explained below. Nothing was sent to Google, because Slides is not connected in this session.

Files in `evals/runs/auto/T12-conflicting-slides/slides/`: `creates.json` (5 `createSlide` requests, send first, then `read_presentation`), then `fills-01.json`, `fills-02.json`, and `fills-03.json` (107 fill requests) in order, with the `requests` array inline. Readback on `fills.json` confirmed all 28 outline items are in the batches.

1. **Cover**: "Manager training kickoff", subtitle "Woodgrove Bank people leaders", date "April 8, 2027".
2. **Agenda** (content): Why we are training managers. The three tracks. Schedule. How to sign up.
3. **The three tracks** (two-column): Coaching basics builds weekly 1:1 habits. Performance conversations practices feedback with role play. Leading through change helps managers explain the new org design.
4. **Schedule** (table, columns Track, Format, Weeks): Coaching basics, live virtual, weeks 1 to 3. Performance conversations, in person, weeks 4 to 6. Leading through change, self-paced, weeks 7 to 8.
5. **Closing**: the Workday bumper. You didn't give a caption, so there is no text under the logo. The check warns that this slide "has no content", which is expected.

The two conflicts and how I handled them:
- **Slide count.** You asked for exactly 4 slides (cover, agenda, schedule, closing), then asked me to add a tracks slide. I followed the later request, so the deck has 5 slides. If 4 is a hard limit, tell me which slide to drop. For example, I could remove the tracks slide, or replace the agenda with it.
- **Cover date.** The cover line said March 2027, but you then said the kickoff is on April 8, 2027 and to use that date. The cover shows April 8, 2027, and March 2027 does not appear anywhere in the deck.

What you will see in Slides:
- **Cover option.** You didn't say which cover image option your org allows, so I used **option C (no image)**. The cover will be flat Ballpoint blue with white text, not the gradient in the preview PNGs in `render/`. If you can share `cover-gradient.png` through a Drive "Anyone with the link" file (option A) or a public URL (option B), tell me and I'll regenerate the fills with the gradient.
- Bullet dots on the agenda follow the text size, so they look larger than in PowerPoint. Click one dot and lower its size if you want them smaller.
- I capitalized the first word of each format cell ("Live virtual", "In person", "Self-paced") to match sentence case.

Questions:
1. Is 5 slides OK, or should I cut back to exactly 4?
2. Which cover image option should I use: A, B, or C?
3. Do you want a caption on the closing slide (for example "Questions" or "See you on April 8")?
