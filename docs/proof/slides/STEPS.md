# Apply the worked example in Google Slides

These steps use the JSON in this folder and the plugins (or `gws`). You need a Workday Google account. The machine that built these files cannot reach your Drive.

`update_presentation` takes the `requests` array only. Do not send `phase`, `note`, or `chrome`. With the Google Slides plugin, put the array **inline** in the call. A file path or an attached JSON file reaches the plugin as a plain string, not an array, and the call fails. That is why the fills are split into chunks of about 40 requests.

The checked-in fill chunks have **no images** (option C in `GETTING_STARTED.md`). They never contain placeholder image IDs, so you can send them as they are. Rebuild with a real cover ID or public URL only if you want the gradient added for you.

## 0. One-time setup

1. Sign in to the Google Drive and Google Slides plugins (or run `gws auth login -s drive,slides`).
2. Convert `assets/template.pptx` to Google Slides:
   - Drive plugin: upload with `convertToGoogleFormat=true`, or
   - Drive UI: upload the PPTX, then File > Open with Google Slides.
3. Copy the new file ID. That is `WORKDAY_SLIDES_TEMPLATE_ID`.
4. **First run:** you can build on this imported file. Copying it is optional.

The imported Title and Bumper layouts already carry the white smile. You never upload or place the smile for this template.

### Cover image: pick one

- **A. Drive, Anyone with the link.** Upload `assets/logos/cover-gradient.png`, share it in the **Drive UI** as Anyone with the link: Viewer (the Cursor Drive connector cannot create that share), and save the ID as `WORKDAY_COVER_IMAGE_ID`.
- **B. Public URL.** If your org only allows "Anyone in my org", Slides cannot fetch the Drive file. Host `cover-gradient.png` in a separate small **public** GitHub repo or any public static host, and use that URL with `--cover-image-url`. A raw URL from this private repo returns 404. The builder checks the URL and drops a private GitHub raw URL with a warning.
- **C. No image.** Send the checked-in chunks as they are. Add the gradient by hand afterwards (step 6).

From a machine with `gws`:

```bash
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws
python3 scripts/build_slides.py --upload-assets --backend gws -o workday-slide-assets.json
```

If `--upload-assets` cannot share (org policy), it keeps the IDs and tells you to use option B or C.

## 1. Optional copy

Skip this on a first run if you are filling the imported file.

Drive plugin: `copy_file` on `WORKDAY_SLIDES_TEMPLATE_ID` with name `Planning workshop`.

`gws`:

```bash
gws drive files copy \
  --params '{"fileId": "<WORKDAY_SLIDES_TEMPLATE_ID>"}' \
  --json '{"name": "Planning workshop"}'
```

Use the copy ID as the deck from here on. Keep the imported file unused if you want a clean template later.

## 2. Read the file

`read_presentation` (or `gws slides presentations get`) on the imported file or the copy. Save the JSON as `get.json`.

A clean PPTX import has **no leftover slides**. The `slides` list is empty. There is nothing to delete. Skip any "delete every slide" step.

If you started from a finished deck that already has pages, delete those `objectId` values with `deleteObject` before you send creates.

Keep the `layouts` list. You need it to resolve names.

## 3. Send creates.json

Rebuild so layout IDs are real. The commands below write to `out/slides/`, which git ignores, so a live run does not overwrite the checked-in reference files in this folder:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json \
  -o out/slides/creates.json
```

Send only the `requests` array, inline, with `update_presentation` on the same file. Keep `objectId` values `wd_s1` through `wd_s7`.

If a request still has `layoutName`, match `layouts[].layoutProperties.displayName` (strip spaces, ignore case) and put `layoutId` in `slideLayoutReference`.

## 4. Send fills (chunked)

Save a fresh `read_presentation` as `get.json` after the create batch. Rebuild fills with `--presentation`:

```bash
# Option C (no image), same as the checked-in chunks
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json --chunk 40 -o out/slides/fills.json

# Option A
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --chunk 40 -o out/slides/fills.json

# Option B
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --cover-image-url "https://raw.githubusercontent.com/your-org/workday-slide-assets/main/cover-gradient.png" \
  --chunk 40 -o out/slides/fills.json
```

That writes `fills.json` plus `fills-01.json`, `fills-02.json`, and so on (about 40 requests each; the worked example has 6 chunks). Send the `requests` array from **each chunk, in order**, inline, to `update_presentation`.

## 5. Check

`read_presentation` again. Open `https://docs.google.com/presentation/d/<file-id>/edit`.

With a cover image (option A or B):

- Title slide: blue to cream to gold wash, bold navy (Ink) title, navy subtitle and date, one white smile top left.

With no image (option C, the checked-in chunks):

- Title slide: flat Ballpoint blue, bold white (Paper) title, white subtitle and date, one white smile top left from the layout.

Every option:

- Section slide: gold/teal rail on the left, Ink eyebrow and statement, footer to the right of the rail (x 3.32 in).
- Content: Ink bullets with space between them.
- Two-column, table, and chart: Ink on Paper, footer at 0.50 in. The chart has a value axis with tick numbers and light gridlines behind the columns.
- Closing: Ink field, one centered smile from the layout, Paper caption.

Two smiles on a slide means the smile was placed on top of the layout's own lockup. Delete the extra one, and do not pass `--place-smile` with the imported template.

## 6. Optional: add the gradient by hand (option C)

Insert > Image > Drive works with private files.

1. On the title slide, insert `cover-gradient.png`.
2. Format options > Size and rotation: clear "Lock aspect ratio", width 10 in, height 5.625 in (25.4 x 14.29 cm). Position X 0, Y 0.
3. Arrange > Order > Send to back.
4. Set the title, subtitle, and date to Ink: Text color > Custom, `0F2E66`.
