Prepared Google Slides batches for the Litware sales kickoff (cover option C): `creates.json` plus `fills-01.json` through `fills-03.json`.

**Deck (4 slides):** cover, pipeline chart, Meet the team, Thank you.

**Limits (these change what you will see in Slides):**
- **Pie chart:** outline uses `pie`, but the Slides builder draws **clustered columns**, not a pie. Use PowerPoint if you need a true pie, or accept columns / add a Sheets chart by hand.  
- **Speaker notes:** `notes` in the outline apply to **PowerPoint only**; they are not in the Slides fill batches.  
- **Team photo:** `image` on `photo-right` is **ignored** in Slides. Insert `examples/images/sample-photo.png` manually (Insert > Image) beside Meet the team.  
- **Orange titles:** custom title color is not supported; titles stay template Ink.  

Readback passed on visible text in `fills.json`. Preview PNGs use PowerPoint (pie and photo render there). I did not call Google APIs in this session.
