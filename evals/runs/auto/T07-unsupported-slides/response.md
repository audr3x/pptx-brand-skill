I prepared the Google Slides request batches for a 4-slide "Litware sales kickoff" deck, with cover option C. Nothing was sent to Google, because Slides is not connected in this session. But four of the things you asked for can't be done by the Google Slides builder, so this deck is not exactly what you asked for. Details are below.

Files in `evals/runs/auto/T07-unsupported-slides/slides/`: `creates.json` (send first, then `read_presentation`), then `fills-01.json` and onward in order, with the `requests` array inline. Readback on `fills.json` confirmed all 9 outline items are in the batches.

1. **Cover**: "Litware sales kickoff", date "February 2027". You didn't give a subtitle, so the cover has none.
2. **Chart**, "Pipeline by segment": Enterprise 55, Mid-market 30, Small business 15.
3. **Photo-right**, "Meet the team": title on the left, photo slot on the right.
4. **Closing**: the Workday bumper with the caption "Thank you".

What you asked for that this deck does not do:
- **Pie chart: drawn as a column chart.** Google Slides draws every chart as clustered columns built from shapes, which you can't edit as data. If you need a real pie, I can build this deck as a PowerPoint (native, editable pie chart), or you can add a Sheets pie chart by hand in Slides.
- **Speaker notes: not added.** The Slides builder does not write speaker notes, and you didn't give me the note text, so I didn't make any up. If you send the notes for each slide, I can put them in a PowerPoint version, or you can paste them into Slides by hand.
- **Team photo: not placed in Slides.** The builder can't upload a local file to a photo slot, so slide 3 will have the title and an empty photo area. After you apply the batches, use Insert > Image > Drive on slide 3 and place `examples/images/sample-photo.png` on the right half. The PNG preview in `render/` shows the photo only because it comes from a PowerPoint preview.
- **Orange titles: not possible.** Title color is set by the Workday template (Ink navy) and the outline has no color field. Orange (Thumbtack) is reserved for the logo smile, so I kept the brand titles.

Also note: the cover will be flat Ballpoint blue with white text (option C), not the gradient shown in the preview PNG.

Questions:
1. Should I switch this to PowerPoint so you get the pie chart, the photo, and speaker notes? If so, what should each slide's notes say?
2. Are the pipeline values percentages, dollar amounts, or deal counts? I left the unit off the chart title because you didn't say. I'll add it once you confirm.
