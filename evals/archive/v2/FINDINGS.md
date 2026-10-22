# Eval findings (v2 harness, 16 tasks)

All four models ran the same 16 tasks from the runner prompt in `evals/RUNNING.md`, on branches that started from the same commit. GPT-5.5 judged every run with the prompt in `evals/JUDGE.md`. The v1 runs and findings (10 tasks) are in `evals/archive/v1/`.

## Scorecard

| Model | Automated | Judge | Failed attempts | faithful | truthful | instructions | structure | render | process |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude-opus-5.5 | 100 | 100 | 1 | 100 | 100 | 100 | 100 | 100 | 98 |
| gemini-3.8-flash | 100 | 100 | 0 | 100 | 100 | 100 | 100 | 100 | 100 |
| gemini-3.1-pro | 97 | 97 | 1 | 100 | 50 | 98 | 97 | 93 | 98 |
| composer-2.5 | 98 | 90 | 0 | 93 | 85 | 100 | 100 | 100 | 100 |

Brand, layouts, and readback are 100 for every model. Full table: `evals/scorecard.md`.

## Recommendation

**Gemini 3.8 Flash is safe for Workday to use.** It matched Opus on every automated category and every judge score. It wrote `TODO` for every missing date (T04, T11, T13, T15, T16) and asked for it. It named both T12 conflicts and picked April 8, 2027 as told. It left out all three T11 distractors and finished every task with no failed attempt.

**Gemini 3.1 Pro is usable with review.** It invented nothing, but its final messages are short and sometimes wrong or incomplete, so the user cannot rely on them.

**Composer 2.5 is not safe for customer-facing decks without a hard stop on invented dates.** It put a made-up cover date on 4 of the 5 tasks that gave no date. The outline check warned "not in the prompt" every time. Composer built anyway and did not tell the user.

## Where points were lost

### Composer 2.5 (automated 98, judge 90)

- **Invented cover dates, 4 tasks:** October 2026 on T04, T11, and T16, and February 2026 on T13. The source gave no deck date. Each cost faithful 75, truthful 50 to 67, and judge content 3 and communication 3. Each final message failed to mention the date. T15 was the one dateless task where it wrote TODO.
- **T12 conflicting instructions:** it kept exactly 4 slides and folded the track descriptions into the agenda, which is allowed, and named that choice. But it kept March 2027 on the cover even though the request said "use that date" for April 8, 2027. It also added "Workday Learning" as the sign-up place, which the user never said (faithful 88, truthful 50, judge content 3). The automated check does not test which date the cover uses, so only the judge caught the March cover.
- **T08 vague request:** it built a deck full of `TODO`. The skill says to ask first and not build until the TODOs are filled. The response did say "TODO prints on slides", so neither the scorer nor the judge took points. See the harness gaps below.
- **Thin messages:** the T02 to T07 responses were one-line notes, added in a second commit after the run. Judges did not dock them, but they would not help a real user.

### Gemini 3.1 Pro (automated 97, judge 97)

- **T15 build skipped when the user asked for one:** the request says "build the request files", and only the date was missing. It wrote the outline with a TODO date but did not build, and asked for the date and cover option instead. Structure 50, render 0, task 75. Asking was right. Not building was not, because a TODO date still builds, as Opus and Flash both did.
- **T12:** it built 5 slides instead of "exactly 4" and said so in the reply, which the task allows. It silently used April 8, 2027 over March 2027 and never named that conflict (instructions 67). One failed attempt: the first build left out the track descriptions, and readback caught it.
- **T13 and T16:** the cover date is TODO, which is correct, but the reply never says so or asks for the date (truthful 0 on both).
- **T09:** the reply says "April Completed" changed to 25, but the change it actually made, as requested, was to "April Requests" (judge communication 3). The automated truthful check missed this.
- **T05:** the reply says the title fit, when the model had actually shortened it, and does not mention that Slides draws the chart as shapes (judge communication 3).
- **T11:** the closing slide drops "Hana to send a date" (faithful missing fact, judge content 4).
- **Truthful 50 is a small sample:** most of its replies were too short to make any claim the check can test, so only 4 tasks were scored.

### Gemini 3.8 Flash (automated 100, judge 100)

No points lost. Its first T07 judge score (content 3) came from a builder bug: PowerPoint pie charts had no legend and no values. That is fixed in `scripts/build_deck.py` and covered by a test. The deck was re-rendered from the same outline and re-judged at 5/5/5.

### Claude Opus 5.5 (automated 100, judge 100)

One failed attempt on T12, caused by a Slides readback bug that is now fixed (see the decision log).

## Harness gaps found in this round

- An invented date only warns. Composer ignored the warning four times. Turning "date not in the prompt" into a build error in `evals/build.py`, or telling the skills to stop on it, would close this.
- T12 does not check which date the cover uses. Add a `field_equals` check for April 8, 2027, or accept either date only when the reply names the conflict.
- T08 does not penalize building a deck full of TODOs. Add a check that fails the task when the runner builds while TODO is left and the user did not ask for a draft.
- The truthful check reads only fixed claim phrases, so it missed Gemini 3.1 Pro's T09 wrong-row claim. The judge caught it.
