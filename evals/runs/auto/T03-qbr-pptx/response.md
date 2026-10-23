I built the 5-slide Fabrikam QBR deck: `evals/runs/auto/T03-qbr-pptx/deck.pptx`. Outline: `outline.yaml`. PNGs of every slide are in `render/`.

Readback confirmed all 47 outline items (titles, table cells, chart labels and values, bullets) are on the slides.

1. **Cover**: "Fabrikam quarterly business review", subtitle "Q3 2026", date "October 2026". The title wraps onto two lines on the cover. It sits clear of the subtitle.
2. **Table**, "Service levels by region": columns Region, Tickets, Resolved in SLA, Satisfaction, and your 5 regions with their values.
3. **Column chart**, "Tickets per quarter (thousands)": Q4 2025 to Q3 2026, with Opened (Water Cooler blue) and Closed (Lunch Break gold) as a native, editable PowerPoint chart. The values axis is 0 to 4 with a legend under the plot.
4. **Content**, "What we will improve next quarter": your 3 bullets.
5. **Closing**: the Workday bumper with no caption.

One check warning: slide 5 "has no content". That is expected, because you asked for a closing slide without a caption, so it shows the Workday logo on Ink only. If you want a line under the logo (for example "Thank you" or "Questions"), tell me the text and I'll rebuild.

The prompt check found no added dates or figures. Everything from your request is included and nothing was invented.
