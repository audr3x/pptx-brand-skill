I made your two changes and rebuilt the PowerPoint: `evals/runs/auto/T09-fix-one-slide/deck.pptx`. The outline is a copy of the fixture at `evals/runs/auto/T09-fix-one-slide/outline.yaml`. The fixture itself is unchanged.

A diff against the fixture shows exactly three changed lines:
- **Slide 3** title: "Working agreements" is now "What the workshop covers".
- **Slide 3** last bullet: "Leave the footer band clear" is now "Agree owners for each next step". The other four bullets are unchanged.
- **Slide 6** (chart, "Sample volume"): Requests for April is now 25 (it was 22). Completed is unchanged at 9, 14, 13, 19.

Everything else is exactly as it was, including the speaker notes on every slide. The check passed with no warnings, and readback confirmed all 47 outline items are on the 7 slides. In the render, the April Requests column is now the tallest bar, and the value axis now goes up to 30.

Note: the first rebuild only picked up the chart change, because of a file-timing slip on my side. I caught it in the readback, applied the slide 3 edit, and rebuilt. The deck in the folder now has all three changes.
