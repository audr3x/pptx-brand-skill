# Apply the worked example in Google Slides

These steps use the JSON in this folder and the plugins (or `gws`). You need a Workday Google account. The VM that built these files cannot reach your Drive.

Image IDs are not baked into `fills.json`. After you upload the PNGs, either replace `YOUR_COVER_IMAGE_ID` / `YOUR_SMILE_IMAGE_ID` in a regenerated fills file, or re-run the phase 2 command below with your real IDs.

## 0. One-time assets

1. Sign in to the Google Drive and Google Slides plugins (or run `gws auth login -s drive,slides`).
2. Upload `assets/template.pptx`. Open with Google Slides. Copy the file ID. That is `WORKDAY_SLIDES_TEMPLATE_ID`.
3. Upload `assets/logos/cover-gradient.png` and `assets/logos/workday-smile.png`.
4. Share each PNG as **anyone with the link, Viewer**.
5. Save the two IDs as `WORKDAY_COVER_IMAGE_ID` and `WORKDAY_SMILE_IMAGE_ID`.

Or from a machine with `gws`:

```bash
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws
python3 scripts/build_slides.py --upload-assets --backend gws -o workday-slide-assets.json
```

## 1. Copy the template

Drive plugin: `copy_file` on `WORKDAY_SLIDES_TEMPLATE_ID` with name `Planning workshop`.

`gws`:

```bash
gws drive files copy \
  --params '{"fileId": "<WORKDAY_SLIDES_TEMPLATE_ID>"}' \
  --json '{"name": "Planning workshop"}'
```

Do not edit the template file itself.

## 2. Read the copy and delete leftover slides

`read_presentation` (or `gws slides presentations get`) on the new ID. Save the JSON as `get.json`.

Delete every slide listed under `slides` (those are leftover layout samples or a blank from the import). `batchUpdate` with one `deleteObject` per `objectId`.

Keep the `layouts` list. You need it to resolve names.

## 3. Send creates.json

Open `docs/proof/slides/creates.json`.

If each `createSlide.slideLayoutReference` still has `layoutName`:

- Find the layout whose `layoutProperties.displayName` matches (strip spaces, ignore case).
- Replace `slideLayoutReference` with `{"layoutId": "<that objectId>"}`.

Or rebuild:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json \
  -o docs/proof/slides/creates.json
```

Send the `requests` array with `update_presentation` / `batchUpdate` on the **copy**. Keep `objectId` values `wd_s1` through `wd_s7`.

## 4. Send fills.json

Rebuild fills with your image IDs:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --smile-image-id "$WORKDAY_SMILE_IMAGE_ID" \
  -o docs/proof/slides/fills.json
```

If slide object IDs are not `wd_s1` … `wd_s7`, save a fresh `read_presentation` and add `--presentation get.json`.

Send the `requests` array to the same copy.

## 5. Check

`read_presentation` again. Open `https://docs.google.com/presentation/d/<copy-id>/edit`.

- Title slide: blue to cream to gold wash, navy title and subtitle, white lockup top left.
- Section slide: gold/teal rail on the left, Ink statement.
- Content, two-column, table, and chart: Ink on Paper, footer at 0.50 in.
- Closing: Ink field, centered smile, Paper caption.

If the cover is flat blue, the fill batch did not include `createImage`. Re-run phase 2 with the image IDs and confirm anyone-with-link Viewer.
