# TODO: sheet data fixes

Found by reviewing the filtering logic against `app/public/data/last_run.json` (2026-11-12, 129 audits).

- [ ] HYANNIS (2018): change the city to `BARNSTABLE (Hyannis)` so it matches a town and shows on the map and in the city filter
- [ ] `LOWELL  , CHELMSFORD` (2019): decide how to handle an audit covering two towns. Either pick one town, or support a list of cities in the Go parser, the filters and `Map.updateMapData`
- [ ] Springfield 2023 themes: add quotes around `"Traffic Calming, Speed, Safety"` so it isn't split into three tags
- [ ] Wakefield 2026 themes: the cell contains only a zero-width space; fill it in or clear it
- [ ] Organizer "The Old Colony planning Council": change to "Planning" to match the other 6 audits
- [ ] Decide whether these themes are duplicates and merge them if so:
  - [ ] "Comfort" (2 audits) and "Comfort & Safety"
  - [ ] "Climate Change - Heat" (2) and "Climate - Heat" (9)
