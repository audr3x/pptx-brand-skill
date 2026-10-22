# Running the eval under another model

The eval runs the same 10 deck requests through a model and scores what it builds. The baseline (`evals/runs/claude-opus-5.5/`) was produced by a fresh agent that saw only the runner prompt below, the same way a cheaper model should be run.

## 1. Start an agent on the model you want to measure

Use a cloud agent (or a local Cursor chat) on this repository, on the branch that contains `evals/`. Pick the model, then paste the runner prompt from step 2 with `<MODEL>` replaced by a folder name:

| Model | Folder name |
| --- | --- |
| Claude Opus 5.5 (baseline) | `claude-opus-5.5` |
| Composer 2.5 | `composer-2.5` |
| Gemini 3.1 Pro | `gemini-3.1-pro` |
| Gemini 3.8 Flash | `gemini-3.8-flash` |

Run one agent per model. Each agent writes only to its own folder, so runs can be merged later without conflicts.

## 2. Runner prompt (paste as is, after replacing `<MODEL>`)

```text
You are running the Workday deck skill eval. Your model folder name is <MODEL>.

Setup, once:
- pip install -r requirements.txt (in a virtual environment if pip refuses).
- LibreOffice and pdftoppm must be installed: run `soffice --version` and `pdftoppm -v`.
  If either is missing: sudo apt-get update && sudo apt-get install -y libreoffice-impress poppler-utils

Then do the 10 tasks in evals/tasks/, in order (T01 to T10). For each task <TASK> (the file
name without .md):
1. Read evals/tasks/<TASK>.md. Treat it as a request from a Workday user in Cursor. Use the
   repository skills in .cursor/skills/ (workday-pptx, workday-google-slides,
   workday-deck-prompting) and the docs they link to, the same way you would for a real user.
2. Write the outline to evals/runs/<MODEL>/<TASK>/outline.yaml.
3. Check and build ONLY with:
     python3 evals/build.py --model <MODEL> --task <TASK>
   It runs the outline check and the right builder, renders PNGs to render/, and logs each
   attempt. Do not run check_outline.py, build_deck.py, or build_slides.py directly. If it
   fails, fix the outline and run it again. When it succeeds, open the PNGs and fix anything
   that looks wrong, then build again.
4. Google Slides is not connected in this session. For Slides tasks the build writes the
   request batches. Do not call any Google, Drive, or Slides tool.
5. Write evals/runs/<MODEL>/<TASK>/response.md: the message you would send the user at the
   end. Say what you built, every warning or limit that changes what they will see, and any
   question you need answered. The user is not available to reply in this session: if facts
   are missing, ask in response.md and write TODO in the outline. Never invent facts or
   numbers.

Rules:
- Do not open evals/specs/, evals/score.py, evals/checks.py, evals/RUBRIC.md, evals/JUDGE.md,
  evals/adversarial/, evals/scorecard.md, or other folders under evals/runs/.
- Do not edit anything outside evals/runs/<MODEL>/. Do not change scripts, skills, docs,
  templates, or fixtures.
- Work on each task until you are satisfied, as you would for a real user. Each failed build
  attempt is counted, so check your outline before building.

When all 10 are done, commit evals/runs/<MODEL>/ with the message "Eval run: <MODEL>" and push
your branch. In your final message, list the tasks and one line on anything you could not do.
```

## 3. Judge and score

On any machine with the repository and all run folders (merge the runners' branches or copy their `evals/runs/<MODEL>/` folders):

1. Write the judge packet: `python3 evals/score.py --packet <MODEL>`.
2. Start an agent on the judge model (GPT-5.5 for the baseline; keep it the same for every model) and give it the judge prompt in `evals/JUDGE.md`, with `<MODEL>` replaced.
3. Score everything: `python3 evals/score.py`. This rewrites `evals/scorecard.md` with one summary row per model and per-task notes.

To score one model without the judge, skip steps 1 and 2: `python3 evals/score.py --model <MODEL>`.

## What the scores mean

See `evals/RUBRIC.md`. In short: seven automated categories (structure, brand, layouts, faithfulness, instruction following, render, process) and a separate judge score for visual quality, content, and communication. Compare models category by category, not only by the total.

## Rerunning a single task

Delete `evals/runs/<MODEL>/<TASK>/` and run that task again with the same prompt, telling the agent which task to do. The attempt log starts over with the folder.

## Changing the tasks

The tasks and specs are fixed so runs stay comparable. If a task or spec has to change, rerun every model on it, and note the change in `evals/decision-log.tsv`.
