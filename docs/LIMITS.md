# What the builders refuse, warn about, and cannot do

`scripts/check_outline.py` and both builders share one set of outline rules (`scripts/outline_rules.py`). An outline either builds the same way in both, or both stop with the same plain message. This page lists what those rules catch and what is still up to you.

The list comes from an adversarial test set in `evals/adversarial/` (24 hostile outlines: overlong text, wrong types, broken YAML, huge tables, odd charts, missing images, and so on). Run it with `python3 evals/adversarial/run.py`. The current report is `evals/adversarial/report.md`.

## The check stops the build (error)

Fix these before building. Neither builder will run until they are fixed.

| Problem | Message points you to |
| --- | --- |
| Invalid YAML or JSON | The line and column, and a hint to quote text that contains `:` or `,` |
| No top-level `slides` list, or a slide that is not a mapping | The outline shape (`- layout: content`) |
| Unknown layout name | The list of layout names that work |
| A field neither builder reads (for example `colour`, `bullet`) | The field name |
| `yes`, `no`, `true`, or `false` as text | Quote it, YAML turns it into a true/false value |
| Chart without categories, with a different number of values than categories, or with values that are not numbers | The series and value |
| Pie chart with a negative value | Pie charts cannot show negatives; use a column chart |
| Table without `headers` | Add `headers` |
| Image that is missing, not a picture file, or a web link | The path. Download web images into the repository first |

## The check warns, and the build goes ahead

The builder still runs, but the slide will not look the way the outline reads. Tell the person about each of these.

| Warning | What happens on the slide | What to do |
| --- | --- | --- |
| Title longer than the layout holds (about 60 characters on the cover, 42 on content, table, and chart slides, 45 on half-width layouts) | The title wraps into the content below | Shorten it, one line that states the point |
| Section eyebrow over 40 characters | It runs into the title | Shorten it |
| More than 6 bullets (sub-bullets count) | Only the first 6 are kept | Split into two slides |
| More than 3 two-column items | Only the first 3 are kept | Split into two slides |
| More than about 6 table rows | Rows past the bottom of the slide are cut off | Split the table across slides |
| More than 6 table columns | Text gets very small | Drop or merge columns |
| More than 5 chart series | Colors repeat and the legend gets crowded | Keep the series that matter |
| More than about 12 chart categories | Axis labels get crowded | Group categories |
| A field the layout does not draw (for example `subtitle` on a content slide) | That text is dropped | Move it to a field the layout draws |
| Both `bullets` and `body`, or both `items` and `right` | Only `bullets` (or `items`) is shown | Merge them |
| Text with commas inside `{...}` that was not quoted | YAML splits it into extra keys that are dropped | Quote the text |
| Table rows written as mappings with keys that are not headers | Those cells are dropped | Match the keys to `headers` |
| `TODO` left in the outline | `TODO` prints on the slide | Fill in the real fact, or remove the line |
| Cover slide not first, or more than one cover | Builds as written | Check the order |
| A slide with no content | An empty layout | Remove the slide or add content |

## Google Slides only

These warnings appear with `--target slides` (the default checks both targets).

| Limit | Why | What to do |
| --- | --- | --- |
| Every chart is drawn as clustered columns, from shapes | The Slides API cannot create a native chart without a linked Sheet | Use PowerPoint for pie, line, or bar charts, or add a Sheets chart by hand |
| Chart bars are not editable data | Same reason | Rebuild the chart slide after changing numbers |
| `image` on photo and intro layouts is ignored | Picture placeholders cannot be filled through the API from a local file | Insert the photo by hand (Insert > Image) |
| Speaker `notes` are not written | Builder scope | Paste notes by hand, or use PowerPoint |
| Intro layouts fill only `title` | Builder scope | Type name, role, and company by hand |
| Nested bullets show at one level | Builder scope | Flatten the list, or indent by hand |
| Bullet dots follow the text size, so they look larger than in PowerPoint | The Slides API has no setting for the dot size | Click one dot (Slides selects all dots in that list) and lower the size, or pick a smaller style in Format > Bullets and numbering |

## Layout limits in both builders

- `photos` (3-photos) fills only the first photo slot.
- `photo-right` has a title and a photo, no bullets. Put the bullets on the next slide.
- Colors, fonts, sizes, positions, backgrounds, animations, and slide numbers come from the template. The outline has no fields for them, and fields that try (for example `color`) stop the build.

## Requests the outline cannot hold

When someone asks for one of these, the deck prompting skill (`.cursor/skills/workday-deck-prompting`) explains the limit and offers the nearest supported option before building. See also [PROMPTING.md](PROMPTING.md).
