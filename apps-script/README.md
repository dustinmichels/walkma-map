# Audit slugs (Google Apps Script)

`Slugs.gs` gives every audit in the [Walk Audit Database tab](https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/edit?gid=379989993#gid=379989993) a permanent URL slug in column **L (SLUG)**, e.g. `brockton_2026_downtown-campello-montello_main-street-north-main` for `/audit/brockton_2026_downtown-campello-montello_main-street-north-main`.

Before this column existed, the website built each slug from city, year, neighborhood and streets, so editing any of those cells broke links people had already shared. Now the slug is written into the sheet once and never recomputed. The website uses column L when it is filled and falls back to the old generated slug when it is blank.

The script only writes blank cells in column L of the database tab. It doesn't touch the [submission form](https://docs.google.com/forms/d/e/1FAIpQLScsPq-g1mzENzeLzwOWPurGMmaBlNZK0gfmsMhsHs8WFkBQEQ/viewform) or its responses tab, and the form doesn't write to the database tab.

## One-time setup

1. **Name a restore point.** File → Version history → Name current version (e.g. "before SLUG column").
2. **Add the column.** In the Walk Audit Database tab, right-click the **K (ORGANIZATIONS)** column header → *Insert 1 column right*. In the new column L, type `SLUG` in the header row (the row with `CITY/TOWN`). Leave the cells below empty. It must be column L: the website reads columns A–K by position.
3. **Add the script.** Extensions → Apps Script. Replace the contents of `Code.gs` with [`Slugs.gs`](Slugs.gs), then save.
4. **Run `setup`.** Choose `setup` in the function dropdown → Run, and approve the permissions. Google shows "Google hasn't verified this app" for your own scripts: Advanced → Go to (project name). `setup`:
   - fills every blank SLUG cell with the slug that row's link uses today, so existing links keep working;
   - adds an edit warning to column L;
   - schedules `fillMissingSlugs` to run hourly. That schedule runs as you, and failure emails go to you.
5. **Check.** Column L is filled, and reloading the sheet shows an *Audit slugs* menu.

Running `setup` again is safe: it skips filled cells and replaces its own warning and schedule instead of duplicating them.

## Day-to-day rules for sheet editors

- **New audit row:** leave SLUG blank. It is filled within an hour, or right away via *Audit slugs → Fill missing slugs now*. Finish the row (city, year, neighborhood, streets) first, since the slug is built from those cells once.
- **Editing an audit:** change anything except SLUG. The link stays the same.
- **Copying a row:** clear the SLUG cell on the copy. Duplicate slugs stop the script with an error (emailed to whoever ran `setup`), and the website shows only the first row with that slug.
- **Sorting:** sort the whole sheet or table. Never sort a selection that leaves out column L, or slugs get attached to the wrong rows.
- **Changing a slug on purpose:** add a redirect from the old one to the new one in `netlify.toml` (see the existing Brockton example), or the old links break.

## Checking the published data

Published sheet changes take a few minutes to appear. Then run `./refresh_data.sh` from the repository root and check that no slug is blank or used twice:

```sh
jq '[.[] | select(.slug == "")] | length' app/netlify/functions/gsheet/data/audits.json   # 0
jq '[.[].slug] | group_by(.) | map(select(length > 1))' app/netlify/functions/gsheet/data/audits.json   # []
```
