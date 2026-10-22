# Eval rubric

The eval measures how well a model drives the Workday deck skills from a plain request to a finished deck. Every model gets the same 16 tasks (`evals/tasks/`), the same tools, and the same scorer. Expected answers live in `evals/specs/`, which the runner is told not to open.

## Tasks

| Task | Target | Level | What it tests |
| --- | --- | --- | --- |
| T01-kickoff-pptx | PowerPoint | easy | Follows a slide-by-slide brief exactly |
| T02-training-slides | Google Slides | easy | Same, for the Slides batches, with no image |
| T03-qbr-pptx | PowerPoint | medium | Table and two-series chart with exact numbers |
| T04-notes-to-deck-pptx | PowerPoint | medium | Turns messy notes into a deck without inventing facts |
| T05-variance-slides | Google Slides | medium | Chart with negative values |
| T06-overstuffed-pptx | PowerPoint | hard | 12 bullets, a 10-row table, and an overlong title: must split and shorten while keeping every point |
| T07-unsupported-slides | Google Slides | hard | Pie chart, speaker notes, photo, and orange titles: must adapt and tell the user what Slides cannot do |
| T08-vague-ask | PowerPoint | ambiguous | No facts at all: must ask or mark TODO, never invent numbers |
| T09-fix-one-slide | PowerPoint | medium | Edits two fields and leaves everything else alone |
| T10-people-photo-pptx | PowerPoint | medium | Intro and photo layouts with a local image |
| T11-distractor-notes-pptx | PowerPoint | hard | Dense notes with last quarter's figures, a corrected typo, and confidential numbers that must stay out |
| T12-conflicting-slides | Google Slides | hard | "Exactly 4 slides" then a fifth topic, and two cover dates: must resolve and name both conflicts |
| T13-long-table-pptx | PowerPoint | hard | A 14-row table that must be split with every row kept |
| T14-fix-traps-pptx | PowerPoint | hard | Three edits with traps: a new bullet containing `: `, a chart month present in two series, a slide named by title, and a stale date to leave alone |
| T15-missing-date-slides | Google Slides | hard | Asks for a cover date but never gives one ("next month") |
| T16-negative-series-pptx | PowerPoint | hard | Three series, six categories, negatives and decimals, exact values |

## Automated categories (0 to 1 each, `evals/score.py`)

| Category | How it is measured |
| --- | --- |
| structure | The final outline passes `check_outline.py` for the task's target with no errors, and the build artifacts exist (`deck.pptx`, or `slides/creates.json` and `slides/fills.json`) |
| brand | PowerPoint: every slide uses a template layout, only Archivo, Archivo Light, or Arial, only brand colors (text, fills, table cells, chart series), and a Workday Confidential footer where the layout has one. Google Slides: no request targets an object before it exists, only Archivo at weights 300, 400, or 700, only brand colors, every bulleted box gets `NEVER_COLLAPSE` spacing, no placeholder or private image URLs, and the fill chunks add up to the full batch with at most 50 requests each. Score is the share of these checks that pass |
| layouts | Slide count is in the expected range, and the layouts match the expected sequence (or include the required layouts) |
| faithful | Share of required facts from the prompt that appear in the built deck, minus penalties for what the prompt never gave (`scripts/provenance.py`): 0.5 per date (month, quarter, fiscal year, or year), 0.25 per figure (single-digit counts are ignored), 0.25 per capitalized name, and 0.5 per distractor the spec forbids (last quarter's number, a typo the user corrected, confidential data). Text marked `TODO` is a declared placeholder and is not penalized here |
| readback | Share of the outline's drawn text (titles, bullets, items, cells, chart labels, and PowerPoint chart values) that is on the built slides, read back by `scripts/readback.py` |
| truthful | Claims in `response.md` held against the readback and the attempt log: "everything is included" needs readback and facts complete; "nothing was invented" needs no dates, figures, names, or distractors from outside the prompt; "verified" or "read back" needs a passing readback; "no warnings" needs a clean last check. Also fails when text is missing and the response does not say so, when `TODO` is on the slides and the response does not say so, and when something not in the prompt is on the slides and the response does not flag that item by name. Not applicable when the response makes none of these claims and none of these conditions hold |
| instructions | Task-specific checks from the spec (exact field values, chart values, table rows, at most 6 bullets per slide, no title warnings, unchanged slides, response mentions limits or conflicts, a cover date left as TODO when none was given, TODO or a question when facts are missing) plus no em or en dashes in deck text |
| render | LibreOffice renders one PNG per outline slide |
| process | Starts at 1 and loses 0.25 for each failed build attempt logged by `evals/build.py`; halved if any tool printed a Python traceback; 0 if the runner never used the wrapper |

The automated score is the mean of the categories that apply. On T08 the build is optional, so structure, render, and process only count if the runner built something.

For Google Slides tasks, the text checks read the `insertText` requests in the fills batch, and chart values come from the outline (Slides draws them as bar heights). The PNGs are a PowerPoint built from the same outline, because the Slides batches cannot be rendered without a live presentation.

Runs scored before these checks existed (10 tasks, seven categories) are in `evals/archive/v1/`, with the original scorecard and the same runs scored by the current scorer.

## Judge categories (1 to 5 each, `evals/JUDGE.md`)

One fixed judge model scores every model's runs from the PNGs, the outline, and the runner's final message:

- **visual**: text that overflows, overlaps, or is cut off; crowded slides; empty placeholders; wrong layout for the content.
- **content**: faithful to the request, sensible splitting and shortening, nothing important missing, nothing invented.
- **communication**: the final message tells the user about every warning and limit that changes what they see, asks for missing facts, and does not claim things that did not happen.

The judge score is the mean of the three, mapped to 0 to 100. It is reported next to the automated score, not mixed into it.

## Reading the scorecard

`evals/scorecard.md` has a summary row per model and a row per task with notes on what failed. Compare models category by category: a cheaper model that loses points only on process (more retries) is a different risk from one that loses points on faithful (invented numbers).
