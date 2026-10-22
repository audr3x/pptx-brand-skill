I have prepared the Google Slides request batches for the Woodgrove Bank manager training kickoff presentation using the `workday-google-slides` skill and cover option C.

### What was built

Because Google Slides is not connected in this session, the API batch requests are saved in `slides/`:
- `slides/creates.json`: 5 `createSlide` requests matching Workday layouts.
- `slides/fills.json` (split into `fills-01.json`, `fills-02.json`, and `fills-03.json` in chunks of 40): 112 fill requests.
- `preview.pptx` and rendered slide PNGs in `render/` for previewing.

### Slide structure

1. **Title slide**: "Manager training kickoff", subtitle "Woodgrove Bank people leaders", date "April 8, 2027".
2. **Agenda slide**: "Agenda", with 4 bullets (Why we are training managers, The three tracks, Schedule, How to sign up).
3. **The three tracks**: "The three tracks" on the 1/2_Headline layout, giving one-line descriptions for Coaching basics, Performance conversations, and Leading through change.
4. **Schedule table**: "Schedule", displaying a 3x3 table with headers `Track`, `Format`, and `Weeks`.
5. **Closing slide**: Bumper slide featuring "Thank you" under the Workday smile.

### Resolution of conflicting instructions

1. **Slide count vs. additional tracks slide**:
   - The initial prompt requested "exactly 4 slides: cover, agenda, schedule table, closing", but subsequently asked to "Also add a slide that describes each of the three tracks in one line". To preserve all requested track descriptions without overloading the agenda or table, a dedicated 1/2_Headline slide was created, resulting in a 5-slide deck.
2. **Date selection**:
   - The initial prompt suggested "March 2027", but was superseded by the subsequent instruction: "the kickoff session itself is on April 8, 2027, so use that date". The cover date has been set to "April 8, 2027".

### Cover option C and application instructions

- The cover is set to flat Ballpoint (`#0057AE`) with Paper typography and layout smile. To add `cover-gradient.png` manually: choose **Insert > Image > Drive**, size to 10.00 x 5.625 in at 0, 0, choose **Arrange > Order > Send to Back**, and change text color to Ink (`#0F2E66`).
- Apply `creates.json` first, run `read_presentation`, and then apply `fills-01.json`, `fills-02.json`, and `fills-03.json` in order.
