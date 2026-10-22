The Adatum steering committee deck is built: `evals/runs/claude-opus-5.5/T06-overstuffed-pptx/deck.pptx`, 7 slides. All 12 points and all 10 milestones are in it, word for word. The template holds about 6 bullets and 6 table rows per slide, so I spread the content over more slides instead of cutting anything. The outline (`outline.yaml`) passed the check with no warnings. Previews are in `render/`.

What I changed to make it fit:

- **Title.** "Adatum workforce planning program status update for the steering committee, October 2026" is 85 characters. The cover holds about 60 before the title runs into the subtitle. I split it into the title "Adatum workforce planning program", the subtitle "Status update for the steering committee", and the date "October 2026". Every word is still on the cover. The title wraps to two lines, which fits.
- **12 points split over 3 slides.** I grouped them by theme:
  - "Progress so far" (5): headcount plan, scenario modeling, training at 85%, dashboard draft, change champions.
  - "Budget and open issues" (5): budget 4% under plan, contractor costs not yet included, 3 business units on spreadsheets, data quality in 2 legacy HR systems, two open roles. I put the contractor costs line right after the budget line so the 4% is read with that caveat.
  - "Coming up" (2): integration testing starts November 3, next steering meeting December 2.
- **Milestones split into 2 tables of 5 rows.** A single 10-row table would run off the bottom of the slide. The first table, "Milestones: kickoff to integration test", has the 4 Done milestones and Integration test (Next). The second, "Milestones: user testing to program close", has the 5 Planned milestones.

Slide order: cover, the 3 content slides, the 2 milestone tables, then the Workday closing slide with "Thank you". You didn't give a caption, so tell me if you want something else there.

Questions:

1. The milestone dates have no years. Go live on January 12 and program close on March 6 are presumably 2027. Should I add the years?
2. Does "Contractor costs are not yet included" refer to the budget figure? If it does, I can merge it into one bullet: "Budget is 4% under plan, before contractor costs".
3. Do you prefer a different grouping, or a different slide order, for example the milestones before the open issues?

The preview PNGs use a substitute font for body text because Archivo Light isn't installed on the render machine. PowerPoint will use Archivo Light if it is installed.
