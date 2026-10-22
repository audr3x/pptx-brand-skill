I have created a 7-slide executive presentation for the CFO based on the Tailspin Toys finance planning workshop notes using the `workday-pptx` skill.

### What was built

The presentation was built at `deck.pptx` with rendered slide previews in `render/`:

1. **Title slide**: "Finance planning workshop", subtitle "Tailspin Toys executive readout", date "November 2026".
2. **Current state & targets**: "Targeting a 5-day close by FY27", covering the 9-day close pain point, FY27 5-day target, $380k budget ask, and December steering committee decision.
3. **Workstreams**: "Three agreed workstreams" on a two-column layout highlighting the three agreed owners and streams (Priya for intercompany recon, Marco for standard chart of accounts across the 4 entities, Lena for daily cash dashboard).
4. **Timeline**: "Implementation phases", structured as a clean 3-row timeline table spanning Phase 1 (Nov-Jan), Phase 2 (Feb-Apr), and Phase 3 (May-Jun).
5. **Risks**: "Program risks to manage", capturing the Brazil ERP migration timeline (March) and the January audit freeze.
6. **Next steps**: "Immediate next steps", listing immediate action items for Priya (Nov 14), Marco, and Lena.
7. **Closing slide**: Workday Bumper slide with "Thank you".

### Faithfulness and open questions for the team

- **No invented data**: Every metric ($380k, 9 days to 5 days, 4 entities), name (Priya, Marco, Lena), and milestone comes directly from your notes.
- **Questions to confirm with the team**:
  1. What is the specific calendar date in December for the CFO steering committee decision?
  2. What target dates should be assigned to Marco's controller review and Lena's dashboard mock?
- The outline passed `check_outline.py` with zero errors and zero warnings.
