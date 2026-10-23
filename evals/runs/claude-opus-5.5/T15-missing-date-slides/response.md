I prepared the Google Slides request batches for a 3 slide "Open enrollment kickoff" deck. Nothing was sent to Google, because Slides is not connected in this session. **Before you apply it, I need the cover date.** You asked for the date on the cover, but "next month" does not tell me which date to print. I did not guess one, so the cover currently reads "TODO: date", and that text would appear on the slide exactly like that.

The slides:
1. Cover: "Open enrollment kickoff", subtitle "Litware", date **TODO**. I added the "Litware" subtitle from your request. Tell me if you want different wording or no subtitle.
2. Content, "What changes this year": Dental moves to a new carrier, HSA employer match rises to $750, Enrollment happens fully in the Workday app.
3. Closing: "Thank you" under the Workday logo. That caption is my addition.

The readback found all 8 outline items in the fills batch. The only check warning is the TODO on the cover.

Files in `evals/runs/claude-opus-5.5/T15-missing-date-slides/slides/`: send `creates.json` first, read the presentation back, then send `fills-01.json` (25 requests) as an inline `requests` array. Once you send the date, I will regenerate the fills with it. Please hold off on applying this batch until then.

Please tell me:
1. **The cover date.** The exact day of the kickoff, or the month and year to print, for example "November 2026".
2. **The cover image option** your org allows. You did not say, so I used option C (no image): a flat Ballpoint blue cover with white type, not the gradient shown in the preview PNGs, which come from PowerPoint. Option A is a Drive image shared "Anyone with the link". Option B is a public URL. Either one gives you the Workday gradient.
