I made the three changes and rebuilt the 6 slide PowerPoint: `evals/runs/claude-opus-5.5/T14-fix-traps-pptx/deck.pptx`, with PNGs in `render/`. I copied the fixture to `outline.yaml` in the run folder and left the fixture itself untouched.

What changed (a diff against `evals/tasks/fixtures/T14-outline.yaml` shows only these three edits):

1. **Open risks (slide 4):** added "Owner: Dana Reyes, review on May 6" as the last bullet, after "Open enrollment window cannot move". I quoted it in the outline. Without quotes, YAML reads the "Owner: ..." text as a key and value instead of a bullet. The slide now has 4 bullets.
2. **What employees will see (slide 2):** "Employees recieve a guided checklist in Workday" now reads "Employees receive a guided checklist in Workday". Nothing else on that slide changed.
3. **Service requests by month (slide 5):** Completed for April went from 58 to 59. Requests and every other month are unchanged.

What I deliberately left alone:

- **The cover date still reads June 2026**, as you asked. Remember to send me the new date when you're ready.
- Everything else: slide order (cover, what employees will see, the Status section, open risks, chart, closing), all other wording, and the closing "Thank you" slide.

The outline check passed with no warnings, and the readback found all 33 outline items on the slides, including the new bullet, the corrected spelling, and the April value of 59. In the render, the new bullet sits under the first three with no wrapping, and the April Completed bar sits just below the April Requests bar (61).
