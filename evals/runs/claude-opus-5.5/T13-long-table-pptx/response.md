I built the Northwind Traders go-live readiness deck at `evals/runs/claude-opus-5.5/T13-long-table-pptx/deck.pptx`. It has 5 slides, and all 14 sites are in it. The readback found all 91 outline items (every site, country, date, status, and lead), and I rendered and checked every slide.

A table on this layout holds about 6 rows before rows run off the bottom of the slide. A single 14-row table would have cut sites off, so I split the schedule across three table slides by country. They are in your original order, with the same five columns (Site, Country, Go-live, Status, Lead):

1. Cover: "Go-live readiness by site", subtitle "Northwind Traders deployment wave 2".
2. "France and Italy sites": Lyon, Marseille, Turin (At risk), and Milan, going live Feb 2 to Feb 9.
3. "Spain and Portugal sites": Seville, Valencia (Blocked), Porto, and Braga, going live Feb 16 to Feb 23.
4. "Belgium, Netherlands, and Austria sites": Ghent (At risk), Antwerp, Utrecht, Eindhoven, Graz (Blocked), and Linz, going live Mar 2 to Mar 16.
5. Closing: "Thank you" under the Workday logo. That caption is my addition, since you did not give one.

The outline check passed with no warnings. No site, value, or name was changed or invented.

Two notes:
- **No cover date.** You did not give one, so the cover has no date line. Tell me the date if you want one.
- **Status is plain text.** The template does not color table cells, so At risk and Blocked look the same as Ready. If you want the 2 blocked and 2 at-risk sites to stand out, I can add a content slide that lists them.
