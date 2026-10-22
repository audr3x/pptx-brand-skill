I have built the PowerPoint presentation for the Adatum steering committee using the `workday-pptx` skill.

### Summary of what was built

The presentation is available at `deck.pptx` with rendered slide PNGs in `render/`:

1. **Title slide**: "Workforce planning program status update", subtitle "Adatum steering committee, October 2026", date "October 2026".
2. **Delivery progress**: "Delivery progress across streams", containing 6 bullets covering headcount plan approval, scenario modeling, recruiting testing, planner training rate, executive dashboard draft, and change champions.
3. **Risks, budget, and staffing**: "Open risks, budget, and staffing", containing 6 bullets covering spreadsheet usage in 3 BUs, legacy data quality, under-plan budget status, contractor costs, open team roles, and the December 2 steering meeting.
4. **Milestones (Part 1)**: "Completed and active milestones", a 5-row table for completed and near-term milestones (Kickoff through Integration test).
5. **Milestones (Part 2)**: "Planned go-live milestones", a 5-row table for upcoming milestones (User testing through Program close).
6. **Closing slide**: Workday Bumper slide featuring "Thank you".

### Preserving all content without truncation

To ensure **every single requested item** was preserved without being cut:
- **Bullet capacity (max 6 per slide)**: The 12 requested points were split into two thematic 6-bullet slides. Putting all 12 on one slide would have caused bullets 7–12 to be dropped by the builder.
- **Table capacity (max 6 rows per slide)**: The 10-row milestone table was split across two 5-row slides. Putting all 10 rows on one slide would have caused rows 7–10 to overflow the bottom margin and obscure the footer.
- **Cover title**: The long title was structured into a clean title and subtitle so it stays within the 60-character limit and renders cleanly without wrapping.

The outline passed `check_outline.py` and readback confirmed all 56 items are present on the slides.
