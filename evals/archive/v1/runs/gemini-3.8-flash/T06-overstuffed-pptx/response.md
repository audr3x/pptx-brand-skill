I have built the PowerPoint presentation for the Adatum steering committee using the `workday-pptx` skill.

### What was built

The presentation is available at `deck.pptx` with preview renderings in `render/`:

1. **Title slide**: "Workforce planning program update", subtitle "Adatum steering committee, October 2026", date "October 2026".
2. **Delivery progress**: "Delivery progress across streams", containing 6 bullets covering headcount plan approval, scenario modeling go-live, recruiting testing, planner training rate, dashboard draft, and regional change champions.
3. **Risks, budget, and team**: "Open risks, budget, and staffing", containing 6 bullets covering spreadsheet usage in 3 BUs, legacy data quality, under-plan budget status, unincluded contractor costs, open team roles, and the December 2 steering meeting.
4. **Milestones (Part 1)**: "Completed and active milestones", a 5-row table for completed and in-flight milestones (Kickoff through Integration test).
5. **Milestones (Part 2)**: "Planned go-live milestones", a 5-row table for upcoming milestones (User testing through Program close).
6. **Closing slide**: Bumper slide featuring "Thank you" under the Workday smile.

### Layout translations & limits applied

To ensure **every single requested item** was preserved without being truncated:
- **Bullet capacity (max 6 per slide)**: The 12 requested points were split into two thematic 6-bullet slides. Placing all 12 on one slide would have caused bullets 7–12 to be automatically dropped by the builder.
- **Table capacity (max 6 rows per slide)**: The 10-row milestone table was split across two 5-row slides. Placing all 10 rows on one slide would have caused rows 7–10 to overflow the bottom margin and obscure the footer.
- **Cover title**: The 84-character title was structured into a concise title and subtitle so it stays within the 60-character limit and renders cleanly without wrapping.

The outline passed `check_outline.py` with zero errors and zero warnings.
