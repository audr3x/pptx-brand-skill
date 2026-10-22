I prepared the Google Slides request batches for a 4 slide Litware sales kickoff deck with cover option C (no image). Three things you asked for can't be done in Google Slides by this builder, and one can't be done at all. Those are explained below before the details. Nothing was sent to Google, because Slides isn't connected in this session.

**What I couldn't do as asked**

- **Pie chart:** Google Slides draws every chart as clustered columns built from shapes, because the API can't create a native pie chart without a linked Sheet. Slide 2 is a column chart of Enterprise 55, Mid-market 30, and Small business 15. If you need a real pie, I can build this deck as a PowerPoint instead, which supports native pie charts. You could also add a Sheets pie chart to slide 2 by hand.
- **Speaker notes on every slide:** the Slides builder doesn't write speaker notes. You also didn't give me the notes text, and I won't make it up. Send me the notes for each slide and either I'll build a PowerPoint with them, or you can paste them into Slides by hand.
- **Team photo:** slide 3 is the Photo-Right layout titled "Meet the team", but Google Slides ignores the image path, so the photo slot will be empty. After the deck is built, insert `examples/images/sample-photo.png` by hand with Insert > Image on slide 3. A PowerPoint build would place the photo automatically.
- **Orange titles:** I didn't change the title color. The Workday template sets titles to Ink (navy) on every layout, and the outline has no color setting. The orange in the brand is reserved for the logo's smile. Titles stay navy.

**What the batches hold** (readback found all 9 outline items in the fills)

1. Cover: "Litware sales kickoff", February 2027. You didn't give a subtitle, so the cover has none. With option C, the cover is flat Ballpoint blue with white text, not the gradient shown in the `render/` preview PNGs, which come from a PowerPoint build of the same outline.
2. Column chart, "Pipeline by segment": one series called "Pipeline". The request didn't give a unit (percent, dollars, or deal count), so the axis shows plain numbers. Tell me the unit and I'll add it to the title. The bars can't be edited as data in Slides.
3. Photo-Right, "Meet the team": title only, with the photo inserted by hand as described above.
4. Closing: "Thank you".

Files are in `evals/runs/claude-opus-5.5/T07-unsupported-slides/slides/`:

- `creates.json`: send this first.
- `fills-01.json` to `fills-03.json`: 82 requests, chunked at 40. Send them in order, passing each `requests` array inline.

Before sending, replace each `layoutName` in `creates.json` with the matching `layoutId` from your imported Workday template.

**Questions**

1. Would you like this as a PowerPoint instead? That would give you the pie chart, the speaker notes, and the photo placed automatically.
2. What should the speaker notes say on each slide?
3. What unit is the pipeline in?
