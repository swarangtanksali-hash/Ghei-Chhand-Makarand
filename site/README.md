# How the site is built

- `data/poems.json` holds every poem. It is the source of truth.
- `build.py` turns it into `../index.html`, using `style.css`, `app.js`, `themes.py` and `../makarand.jpg`.
- `sheet_import.py` adds new poems from the Google Sheet (published as CSV) to `data/poems.json`.
  Every Form entry is published as its own poem on its own date, even if the text was posted before.
- `data/imported.json` remembers which Sheet rows are already published, so none is added twice.
- `.github/workflows/daily-poems.yml` runs the import and build every morning at 09:00 IST and commits any change.

Everything uses the Python standard library; nothing to install.

## Settings the daily job reads

Repo → Settings → Secrets and variables → Actions → **Variables**:

| Name | Value |
|---|---|
| `SHEET_CSV_URL` | The Sheet's "Publish to web" CSV link (`https://docs.google.com/spreadsheets/d/e/.../pub?output=csv`) |
| `SHEET_DATE_ORDER` | Optional. `DMY` (default, India) or `MDY` if the Sheet's timestamps look like 10/17/2026 |

## Run it by hand

```
python site/sheet_import.py --file some.csv   # or set SHEET_CSV_URL
python site/build.py
python -m unittest discover -s site
```

## Fixing a poem

Each Sheet row is published once. Editing a row afterwards publishes the edited text as a
new entry and leaves the first one on the site. To correct or remove a poem that is
already live, edit (or delete) its entry in `data/poems.json` and run `python site/build.py`.
