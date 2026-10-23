I made the two changes you asked for and rebuilt the 7 slide PowerPoint: `evals/runs/claude-opus-5.5/T09-fix-one-slide/deck.pptx`, with PNGs in `render/`. I copied the fixture to `outline.yaml` in the run folder and didn't touch the fixture itself.

A diff against `evals/tasks/fixtures/T09-outline.yaml` shows exactly three changed lines:

- **Slide 3, title:** "Working agreements" is now "What the workshop covers".
- **Slide 3, last bullet:** "Leave the footer band clear" is now "Agree owners for each next step". The other 4 bullets are unchanged and in the same order.
- **Slide 6 (chart), Requests for April:** 22 is now 25. Completed for April stays 19, and every other value is the same.

Every other slide, field, and speaker note is exactly as it was. The outline check passed with no warnings, and the readback found all 47 outline items on the slides, including the new title, the new bullet, and the April value of 25. In the render, the April Requests bar is now the tallest on the chart. The value axis now runs to 30 to fit it, and nothing else moved.
