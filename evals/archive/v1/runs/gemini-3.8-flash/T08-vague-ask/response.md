I have drafted a preliminary outline structure for the Contoso Q3 business review, but I have not built the deck yet. Under Workday brand and prompting guidelines, we do not invent facts, statistics, or performance numbers.

### Information needed before building

To ensure your presentation is accurate and impactful, please share the following details in your next reply:

1. **Audience & Goal**: Who will be attending from Contoso (e.g., executive leadership, operational management), and what is the primary decision or takeaway desired from this meeting?
2. **Length / Slide Count**: How many slides do you envision (e.g., 5 to 7 slides)?
3. **Specific Q3 Metrics & Stats**: Please share the real figures you would like highlighted, such as:
   - System adoption, active users, or service levels.
   - Any financial, ticket, or delivery metrics.
   - Specific chart categories and values (e.g., monthly volume or quarterly growth).
4. **Key Topics & Milestones**:
   - Major accomplishments achieved in Q3.
   - Key focus areas or priorities for Q4.
   - Any known risks or blockers that need executive support.

### Proposed outline draft

A skeleton outline has been prepared at `outline.yaml` with `TODO` markers for the missing data:

```yaml
title: Contoso Q3 business review
subtitle: "TODO: Add review subtitle"
date: October 2026
footer: Workday Confidential
slides:
  - layout: title
    title: Contoso Q3 business review
    subtitle: "TODO: Add review focus"
    date: October 2026

  - layout: section
    eyebrow: Agenda
    title: "TODO: Add agenda statement"

  - layout: content
    title: "TODO: Add Q3 achievements title"
    bullets:
      - "TODO: Add stat or bullet point"
      - "TODO: Add stat or bullet point"
      - "TODO: Add stat or bullet point"

  - layout: two-column
    title: "TODO: Add strategic priorities"
    items:
      - title: "TODO: Pillar 1"
        body: "TODO: Pillar 1 description"
      - title: "TODO: Pillar 2"
        body: "TODO: Pillar 2 description"
      - title: "TODO: Pillar 3"
        body: "TODO: Pillar 3 description"

  - layout: closing
    title: Thank you
```

Once you provide the metrics and content, I will update the outline, verify it with `check_outline.py`, and build the PowerPoint deck using the Workday Corporate Template.
