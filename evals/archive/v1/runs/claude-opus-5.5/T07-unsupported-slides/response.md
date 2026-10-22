The request batches for the 4-slide Litware sales kickoff deck in Google Slides are ready. Google Slides isn't connected here, so nothing was sent. Several of the things you asked for can't be done in Google Slides with this builder. Here is what I did for each one and what you can do instead.

Files in `evals/runs/claude-opus-5.5/T07-unsupported-slides/`: `outline.yaml`, `slides/creates.json` (4 slides), and `slides/fills-01.json` to `fills-03.json` (82 fill requests, chunked at 40; send them in order). `render/` has a PowerPoint preview of the same outline.

Slides:

1. Cover: "Litware sales kickoff", February 2027. There is no subtitle because you didn't give one.
2. Chart: "Pipeline by segment" with Enterprise 55, Mid-market 30, and Small business 15.
3. Photo-right: "Meet the team".
4. Closing: the Workday bumper with "Thank you".

What I could not do as asked:

- **Pie chart.** Google Slides charts from this builder are always clustered columns drawn as shapes. The Slides API can't create a native pie without a linked Sheet. So the segments show as three Water Cooler blue columns, and the numbers can't be edited as data in Slides. If you need a real pie, I can build the deck in PowerPoint, where `pie` is a native, editable chart. Or you can add a Google Sheets pie chart by hand.
- **Speaker notes.** The Slides builder doesn't write speaker notes, and you didn't give me the text, so there are none. I didn't write any for you. Send me the notes and I'll put them in a PowerPoint version, or you can paste them into Slides by hand (View > Show speaker notes).
- **Team photo.** Google Slides can't fill the photo slot from a repository file, so slide 3 has the title "Meet the team" and an empty photo area. To add it, go to Insert > Image, choose `examples/images/sample-photo.png` (upload it to Drive first), and place it in the right-hand half. The `photo-right` layout has no room for bullets. If you want text about the team, give me the names and roles and I'll add a content slide after it. The PowerPoint preview in `render/slide-3.png` shows the photo in place, but the Slides deck will not have it.
- **Orange titles.** I didn't do this. The Workday template sets every slide title to bold Ink navy (`#0F2E66`), and the outline has no color field. Orange is only for the smile in the logo. The titles will stand out through size and weight.
- **Cover option C (no image):** the cover is flat Ballpoint blue with white type and the logo. The gradient in the preview is PowerPoint only. You can add `cover-gradient.png` by hand (Insert > Image > Drive, 10 x 5.625 in at 0, 0, send to back), then set the title and date to Ink.

To apply: import or copy the Workday template in Slides. Send `creates.json`, swapping each `layoutName` for that layout's `objectId` from `presentations.get`. Then send `fills-01.json` through `fills-03.json` in order.

Questions:

1. What unit are 55, 30, and 15: percent of pipeline, USD millions, or a deal count? I left the chart title as "Pipeline by segment". If it is a share, I'll add the unit, for example "Pipeline by segment (%)".
2. Do you want me to switch this deck to PowerPoint, so the pie chart, the photo, and the speaker notes all work?
3. What should the speaker notes say on each slide?
4. Which Slides file should it go on? Send me the presentation ID of your imported Workday template.
