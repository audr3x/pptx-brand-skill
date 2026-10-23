Done. I copied `evals/tasks/fixtures/T09-outline.yaml` to `evals/runs/claude-opus-5.5/T09-fix-one-slide/outline.yaml` and made only the changes you asked for. The fixture itself is untouched. The rebuilt PowerPoint is `deck.pptx` in that folder, and the previews are in `render/`.

Compared with the fixture, exactly three lines changed:

- Slide 3 title: "Working agreements" is now "What the workshop covers".
- Slide 3 last bullet: "Leave the footer band clear" is now "Agree owners for each next step". The other 4 bullets are unchanged.
- Slide 6 chart: the April value for Requests is now 25 (it was 22). The Completed series is unchanged. The value axis now runs to 30 so the taller April bar fits.

Everything else is exactly as before: the cover, section, two-column, table, and closing slides, the speaker notes, and the deck settings. The outline check passed with no warnings, and I checked slides 3 and 6 in the render.

Note: the speaker note on slide 3 still reads "Title and Content layout. Bullets use the layout list style." I left it, as you asked. Tell me if you want new notes for the new title.

I built twice. The first build may have started before the April edit was saved, so I rebuilt. The current `deck.pptx` shows 25 for April.
