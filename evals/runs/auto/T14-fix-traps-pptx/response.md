I made your three changes and rebuilt the PowerPoint: `evals/runs/auto/T14-fix-traps-pptx/deck.pptx`. The outline is a copy of the fixture at `evals/runs/auto/T14-fix-traps-pptx/outline.yaml`. The fixture itself is unchanged.

What changed (a diff against the fixture shows exactly these three edits):
1. **Open risks (slide 4)**: added "Owner: Dana Reyes, review on May 6" as the last bullet. The slide now has 4 bullets. I quoted the text in the outline because it contains a colon followed by a space, which YAML would otherwise read as a key and value. The slide shows the full line.
2. **What employees will see (slide 2)**: "Employees recieve a guided checklist in Workday" now reads "Employees **receive** a guided checklist in Workday".
3. **Service requests by month (slide 5)**: Completed for Apr is now 59 (it was 58). Requests is unchanged at 40, 52, 47, 61.

Left exactly as it was:
- **Cover date "June 2026".** You said it's old and you'll update it later, so I didn't touch it. The cover still shows June 2026.
- Every other slide and field: the cover title and subtitle, the "Status" section, the other bullets including "Owner: Sam Patel for carrier files", the Jan to Mar values, and the "Thank you" closing.

The check passed with no warnings, and readback confirmed all 33 outline items are on the 6 slides.
