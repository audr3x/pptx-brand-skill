# Workday PowerPoint brand system

Extracted from the Workday Corporate Template (16:9). Use these tokens only. Do not invent colors, fonts, or chrome.

The reference deck is a corporate template plus color-usage slides, not a customer narrative. This file records the brand system. It does not reproduce any confidential slide copy.

## Canvas

| Token | Value |
| --- | --- |
| Theme name | Workday Corporate Template |
| Color scheme | Workday Color Palette |
| Slide size | 10.00 in x 5.625 in (`9144000` x `5143500` EMU) |
| Aspect | 16:9 widescreen (`screen16x9`) |
| Transition | Medium fade (700 ms) |
| Guides | Dense vertical and horizontal guides in `#A4A3A4` (layout aid only) |

Keep a **0.50 in** content inset on the left and right. Titles sit at **x = 0.50 in, y = 0.41 in**, **9.00 x 0.525 in** on standard content layouts. Do not crowd the footer band below **y = 5.20 in**.

## Color

Official names come from the template's color slides. Hex values match the theme XML.

### Core palette (use this first)

The core palette should cover almost every slide.

| Name | Hex | RGB | Theme slot | Typical use |
| --- | --- | --- | --- | --- |
| After Hours | `#022043` | 2 / 32 / 67 | `lt2` | Darkest navy surface |
| Ink | `#0F2E66` | 15 / 46 / 102 | `dk1` / `tx1` | Titles, body, default text |
| Ballpoint | `#0057AE` | 0 / 87 / 174 | `dk2` / `tx2` / hyperlink | Title-slide fallback fill, links |
| Water Cooler | `#1C98E8` | 28 / 152 / 232 | `accent1` | Primary accent, numbers, chart series 1 |
| Blue Sky | `#9ECFFF` | 158 / 207 / 255 | `accent2` | Light accent, chart series 4 |
| Paper | `#FFFFFF` | 255 / 255 / 255 | `lt1` / `bg1` | Default content background, reverse text |
| Keyboard | `#FCF8E8` | 252 / 248 / 232 | `accent6` | Warm cream surface or cover subhead |
| Highlighter | `#FFF3A8` | 255 / 243 / 168 | `accent5` | Soft yellow highlight |
| Pencil | `#FDE65E` | 253 / 230 / 94 | `accent4` | Yellow accent |
| Lunch Break | `#FEC10B` | 254 / 193 / 11 | `accent3` | Gold accent, chart series 2 |

Theme XML stores Blue Sky as `#9ECFFF`. Some swatches in the color slides use `#9FCFFF`. Prefer `#9ECFFF`.

### Secondary palette (use sparingly)

These colors are documented as occasional accents, not default UI.

| Name | Hex | RGB | Typical use |
| --- | --- | --- | --- |
| Tack | `#6FC9D3` | 111 / 201 / 211 | Teal accent |
| Eraser | `#FFC2FD` | 255 / 194 / 253 | Pink accent |
| Smoothie | `#AB65D0` | 171 / 101 / 208 | Purple accent |
| Happy Hour | `#FD7E00` | 253 / 126 / 0 | Orange accent |
| Thumbtack | `#FC5B05` | 252 / 91 / 5 | Smile-logo orange, strong accent |
| Laptop | `#525D6A` | 82 / 93 / 106 | Dark gray |
| Staple | `#7D8B99` | 125 / 139 / 153 | Footer, muted labels |
| Desk | `#B6C1CC` | 182 / 193 / 204 | Rules, timeline ticks |
| Business Card | `#F1F3F6` | 241 / 243 / 246 | Default shape fill, card surface |

### Surfaces

| Surface | Color | Notes |
| --- | --- | --- |
| Default content slide | Paper `#FFFFFF` | Master background is `bg1` |
| Title slide | Ballpoint `#0057AE` under a full-bleed warm-to-navy gradient | Layout `Title Slide` |
| Bumper / closing | Ink `#0F2E66` | Layout `Bumper Slide` |
| Intro slides | Keyboard / paper glow (`glow-keyboard.svg`) | `Intro_One`, `Intro_Three`, `Intro_Four` |
| Alt content | Paper with a warm paper glow (`glow-paper.svg`) | `Title Only_Alt`, `1/2 Headline_Alt` |
| Default shape | Business Card `#F1F3F6`, no stroke | Theme object default |

### Color combination rules (from the template)

Use the core palette on every slide. Keep secondary colors rare.

Text on filled backgrounds that the template explicitly allows:

| Background | Safe text colors |
| --- | --- |
| After Hours | Paper, Keyboard, Highlighter, Pencil, Lunch Break |
| Ink | Paper, Keyboard, Highlighter, Pencil, Lunch Break, Blue Sky |
| Ballpoint | Paper, Keyboard |
| Water Cooler | Paper |
| Blue Sky | Ink, After Hours |
| Paper | Ballpoint, Ink, After Hours |
| Keyboard | Ballpoint, Ink, After Hours |
| Highlighter | Ink, After Hours |
| Pencil | Ink, After Hours |
| Lunch Break | Ink, After Hours |

Do not put Ink or After Hours on Ballpoint without checking contrast. Do not put Water Cooler text on Highlighter or Pencil. Do not invent a new hex if a named token already exists.

Accessibility: the template's own guidance is to keep strong contrast. Prefer Ink on Paper, Paper on Ink, or Paper on Ballpoint / After Hours.

## Type

### What the theme declares

The theme font scheme is named **Office Classic 2** and points both major and minor Latin to **Arial**. That is the Office theme fallback, not the designed voice.

### What the master actually uses

| Role | Face | Size | Weight | Color |
| --- | --- | --- | --- | --- |
| Cover title | Archivo | 36 pt | Regular (layout), Bold in practice | Theme `tx1` (Ink) |
| Slide title | Archivo | 28 pt | Bold | Ink `#0F2E66` |
| Section title | Archivo | 28 pt (sample also uses 44 pt on a highlight word) | Bold | Ink |
| Subhead | Archivo | 16 pt | Regular | Ink |
| Body | Archivo Light | 18 pt | Regular | Ink |
| Content L1 | Archivo Light | 20 pt | Regular | Ink |
| Content L2 | Archivo Light | 16 pt | Regular | Ink |
| Content L3 | Archivo Light | 14 pt | Regular | Ink |
| Item title | Archivo | 12 to 15 pt | Regular / Bold | Ink |
| Item body | Archivo Light | 10.5 to 13 pt | Regular | Ink |
| Eyebrow | Archivo | 14 pt | Regular | Water Cooler or Ink |
| Footer | Archivo | 8 pt | Regular | Staple `#7D8B99` |
| Date on cover | Archivo | 12 pt | Regular | Ink or Keyboard |

Object defaults also set Archivo 16 pt Ink for new text boxes, and Archivo 16 pt on Business Card shapes.

### Faces listed but not designed as the voice

The package font table lists Archivo, Archivo Light, Arial, Courier New, Lucida Grande, **Proxima Nova**, and Wingdings.

- **Archivo / Archivo Light** are the designed faces. Archivo is SIL Open Font License (Google Fonts). Install it on the authoring machine. Do not silently swap in Calibri or Inter.
- **Arial** is the theme fallback and the bullet-font face.
- **Proxima Nova** is a licensed face. It is listed in document properties and is **not** the theme Latin face. Do not bundle it. If a host machine does not have Archivo, fall back to Arial, not to Proxima Nova.
- Courier New, Lucida Grande, and Wingdings appear only as bullet-character fonts on unused deep list levels.

No `ppt/fonts` part is embedded in the package, so licensed faces cannot be extracted from the file.

If Archivo Light is missing, use Archivo at the same size. Do not synthesize a new family.

## Layouts

One slide master (`slideMaster1`) owns 15 layouts. python-pptx index and XML name:

| Index | Layout name | Intent | Placeholders |
| --- | --- | --- | --- |
| 0 | `Title Slide` | Cover | Center title, subtitle |
| 1 | `Intro_One` | One speaker | Photo, name, title, company, footer |
| 2 | `Intro_Three` | Three speakers | 3 photos + 3 name/title/company stacks, footer |
| 3 | `Intro_Four` | Four speakers | 4 photos + 4 stacks, footer |
| 4 | `Title and Content ` | Body bullets (name has a trailing space) | Title, body, footer |
| 5 | `Title Only` | Title plus freeform body | Title, footer |
| 6 | `Title Only_Alt` | Same, warm glow background | Title, footer |
| 7 | `1/2_Headline` | Left title, right freeform | Title (3.70 x 0.95 in), footer |
| 8 | `1/2 Headline_Alt` | Same, warm glow background | Title, footer |
| 9 | `Section Title` | Section / agenda / divider | Footer only. Title is drawn in the open field |
| 10 | `Layout 1` | Thin left gradient rail | Footer only |
| 11 | `3-Photos` | Three image cards | Title, 3 pictures, footer |
| 12 | `Photo-Right` | Copy left, full-bleed photo right | Title, picture, footer |
| 13 | `Bumper Slide` | Close | None. Centered smile on Ink |
| 14 | `Blank White Background` | Escape hatch | Footer |

Match intent to layout. Do not rebuild chrome on a blank slide when a layout already has it.

### Intent map

| Intent | Layout | How to fill it |
| --- | --- | --- |
| Title / cover | `Title Slide` | Title + subtitle placeholders. Optional date text box at 0.51 in, 4.96 in |
| Section / divider | `Section Title` | Wide left gradient is already on the layout. Add eyebrow + title in the open field starting at x = 3.32 in |
| Content / bullets | `Title and Content ` | Title + body placeholders |
| Two-column | `1/2_Headline` | Title placeholder on the left. Add a right-hand stack of at most three numbered items |
| Table | `Title Only` | Title placeholder. Draw the table in the content well |
| Chart | `Title Only` | Title placeholder. Draw the chart in the content well |
| Closing | `Bumper Slide` | Leave the smile. Optional one-line Paper caption under the mark |
| Intro | `Intro_One` / `_Three` / `_Four` | Name, title, company placeholders |
| Photo story | `Photo-Right` or `3-Photos` | Title + picture placeholders |

### Key geometry (inches)

| Element | x | y | w | h |
| --- | --- | --- | --- | --- |
| Standard title | 0.50 | 0.41 | 9.00 | 0.53 |
| Standard body | 0.50 | 1.34 | 9.00 | 3.74 |
| Cover title | 0.51 | 3.53 | 8.63 | 0.65 |
| Cover subtitle | 0.51 | 4.17 | 8.63 | 0.37 |
| Cover date | 0.51 | 4.96 | 2.48 | 0.30 |
| Cover smile | 0.67 | 0.52 | 1.34 | 0.64 |
| Half-width title | 0.50 | 0.41 | 3.70 | 0.95 |
| Section title field | 3.32 | 1.46 | 5.61 | 2.20 |
| Section eyebrow | 3.32 | 1.08 | 4.34 | 0.41 |
| Photo-right title | 0.50 | 0.41 | 4.58 | 0.95 |
| Photo-right image | 5.81 | 0.00 | 4.19 | 5.63 |
| Bumper smile | 3.39 | 1.79 | 3.22 | 1.52 |
| Footer | 0.03 | 5.27 | 3.38 | 0.30 |
| Thin left rail | 0.00 | 0.00 | 0.36 | 5.63 |
| Wide section rail | 0.00 | 0.00 | 2.74 | 5.63 |

## Bullets

On `Title and Content ` the body list style is:

| Level | Size | Bullet | Indent |
| --- | --- | --- | --- |
| 1 | 20 pt | `•` Arial, Ink | 0.25 in hanging |
| 2 | 16 pt | `‒` (U+2012) Arial, Ink | 0.63 in |
| 3 | 14 pt | Wingdings `§` | 1.00 in |
| 4 | 12 pt | Courier New `o` | 1.31 in |
| 5 | 11 pt | Lucida Grande `◆` | 1.69 in |

The master body placeholder (not the content layout) also shows an older orange bullet `#F38B00`. Prefer the content-layout style: **Ink `•`**. Do not use unicode bullets typed into the run (`•` as characters). Let `python-pptx` / the placeholder list style draw the bullet.

**At most about 6 bullets on a slide.** Prefer 3 to 5. Do not walk past level 2 unless the outline truly needs it.

Paragraph spacing on master body styles is 6 pt before and after. Title line spacing is 90%.

## Tables

Default table style in the package is **Medium Style 2 - Accent 1**.

| Part | Fill | Text | Border |
| --- | --- | --- | --- |
| Header | Water Cooler (`accent1`) | Paper, bold | Paper, 3 pt bottom |
| Body | Water Cooler tint 20% | Ink | Paper, 1 pt |
| Banded row | Water Cooler tint 40% | Ink | Paper, 1 pt |
| First / last column | Water Cooler | Paper, bold | none extra |

When `python-pptx` cannot apply the named style, paint the same tokens by hand:

- Header fill `#1C98E8`, header text Paper 12 pt Archivo Bold
- Body fill Keyboard / Business Card alternate (Keyboard so odd rows do not vanish into Paper), body text Ink 11 pt Archivo Light
- Outer and last-row rules in Desk `#B6C1CC`. No gray Office theme, no black grid

Place tables in the content well: **0.50, 1.34, 9.00 x 3.40 in**, leaving the footer clear.

## Charts

The reference package has **no sample charts**. Style charts from the palette.

| Series | Color |
| --- | --- |
| 1 | Water Cooler `#1C98E8` |
| 2 | Lunch Break `#FEC10B` |
| 3 | Ballpoint `#0057AE` |
| 4 | Blue Sky `#9ECFFF` |
| 5 | Ink `#0F2E66` |

Rules:

- Chart plot area and wall: Paper, no shadow
- Axis and labels: Ink, Archivo Light 10 to 12 pt
- Legend: Ink, Archivo 10 pt
- Gridlines: Desk `#B6C1CC` only, if needed
- No Excel default orange / green / gray
- One chart per slide, with a written title in the title placeholder

## Logos and decorative assets

Extracted to `assets/logos/`. The template already embeds the same files on the layouts that need them. Do not re-place them unless you are drawing on `Blank White Background`.

| File | What it is | Where the template uses it |
| --- | --- | --- |
| `workday-smile.png` | Full lockup: white "workday" wordmark plus orange smile `#FC5B05`. The wordmark is white, so it only reads on dark grounds (title and bumper). | Title Slide (top left), Bumper Slide (center) |
| `gradient-day-crop.svg` | Yellow-to-navy vertical wash (`Day_Crop_5`) | Title Slide full bleed |
| `gradient-day-crop-warm.svg` | Yellow-to-teal wash (`Day_Crop_1`) | Section Title wide rail, Layout 1 thin rail |
| `glow-keyboard.svg` | Cream / gold intro glow (`Night_Glow_on_Keyboard`) | Intro layouts |
| `glow-paper.svg` | White / orange paper glow (`Day_Glow_on_Paper`) | Title Only_Alt, 1/2 Headline_Alt |

The lockup is one PNG. Do not recolor it, do not separate the smile from the wordmark, and do not invent a second mark.

A photo-instruction PNG lived on sample slides only. It is not a logo and is not in this repo.

## Footer and header chrome

- Footer copy: **Workday Confidential**
- 8 pt Archivo, Staple `#7D8B99`, left aligned
- Box: 0.03 in, 5.27 in, 3.375 x 0.30 in
- Master header/footer flags: slide number off, date off, header off (`sldNum="0" hdr="0" dt="0"`)
- Title Slide and Bumper Slide have no footer
- Do not add slide numbers, confidential-classification bars, or extra legal lines unless the brief asks for them

## Spacing and density

- One idea per slide
- Titles stay on one line when possible. The 28 pt title box is 0.53 in tall (about one line) on content layouts, 0.95 in on half-width and photo-right layouts
- 0.30 in or more between stacks
- Do not fill the footer band
- Prefer three numbered items over a wall of bullets on `1/2_Headline`
- Agenda-style stacks in the reference use at most six items

## What you must not do

- Do not pick a hex that is not in this file
- Do not use Calibri, Inter, Roboto, or Proxima Nova as a substitute "modern" stack
- Do not drop the smile onto a Paper content slide as decoration
- Do not rebuild a title slide on `Blank White Background`
- Do not add accent underlines under titles
- Do not use emoji
- Do not ship Lorem ipsum, "Click to edit", or "Insert slide title" in a finished deck

## Could not extract

| Item | Why |
| --- | --- |
| Proxima Nova | Licensed; listed in the package font table only. No embed |
| Archivo font files | Not embedded (`ppt/fonts` is absent). Download from Google Fonts |
| Separate dark-color wordmark | The lockup PNG is white type. It will not read on Paper. |
| Official chart spec | No charts in the reference package |
| Print / notes typography beyond defaults | Notes and handout masters still use Office theme 2 / 3 |
| Exact lockup clear-space spec | Not written in the theme; inferred from title-slide and bumper placement only |
