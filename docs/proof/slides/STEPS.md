# Apply the worked example in Google Slides

These steps use the JSON in this folder and the plugins (or `gws`). You need a Workday Google account. The VM that built these files cannot reach your Drive.

`update_presentation` takes the `requests` array only. Do not send `phase`, `note`, or `chrome`.

Image IDs are not real Drive IDs in the checked-in files (`YOUR_COVER_IMAGE_ID`). After you upload and share the PNGs, rebuild fills with your IDs.

## 0. One-time assets

1. Sign in to the Google Drive and Google Slides plugins (or run `gws auth login -s drive,slides`).
2. Convert `assets/template.pptx` to Google Slides:
   - Drive plugin: upload with `convertToGoogleFormat=true`, or
   - Drive UI: upload the PPTX, then File > Open with Google Slides.
3. Copy the new file ID. That is `WORKDAY_SLIDES_TEMPLATE_ID`.
4. **First run:** you can build on this imported file. Copying it is optional.
5. Upload `assets/logos/cover-gradient.png` and `assets/logos/workday-smile.png`.
6. In the **Drive UI** (not the connector), share each PNG as **Anyone with the link: Viewer**. The Cursor Google Drive connector cannot create that share.
7. Save the two IDs as `WORKDAY_COVER_IMAGE_ID` and `WORKDAY_SMILE_IMAGE_ID`.

Do not use a GitHub raw URL. This repo is private, so those links 404. `--cover-image-url` will not fix that.

Or from a machine with `gws`:

```bash
python3 scripts/build_slides.py examples/outline.yaml \
  --import-pptx assets/template.pptx --backend gws
python3 scripts/build_slides.py --upload-assets --backend gws -o workday-slide-assets.json
```

If `--upload-assets` cannot share, still set Anyone with the link: Viewer in the Drive UI.

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

Rebuild so layout IDs are real:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase creates \
  --presentation get.json \
  -o docs/proof/slides/creates.json
```

Send only the `requests` array with `update_presentation` on the same file. Keep `objectId` values `wd_s1` through `wd_s7`.

If a request still has `layoutName`, match `layouts[].layoutProperties.displayName` (strip spaces, ignore case) and put `layoutId` in `slideLayoutReference`.

## 4. Send fills (chunked)

Save a fresh `read_presentation` as `get.json` after the create batch. Rebuild fills with `--presentation` and your image IDs:

```bash
python3 scripts/build_slides.py examples/outline.yaml --phase fills \
  --presentation get.json \
  --cover-image-id "$WORKDAY_COVER_IMAGE_ID" \
  --smile-image-id "$WORKDAY_SMILE_IMAGE_ID" \
  --chunk 40 \
  -o docs/proof/slides/fills.json
```

That writes `fills.json` plus `fills-01.json`, `fills-02.json`, and so on (about 40 requests each). Send the `requests` array from **each chunk, in order**, to `update_presentation`. Do not paste the whole `fills.json` if the connector cannot take that many requests at once.

When image IDs are set, `createImage` URLs are Drive download links only. GitHub raw URLs are dropped.

## 5. Check

`read_presentation` again. Open `https://docs.google.com/presentation/d/<file-id>/edit`.

- Title slide: blue to cream to gold wash, navy title and subtitle, white lockup top left.
- Section slide: gold/teal rail on the left, Ink statement.
- Content, two-column, table, and chart: Ink on Paper, footer at 0.50 in.
- Closing: Ink field, centered smile, Paper caption.

If the cover is flat blue, the fill batch did not include a working `createImage`. Share the PNGs in the Drive UI as Anyone with the link: Viewer, then rebuild and resend the fill chunks.
