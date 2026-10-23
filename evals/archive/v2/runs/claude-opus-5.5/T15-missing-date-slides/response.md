I prepared the Google Slides request batches for a 3 slide Litware open enrollment kickoff deck, but the cover date is a **TODO**. "Next month" doesn't tell me the actual date, and I won't guess one. Please don't send the batches until you've given me the date and I've rebuilt them. Otherwise, "TODO: date" will print on the cover.

What the batches hold (readback found all 8 outline items in the fills):

1. **Cover:** "Open enrollment kickoff", with "Litware" as the subtitle and date **TODO**.
2. **Content, "What changes this year":** dental moves to a new carrier; the HSA employer match rises to $750; enrollment happens fully in the Workday app.
3. **Closing:** "Thank you". You didn't give a caption, so I used that. Tell me if you want different text.

Files are in `evals/runs/claude-opus-5.5/T15-missing-date-slides/slides/`:

- `creates.json`: 3 `createSlide` requests. Send this first.
- `fills-01.json`: 25 fill requests, in one chunk. Send it second, passing the `requests` array inline.

Nothing was sent to Google, because Slides isn't connected in this session. Before sending, replace each `layoutName` in `creates.json` with the matching `layoutId` from your imported Workday template.

The outline check flagged no figures or dates outside your request. Its only warning is the TODO on the cover.

Questions before I finalize:

1. **What date should the cover show?** A month and year, such as "November 2026", or the exact kickoff date both work.
2. **Which cover image option does your org allow?** You didn't say, so the batches use option C (no image). That gives a flat Ballpoint blue cover with white text, not the gradient in the `render/` preview PNGs, which come from a PowerPoint build of the same outline. If you can use option A (a Drive copy of `cover-gradient.png` shared as Anyone with the link) or option B (a public URL), send me the ID or URL and I'll add the gradient.
3. Is "Litware" the subtitle you want, or would you like something like an audience line instead?
