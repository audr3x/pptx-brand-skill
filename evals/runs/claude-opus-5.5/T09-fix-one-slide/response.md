I copied the fixture to `evals/runs/claude-opus-5.5/T09-fix-one-slide/outline.yaml` and made the three changes. Then I rebuilt the 7 slide deck at `evals/runs/claude-opus-5.5/T09-fix-one-slide/deck.pptx`. The fixture itself is unchanged.

What changed (a `diff` against the fixture shows only these three lines):
- Slide 3 title: "Working agreements" is now "What the workshop covers".
- Slide 3, last bullet: "Leave the footer band clear" is now "Agree owners for each next step". The other four bullets are unchanged.
- Slide 6 chart: the April value for Requests is now 25 (it was 22). Completed is unchanged at 9, 14, 13, 19.

Every other slide, field, and speaker note is exactly as it was. The outline check passed with no warnings, and the readback found all 47 outline items, including the new 25 in the chart data. I rendered all 7 slides. The new title fits on one line, and the April Requests bar now reaches 25.

The first build attempt failed the readback because the chart edit had not been saved yet when the build started. The second build has all three changes and passes.
