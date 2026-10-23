# Eval findings (v3: v2 harness with stricter checks, 16 tasks)

This round added four stricter checks, then reran Opus 5.5, Composer 2.5, and Gemini 3.1 Pro on all 16 tasks with the runner prompt in `evals/RUNNING.md`. Each runner was a fresh agent on the same model as its v2 runner. GPT-5.5 judged every run with the prompt in `evals/JUDGE.md`. Gemini 3.8 Flash was not rerun, because that model was not available to the agent that launched the runners. Its v2 run, scored with the new checks, is shown for comparison. The v2 runs, scorecards, and findings are in `evals/archive/v2/`. The v1 runs are in `evals/archive/v1/`.

## What changed in the harness

- **An invented date fails the build.** With `--prompt`, `check_outline.py` now reports a date that is not in the user's text as an error, not a warning. `build_deck.py` and `build_slides.py` take the same `--prompt` and refuse to build it, and `evals/build.py` passes the prompt to all three. Run on the 64 v2 outlines, the new error caught exactly Composer's 4 invented cover dates and nothing else.
- **T12 checks the cover date.** The cover must say April 8, 2027, the date the request says to use.
- **T08 penalizes a TODO-only deck.** Building a deck while the outline still has `TODO`, when the user gave no facts and did not ask for a draft, fails a check.
- **The truthful category checks specific claims against the deck.** A chart or table value named by category and series ("April Completed is now 25"), a slide count ("the 7 slide deck"), "everything is included", and a claim that a deck was built when nothing was built. On the v2 runs it caught Gemini 3.1 Pro's T09 claim and its T11 "Everything is included" with no false positives on the other runs.
- **Builder fix found by this round's judge:** on every two-series PowerPoint chart the legend sat on top of the last bars and hid one swatch. It now sits below the plot. All v3 runs were rebuilt from the same outlines (attempts not counted) and the four chart tasks (T03, T09, T14, T16) were re-judged for every model.

## Scorecard

Automated and judge scores are 0 to 100, with one decimal so close scores are not hidden by rounding. "v2 re-scored" is the earlier run scored with the new checks, so the difference between the columns is the new run, not the new checks.

| Model | v2 automated (as reported) | v2 re-scored | v3 automated | v2 judge | v3 judge | v3 failed attempts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| claude-opus-5.5 | 100 | 99.8 | 99.8 | 100 | 99.0 | 1 |
| gemini-3.8-flash | 100 | 100.0 | not rerun | 100 | not rerun | |
| composer-2.5 | 98 | 97.5 | 99.5 | 90.1 | 99.0 | 0 |
| gemini-3.1-pro | 97 | 95.9 | 99.5 | 96.9 | 93.2 | 0 |

Brand, layouts, readback, structure, and render are 100 for every v3 run. Full table: `evals/scorecard.md`. Per-task v2 tables: `evals/archive/v2/scorecard-rescored.md`.

## Recommendation

**Use Claude Opus 5.5 or Gemini 3.8 Flash.** Opus lost nothing on content or replies in either round. Flash had a clean v2 run under every check, including the new ones.

**Composer 2.5 improved but still needs review.** It invented no dates this time and put April 8, 2027 on the T12 cover. It still built a deck full of `TODO` on the vague T08 request instead of asking first. In v2 it invented 4 cover dates; the build now refuses those, so that failure can no longer reach a deck when `--prompt` is used.

**Gemini 3.1 Pro still drops content and overstates its replies.** On T11 it again left out "Hana to send a date" and then told the user "Everything is included and nothing was invented." It also built a `TODO` deck on T08.

## Where points were lost (v3)

### Claude Opus 5.5 (automated 99.8, judge 99.0)

- **T09:** one failed attempt. It started the build before its chart edit was saved. The second build passed (process 75).
- **T07 judge visual 3:** slide 3 shows the empty photo placeholder. Google Slides cannot insert the requested local photo, and Opus said in its reply that the user has to add it by hand. This is a builder limit, not a model error.

### Composer 2.5 (automated 99.5, judge 99.0)

- **T08 vague request:** it built a 5-slide deck full of `TODO` (instructions 67). Its reply does ask for the missing facts. The judge gave this 5/5/5, so only the new automated check takes the point.
- **T06:** the cover title is 88 characters, so the gate warned it will wrap. The reply lists the "continued" slides but does not use any phrase the spec looks for ("split", "two slides", "across"), so instructions 60. The reply does describe the split, so this point is partly a strict phrase match.
- **T16 judge content 4, communication 4:** it added a closing slide the user did not ask for and still said nothing was invented.

### Gemini 3.1 Pro (automated 99.5, judge 93.2)

- **T11:** the deck leaves out "Hana to send a date" (faithful 95), and the reply says "Everything is included" (truthful 75, judge content 3, communication 3).
- **T08 vague request:** it built a deck with a `TODO` title and bullets (instructions 67, judge visual 3).
- **T12 judge content 4:** it built 5 slides against "exactly 4". It said so in the reply, which the spec allows.
- **TODO dates on the cover (T13, T15, T16):** the judge took visual points for a visible `TODO` date on Gemini's covers (T16 visual 3) but not for the same `TODO` on Opus's covers. Writing `TODO` is correct when no date was given, so treat these judge points as noise.

## Remaining harness limits

- The judge is not fully consistent: the same `TODO` cover date or the same chart render scored differently across models. Compare the automated categories first and read the judge notes behind any score under 5.
- `response_mentions` checks fixed phrases, so a reply that explains a split in other words can lose the point (Composer T06).
- The claim check only tests claims it can tie to the outline. A wrong claim about wording or layout still needs the judge.
- Gemini 3.8 Flash should be rerun on this harness when an agent on that model is available, using the runner prompt in `evals/RUNNING.md`.
