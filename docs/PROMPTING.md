# Prompting guide: Workday decks in Cursor

How to ask Cursor for a Workday deck with the `workday-pptx` (PowerPoint) and `workday-google-slides` (Google Slides) skills, and get it right the first time.

Setup comes first: [GETTING_STARTED.md](../GETTING_STARTED.md). Brand rules: [BRAND.md](../BRAND.md).

## How a prompt becomes a deck

1. You describe the deck in chat.
2. Cursor writes an **outline** (a short YAML file, like [examples/outline.yaml](../examples/outline.yaml)).
3. A builder turns the outline into slides: `scripts/build_deck.py` for PowerPoint, `scripts/build_slides.py` for Google Slides.
4. Cursor reads back the text that is actually on the slides (`scripts/readback.py`), fixes anything that did not make it, and then tells you what the deck holds.

The builders only read the fields listed below. Colors, fonts, the cover, the logo, and the footer come from the Workday template, so you never need to ask for them. Anything the outline cannot express (a custom color, a moved box, an animation) will not appear in the deck, however you phrase the prompt.

The most reliable way to work: ask for the outline first, read it, then ask Cursor to build.

## What Cursor must not do, and how it checks

These rules are in all three skills. Where a script can enforce them, it does.

| Rule | How it is checked |
| --- | --- |
| Ask first when the request has no real content (numbers, names, dates, rows). A draft gets `TODO` for every gap | Skills; the gate warns on every `TODO` left in the outline |
| Never infer or invent a date, number, name, or quote. "Next month" or "our Q3 review" is not a cover date | `check_outline.py --prompt <your request saved to a file>` fails on a date that is not in it and warns on a figure; `build_deck.py` and `build_slides.py` take the same `--prompt` and refuse the date |
| Leave out figures you mark as old, a typo, or confidential | Skills; say it plainly in the prompt ("last quarter's 48% stays out") |
| When two instructions conflict (exactly 4 slides, then a fifth topic; two dates), ask or pick one and say which | Skills |
| Quote text that contains `: ` (`- "Risk: audit freeze"`) | The gate warns, and keeps the text instead of dropping it |
| Read back the visible slide text after every build and fix drops before reporting | `scripts/readback.py <outline> <deck.pptx or fills.json>` lists every title, bullet, item, cell, and chart label missing from the slides and exits 1 |
| Look hardest at titles that wrap and the first bullet under each title | The gate warns on long titles; the render shows collisions |
| The final message claims only what readback confirms: slide count, what each slide holds, every `TODO` left, warnings that change what you see, anything cut or changed | Skills; the eval harness scores this (`evals/RUBRIC.md`, truthful) |

## What to put in a prompt

| Include | Example |
| --- | --- |
| The skill and the target | "Use the workday-pptx skill" or "Use the workday-google-slides skill" |
| Audience and goal | "For the HR leadership team. Goal: approve the Q3 rollout plan." |
| Length | "8 slides including cover and closing" |
| The slide plan, one line per slide, with a layout | "3: content, Working agreements, 5 bullets" |
| Real content | Paste the bullets, numbers, table rows, and names. Do not ask Cursor to make up figures |
| Cover details | Title, subtitle, date |
| Where the file goes | "Save to decks/q3-rollout.yaml and decks/q3-rollout.pptx" |
| For Google Slides: the cover image option | "Cover option B, URL https://..." or "Cover option C (no image)" |

## Layouts and the fields each one reads

Use these `layout` names in the outline and in your prompt.

| `layout` | Use it for | Fields | Limits |
| --- | --- | --- | --- |
| `title` | Cover | `title`, `subtitle`, `date` | One per deck, first slide |
| `section` | Divider / agenda break | `eyebrow` (small caps line), `title` | Short statement, about 8 words |
| `content` | Bullets | `title`, `bullets` (or `body` for one paragraph) | 6 bullets at most. The builders cut the rest |
| `two-column` | Three steps or pillars | `title`, `items` (each has `title` and `body`) | 3 items at most |
| `table` | Comparisons, timelines | `title`, `headers`, `rows` | About 6 rows. Split longer tables |
| `chart` | One simple chart | `title`, `chart.type`, `chart.categories`, `chart.series` (each has `name` and `values`) | Numbers only, one value per category |
| `closing` | Last slide | `title` (shown as a caption under the logo) | Optional caption |
| `intro` | Introduce a person | `name`, `role`, `company`, `image` | PowerPoint fills all four. Google Slides fills `title` only |
| `photo-right` | One photo with a title | `title`, `image` | No body area. Bullets are dropped |
| `photos` | Photo layout | `title`, `image` | Only the first of the three photo slots is filled |
| `blank` | Last resort | none | Avoid. Pick a real layout |

Every slide also accepts `notes` (speaker notes) and `footer` (overrides the deck footer). The deck itself takes `title`, `subtitle`, `date`, `author`, `subject`, and `footer` (default `Workday Confidential`).

### What differs between PowerPoint and Google Slides

| Feature | PowerPoint | Google Slides |
| --- | --- | --- |
| Chart types | `column`, `bar`, `line`, `pie` as native, editable charts | Always clustered columns, drawn as shapes with a value axis and gridlines. Not editable as data |
| `image` on `intro`, `photo-right`, `photos` | Placed in the photo slot | Ignored. Insert the photo by hand (Insert > Image) |
| `notes` | Written to speaker notes | Not written |
| `intro` name, role, company | Filled | Only `title` is filled |
| Cover gradient | Always present | Needs a cover image option (A or B), otherwise flat Ballpoint (option C) |

If you need a line, bar, or pie chart, a photo, or speaker notes, use PowerPoint, or plan to add them by hand in Google Slides.

## Images

- **Cover and logo.** Automatic. Do not mention them in the prompt, and do not ask for the Workday logo on other slides. In Google Slides the cover gradient depends on the cover image option in [GETTING_STARTED.md](../GETTING_STARTED.md).
- **Photos.** Put the file in the repository, for example under `examples/images/` or your own `decks/images/`, and give the path from the repository root: `image: decks/images/jordan.jpg`. PNG or JPEG. The photo slot crops to fit, so leave space around faces.
- **Where photos go.** Only `intro`, `photo-right`, and `photos` have a photo slot. An `image` on any other layout is ignored.
- **Google Slides.** The builder does not upload photos. Build the deck, then Insert > Image > Drive on the slide. Private Drive files work for this.
- **Not supported.** Screenshots or diagrams on content slides, background photos, icons, and logos of other companies. Ask for a separate slide you finish by hand instead.

## Charts and tables

- Give the numbers. "Requests per month: Jan 12, Feb 18, Mar 15, Apr 22" becomes `categories: [Jan, Feb, Mar, Apr]` and `values: [12, 18, 15, 22]`.
- Every series needs one value per category. Up to about 4 series stays readable. Colors are fixed: Water Cooler, Lunch Break, Ballpoint, Blue Sky, Ink.
- No data labels, axis titles, or units on the axis. Put the unit in the slide title ("Requests per month").
- Tables: give the header row and each row. Short cells (a few words). About 6 rows per slide. Ask for two slides rather than a long table.

## Formatting you can and cannot ask for

You can ask for: the layout per slide, the words, bullet order, nested bullets (PowerPoint only; Google Slides shows them at one level), the footer text, speaker notes (PowerPoint).

Nested bullets in the outline look like this (sub-bullets count toward the 6):

```yaml
slides:
  - layout: content
    title: Open risks have owners
    bullets:
      - text: Data quality in two regions
        children:
          - Owner named, fix due November
      - Manager training capacity
```

The template decides, and prompts cannot change: colors, fonts, font sizes, positions, the cover, the logo, the section rail, the footer position, slide size (16:9), bullets style, and table and chart colors. Do not ask for slide numbers, animations, transitions, custom backgrounds, or bold words inside a bullet. Those are not in the outline.

## Tone

- Titles: sentence case, one line (about 40 characters), say the point ("Adoption doubled in Q2"), not the topic ("Adoption").
- Bullets: one idea each, start with a verb or the key noun, no ending periods, under about 12 words.
- Plain language. Real numbers and names. No filler ("leverage", "synergy", "best-in-class").
- One idea per slide. If a slide needs a second title, it is two slides.

## Copy-paste prompts

Replace the angle-bracket parts. Each prompt is checked against what the builders support.

### 1. PowerPoint from a brief (outline first)

```text
Use the workday-pptx skill. Draft an outline only, do not build yet.
Audience: <who>. Goal: <decision or takeaway>.
Cover: title "<title>", subtitle "<subtitle>", date "<Month YYYY>".
Slides:
2 section: eyebrow "Agenda", title "<statement>"
3 content: "<title>", bullets: <paste up to 6>
4 two-column: "<title>", 3 items with a short title and one-sentence body: <paste>
5 table: "<title>", headers <a, b, c>, rows: <paste>
6 chart (column): "<title with unit>", categories <...>, series "<name>" <values>
7 closing: "Thank you"
Save to decks/<name>.yaml and run python3 scripts/check_outline.py on it. Show me the outline and any warnings.
```

Then:

```text
Looks good. Build decks/<name>.yaml with the workday-pptx skill to decks/<name>.pptx, run scripts/readback.py on it, and render PNGs so I can check every slide.
```

### 2. PowerPoint from an outline you already have

```text
Use the workday-pptx skill. Build examples/outline.yaml to decks/planning-workshop.pptx. Run check_outline.py first and stop if it reports errors. Then render PNGs and tell me if any slide breaks a BRAND.md rule.
```

### 3. Google Slides, cover from a public URL (option B)

```text
Use the workday-google-slides skill. Drive and Slides are connected. I imported assets/template.pptx with convertToGoogleFormat; the file ID is <id>.
Build decks/<name>.yaml on that file: creates first, then fills chunked at 40, each chunk's requests array sent inline and in order.
Cover option B: --cover-image-url <public https URL of cover-gradient.png>. Do not place the smile, the template has it.
Read the deck back and check it against STEPS.md section 5.
```

### 4. Google Slides, no cover image (option C)

```text
Use the workday-google-slides skill on presentation <id> (imported Workday template).
Build examples/outline.yaml with cover option C (no image options): creates, then fills chunked at 40, requests sent inline in order.
After it is done, tell me the exact steps to add cover-gradient.png by hand and switch the title, subtitle, and date to Ink.
```

### 5. Fix one slide

```text
In decks/<name>.yaml change slide 4 only: title "<new title>", keep the items, shorten each body to one sentence. Run check_outline.py, rebuild the PowerPoint, and show me slide 4.
```

For Google Slides the builder always writes the whole deck. Either build again on a fresh copy of the template, or ask:

```text
On presentation <id>, slide wd_s4 only: replace the text of wd_s4_title with "<new title>" using update_presentation (deleteText then insertText, keep the existing style). Do not touch other slides.
```

### 6. Turn notes into a deck

```text
Use the workday-pptx skill. Here are my notes: <paste>. Propose a 6 to 8 slide outline using only these layouts: title, section, content, two-column, table, chart, closing. Use only facts from my notes; mark anything missing as TODO instead of inventing it. Save my notes to decks/<name>-notes.md and the outline to decks/<name>.yaml, and run check_outline.py with --prompt decks/<name>-notes.md.
```

## Example outline

A complete outline that uses every common layout. It passes `scripts/check_outline.py` and builds with both builders.

```yaml
title: Q3 rollout plan
subtitle: HR leadership review
date: October 2026
footer: Workday Confidential
slides:
  - layout: title
    title: Q3 rollout plan
    subtitle: HR leadership review
    date: October 2026

  - layout: section
    eyebrow: Agenda
    title: Where we are and what we need from you

  - layout: content
    title: Pilot results are ready for rollout
    bullets:
      - 3 pilot teams live since July
      - Time to approve requests down from 4 days to 1
      - Support tickets flat after week two
      - Two open risks, both with owners
    notes: Lead with the approval time. That is the number leadership asked about.

  - layout: two-column
    title: Rollout in three steps
    items:
      - title: Prepare
        body: Train managers and confirm data owners in each region.
      - title: Launch
        body: Turn on the new flow for all teams in two waves.
      - title: Review
        body: Check adoption at 30 days and close the pilot.

  - layout: table
    title: Wave plan
    headers: [Wave, Teams, Start]
    rows:
      - [1, Americas, November]
      - [2, EMEA and APJ, January]

  - layout: chart
    title: Requests approved per month
    chart:
      type: column
      categories: [July, August, September]
      series:
        - name: Pilot teams
          values: [140, 210, 260]

  - layout: closing
    title: Decision needed today
```

A PowerPoint-only outline with a photo and a line chart (Google Slides would ignore the photo and draw the chart as columns):

```yaml
title: Team update
slides:
  - layout: photo-right
    title: Meet the program team
    image: examples/images/sample-photo.png
  - layout: intro
    name: Jordan Lee
    role: Program lead
    company: Workday
    image: examples/images/sample-photo.png
  - layout: chart
    title: Weekly active users (thousands)
    chart:
      type: line
      categories: [W1, W2, W3, W4]
      series:
        - name: Users
          values: [1.2, 1.8, 2.1, 2.6]
```

## Anti-patterns

| Instead of | Ask for |
| --- | --- |
| "Make a nice deck about Q3" | Audience, goal, slide count, and a line per slide with a layout |
| "Add some stats" | The actual numbers, with their source |
| "Make the title orange" / "use our blue" | Nothing. Colors come from the template |
| "Put a photo next to these bullets" | `photo-right` (title and photo) followed by a `content` slide |
| "10 bullets on this slide" | Two `content` slides, 5 bullets each |
| "A pie chart" in Google Slides | PowerPoint, or a column chart, or a Sheets chart you add by hand |
| "Add speaker notes" in Google Slides | PowerPoint, or type the notes in Slides by hand |
| "Add our logo to every slide" | Nothing. The cover and closing slides carry the logo |
| "A 3-photo collage" | `photos` gives one photo; add the other two by hand |
| "Fix it" after a bad slide | Name the slide number, the field, and the new text |
| Pasting a confidential customer deck as a style reference | The skill and BRAND.md. Do not copy sentences from reference decks |

Every warning the check gives, and every limit of the builders, is listed in [LIMITS.md](LIMITS.md).

## Checklist before you send the prompt

- [ ] Skill named, and target chosen (PowerPoint or Google Slides)
- [ ] Audience, goal, and slide count stated
- [ ] A layout from the table for every slide
- [ ] Real content pasted. Nothing left for Cursor to invent
- [ ] 6 bullets or fewer per slide, 3 items per two-column slide, about 6 table rows
- [ ] Chart: type, categories, and one number per category per series
- [ ] Photos only on `intro`, `photo-right`, or `photos`, with a path in the repository
- [ ] Google Slides: cover option (A, B, or C) stated, and no request for photos, notes, or non-column charts
- [ ] Cover date given, or you expect a `TODO` in its place
- [ ] Asked Cursor to run `scripts/check_outline.py`, read back the built slides with `scripts/readback.py`, and show you the slides when done
