# Cheaper model eval findings

Generated after merging:

- `eval-run/composer-2.5`
- `eval-run/gemini-3.1-pro`
- `eval-run/gemini-3.8-flash`

Baseline: `claude-opus-5.5`, judged with GPT-5.5.

## Scorecard

| Model | Tasks run | Automated | Judge | Failed attempts | Structure | Brand | Layouts | Faithful | Instructions | Render | Process |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude-opus-5.5 | 10/10 | 100 | 99 | 0 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| composer-2.5 | 10/10 | 100 | 98 | 0 | 100 | 100 | 100 | 99 | 100 | 100 | 100 |
| gemini-3.1-pro | 10/10 | 100 | 98 | 0 | 100 | 100 | 100 | 99 | 100 | 100 | 100 |
| gemini-3.8-flash | 10/10 | 99 | 95 | 0 | 100 | 100 | 100 | 96 | 100 | 100 | 100 |

## Where the cheaper models lost points

### Composer 2.5

- **T04, notes to deck.** Automated faithfulness lost 12 points on this task because the deck introduced `October 2026`, a number/date not present in the notes. Judge score was 75 for the task: visual 5, content 4, communication 3. The slide deck is clean and otherwise faithful, but the final response says "Nothing was invented," which is false because the cover date was inferred.
- **T05, variance Slides.** It took one extra successful build attempt to shorten the title, but process stayed at 100 because there were no failed attempts. The final deck and message were fine.

Everything else was clean.

### Gemini 3.1 Pro

- **T04, notes to deck.** Automated faithfulness flagged a missing `Brazil` fact. The rendered deck confirms the issue: slide 4 shows only the budget bullet, while the Brazil ERP and January audit-freeze risk bullets are not visible. Judge score was 75 for the task: visual 5, content 4, communication 3. The response says the risks are included, so the final message overstates what was actually on the slides.
- **T05, variance Slides.** The chart title wraps to two lines. It is still clean and the response warns about it, so no score loss.

Everything else was clean.

### Gemini 3.8 Flash

- **T04, notes to deck.** Automated faithfulness lost 12 points because the deck introduced `November 2026`, a date not present in the notes. Judge score was 75 for the task: visual 5, content 4, communication 3. The response presents that date as part of the built deck instead of asking for it.
- **T08, vague ask.** Automated faithfulness lost 25 points because the skeleton outline introduced `October 2026` even though the user gave no date. Judge score was 75 for the task: visual null, content 4, communication 4. The response correctly asks for real facts and the Q3 date range, but the outline itself still contains an inferred date.
- **T05, variance Slides.** The chart title wraps to two lines. It is clean and disclosed, so no score loss.

Everything else was clean.

## Ceiling effect

The automated harness was too easy for the stronger cheap models:

- All three cheaper models got 100 in structure, brand, layouts, instructions, render, and process.
- Composer 2.5 and Gemini 3.1 Pro both reached 100 automated overall after rounding, with only small faithfulness issues.
- The judge found only one real task-level issue for Composer 2.5 and Gemini 3.1 Pro, and two for Gemini 3.8 Flash.

The harness still found useful differences, but the ceiling is high. The next version should add harder checks:

1. Score visible text only for every PowerPoint task, not just the generated deck text. The Gemini 3.1 T04 issue slipped through the automated scorer because the outline had the missing risks.
2. Add a no-date-if-not-provided check for all tasks generated from notes or vague asks.
3. Add a task where a long first bullet can hide later bullets, then require the runner to compare rendered PNGs to the outline.
4. Add a task where the correct answer is to stop and ask rather than build, and score "built a TODO skeleton" separately from "asked first."
5. Add response-truthfulness checks: do not claim "nothing invented" or "all facts included" unless a visible-slide comparison passes.

## Recommendation

Use **Composer 2.5** as the default cheaper model for routine Workday skill runs where a human reviews the output before sending. It matched Gemini 3.1 Pro on total score, but its only meaningful miss was an inferred cover date; it did not visibly drop requested slide content.

Use **Gemini 3.1 Pro** as an acceptable fallback with the same guardrails. It was strong overall, but the T04 hidden-content issue is more concerning than Composer's date inference because the final message claimed risks were included when they were not visible.

Use **Gemini 3.8 Flash** only for low-risk outline drafts or first passes. It was fast and mostly faithful, but it inferred dates twice, including on the vague request where the right behavior was to leave every missing fact as TODO or ask first.

Recommended guardrails and prompt tweaks for all cheaper-model runners:

1. **No inferred dates.** If the prompt does not give a date, use `TODO date` or ask. Never use the current month or year.
2. **Visible-slide readback.** After building, compare each rendered PNG with the outline: every bullet, table row, and chart fact must be visible.
3. **Truthful final message.** Do not say "nothing invented," "all facts included," or "no warnings" unless the outline check and visible-slide readback support that claim.
4. **Ambiguous prompt rule.** For vague asks, write a TODO outline and questions, but do not build a final deck until facts arrive unless the user explicitly asks for a skeleton.
5. **Long-text caution.** If a title or first bullet wraps, inspect the rest of the text box to make sure later bullets did not disappear.

With those guardrails, Composer 2.5 is safe for most internal draft generation and builder operation. Keep Opus 5.5 or another high-capability model for customer-facing decks with messy notes, missing facts, or no human review before delivery.
