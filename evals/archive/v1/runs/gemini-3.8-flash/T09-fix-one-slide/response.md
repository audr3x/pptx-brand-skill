I have updated the presentation based on `evals/tasks/fixtures/T09-outline.yaml` and rebuilt the PowerPoint deck at `deck.pptx`.

### Summary of changes made

1. **Slide 3 (Content)**:
   - Changed title to: "What the workshop covers".
   - Replaced the final bullet with: "Agree owners for each next step".
   - Preserved all other bullets, notes, and layout properties.
2. **Slide 6 (Chart)**:
   - Updated the April value for the "Requests" series to **25** (values are now `[12, 18, 15, 25]`).
   - Left all other categories and the "Completed" series values untouched.
3. **All other slides**: Left completely unchanged (Cover, Section Title, Two-column, Table, and Closing slides).

### Build verification

- Outline verified with `check_outline.py` with zero errors and zero warnings.
- Rebuilt `deck.pptx` (7 slides) from `template.pptx`.
- Rendered visual previews for all slides in `render/`.
