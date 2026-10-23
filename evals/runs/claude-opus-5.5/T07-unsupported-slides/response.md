I prepared the Google Slides request batches for a 4 slide "Litware sales kickoff" deck. Nothing was sent to Google, because Slides is not connected in this session. Four of the things you asked for are not possible in the Slides build. Here is what I did for each:

1. **Pie chart.** The Google Slides builder draws every chart as clustered columns, made from shapes. It cannot make a pie chart. Slide 2, "Pipeline by segment", shows Enterprise 55, Mid-market 30, and Small business 15 as three columns. If you need a real pie chart, I can build this deck as PowerPoint instead, where pie charts are native and editable. Or you can add a Google Sheets pie chart to the slide by hand.
2. **Speaker notes.** The Slides builder does not write speaker notes. Also, you did not tell me what the notes should say, and I will not make them up. No slide has notes. Send me the notes for each slide. Then you can paste them into Slides, or I can build the deck as PowerPoint, which does write notes.
3. **Team photo.** Slide 3 is the "Meet the team" photo layout, but the Slides API cannot place a local file. The photo slot will be empty. Insert `examples/images/sample-photo.png` by hand: upload it to Drive, then Insert > Image > Drive on slide 3. The PNG preview in `render/` shows the photo because it is rendered from PowerPoint. The Slides deck will not have it.
4. **Orange titles.** I did not do this. Title colors come from the Workday template (Ink navy), and the outline has no field for them. Workday orange is reserved for the logo smile.

What is in the deck:
1. Cover: "Litware sales kickoff", date "February 2027", no subtitle.
2. Chart: "Pipeline by segment", columns as above. You gave no unit, so the title has none. Tell me if these are percent or a currency amount.
3. Photo layout: "Meet the team" (photo to be inserted by hand).
4. Closing: "Thank you" under the Workday logo.

Files in `evals/runs/claude-opus-5.5/T07-unsupported-slides/slides/`: `creates.json` first, then read the presentation, then `fills-01.json`, `fills-02.json`, and `fills-03.json` (82 requests, chunks of 40) in order, each as an inline `requests` array.

The readback found all 9 outline items in the fills batch. The only check warning is the ignored photo. Cover option C means a flat Ballpoint cover with white type and no gradient image.

Questions for you:
- PowerPoint instead, so you get the pie chart, notes, and photo built in? Or keep Google Slides and add them by hand?
- What should the speaker notes say on each slide?
- What unit are the pipeline values in?
