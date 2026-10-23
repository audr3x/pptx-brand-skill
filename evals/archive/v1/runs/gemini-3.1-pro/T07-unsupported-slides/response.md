I have prepared the Google Slides request batches for the Litware sales kickoff presentation. 

Since Google Slides is not connected in this session, I generated the request batches (`creates.json` and chunked `fills.json`), which you can apply using `gws` or the Slides API.

There are a few important limitations to note regarding your requests in Google Slides:
- **Pie chart**: The Google Slides builder only supports drawing column charts, so the pipeline chart has been drawn as clustered columns instead of a pie chart. If a pie chart is strictly necessary, I can build this as a PowerPoint deck instead, or you can insert a Sheets chart manually.
- **Speaker notes**: The builder ignores speaker notes in Google Slides. These are only supported in PowerPoint. You will need to add them manually.
- **Photos**: The Google Slides builder ignores image fields, so the team photo (`examples/images/sample-photo.png`) could not be placed automatically. You will need to insert it manually using Insert > Image in Google Slides.
- **Custom colors (orange titles)**: The slide titles follow the fixed Workday brand template (bold navy Ink), so I didn't change them to orange. The template styling is enforced to maintain brand consistency.

Let me know if you would like me to convert this presentation to a PowerPoint file instead, where speaker notes and images are natively supported!