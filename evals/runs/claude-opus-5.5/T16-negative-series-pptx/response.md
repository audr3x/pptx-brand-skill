I built the 3 slide Proseware workforce planning deck at `evals/runs/claude-opus-5.5/T16-negative-series-pptx/deck.pptx`. The outline check passed with no warnings, the readback found all 34 outline items (every region, quarter, and value), and I rendered and checked every slide.

1. Cover: "Open roles by region", subtitle "Quarterly net change".
2. Column chart, "Net change in open roles by region". It shows your 6 regions, with one series per quarter: Q1 in Water Cooler blue, Q2 in Lunch Break gold, and Q3 in Ballpoint blue. I used your exact values, including the decimals and negatives (for example Nordics Q1 7.25 and APAC Q1 -15). Negative bars hang below the zero line, and the value axis runs from -20 to 15.
3. Content, "Takeaways": your three takeaways as written. I checked them against the data, and each one holds. APAC went -15, -11, then 4. North America went 12, 9, then -6. UK and Ireland went 3, 5.5, then 8.

What you will see on the chart:
- **No value labels on the bars.** The template draws the axis and gridlines only. The exact values (such as -0.8 and -1.75) are stored in the chart data, so you can see them in PowerPoint with Edit Data or by hovering, but they are not printed on the slide.
- **Latin America Q3 is 0**, so that bar is a flat line at zero and looks missing. That is the value you gave, not a dropped bar.
- **No unit on the axis.** The template has no axis titles, and the slide title says what is measured. Tell me if you want the unit in the title, for example "(roles)".

You did not give a cover date, so the cover has none. You also did not ask for a closing slide, so the deck ends on the takeaways. Nothing was invented or cut.
