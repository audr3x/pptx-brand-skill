# Judge instructions

Use the same judge model for every model's runs, so scores are comparable. The baseline was judged with GPT-5.5.

1. Write the packet: `python3 evals/score.py --packet <model-folder>`. It lists, per task, the prompt, the outline, the runner's final message, and every rendered slide PNG.
2. Give the judge the prompt below and the packet path.
3. Run `python3 evals/score.py` to fold the judge scores into the scorecard.

## Judge prompt

```text
You are judging Workday-branded slide decks that another model built from a user's request.
Open evals/runs/<MODEL>/judge-packet.md. For every task listed there:

1. Read the user's request (evals/tasks/<task>.md), the outline the model wrote, and the
   model's final message to the user (response.md).
2. Look at every slide PNG listed for the task. Open each image; do not guess from file names.
3. Score three things from 1 to 5:

   visual: 5 = every slide is clean: no text overflowing its box, overlapping other text,
   running off the slide, or cut off; no crowded slide; no empty placeholder; each layout
   suits its content. 3 = one or two visible problems a user would fix by hand.
   1 = several slides are broken or unreadable.

   content: 5 = says what the user asked, with every fact they gave that belongs on a slide,
   nothing invented, sensible splits and short titles where the request was too long.
   3 = a fact is missing or reworded so the meaning changes, or one invented detail.
   1 = large parts missing or invented.

   communication: 5 = the final message tells the user every warning or limit that changes
   what they will see (split slides, dropped fields, things Google Slides cannot do), asks
   for facts that were missing, and claims nothing that did not happen. 3 = misses one
   important limit, or is vague. 1 = misleading, or silent about a major change.

4. Write evals/runs/<MODEL>/<task>/judge.json:
   {"visual": n, "content": n, "communication": n, "notes": "one or two sentences naming the
   specific slide and problem behind any score under 5"}

If a task has no PNGs (for example the model asked questions instead of building), score
visual as null and judge the other two from the outline and the message.

Do not edit anything except the judge.json files. Do not read evals/specs/ or evals/score.py.
Judge each task on its own; do not compare with other models.
```

For Google Slides tasks the PNGs are a PowerPoint built from the same outline. Slides-only differences (all charts as columns, no photos, no speaker notes) are expected and should not cost visual points; whether the model told the user about them counts under communication.
