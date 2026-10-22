# Eval findings (v2 harness, 16 tasks)

The v1 runs and findings (10 tasks, before the readback and truthful checks) are in `evals/archive/v1/`. Re-scoring those runs under the v2 scorer moved the cheaper models off the ceiling: Composer 2.5 99, Gemini 3.1 Pro 99, Gemini 3.8 Flash 94 automated (see `evals/archive/v1/scorecard-rescored.md`). The drops come from the new truthful and faithful checks, which catch the invented cover dates and "nothing was invented" claims.

## Baseline: claude-opus-5.5, judged with GPT-5.5

| Model | Tasks run | Automated | Judge | Failed attempts | faithful | readback | truthful | process |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude-opus-5.5 | 16/16 | 100 | 100 | 1 | 100 | 100 | 100 | 98 |

Full table: `evals/scorecard.md`.

- **The six new tasks (T11 to T16) all passed.** On T11 the deck left out the outdated 48%, the $1.24M typo, and the confidential headcount. T12 used 5 slides and April 8, 2027, and the response named both conflicts. T13 split the 14 sites across 3 tables. T14 made exactly the three edits. T15 kept the cover date as TODO and asked for it. T16 had all 18 values exact, including the negatives.
- **The one failed attempt (T12) was a harness bug, not a model error.** For Google Slides, readback counted slides by the last slide that receives text. A closing slide with no caption gets no text requests, so readback reported a missing slide. This is fixed in `scripts/readback.py` and covered by a test. The runner worked around it by adding a "Thank you" caption. The attempt stays in the log, so T12 process is 75 and the overall process score is 98.
- **The judge is at its ceiling too.** GPT-5.5 gave 5/5/5 on every task. Use the automated scores to compare models. Treat the judge as a check for visual breakage.

## Headroom

Opus 5.5 still scores 100, but the harness can now tell a good deck from a bad one. In a sensitivity check, deliberately flawed hand-written answers to T11 to T16 scored 86, 96, 92, 81, 78, and 89. Each flaw was a realistic slip: an invented date, a distractor number, a dropped table row, a wrong chart value, or a response claiming more than the readback shows. Under the v2 scorer, the v1 cheaper-model runs already lose 1 to 6 points. Expect larger gaps on the new tasks.
