# Web App Rules

## Filtering Overview

There are four independent filter dimensions: **City**, **Tags**, **Organizer**, and **Year**. All active filters are combined with AND logic — an audit must satisfy every active filter to appear in results.

Filters are managed in `AuditFilters.vue` and applied in two layers:

- **Content filters** (Tags, Organizer, Year) — applied globally, independent of City.
- **City filter** — applied on top of content filters to narrow results further.

---

## Filter Dimensions

### City

- Selecting a city narrows the DataPanel and ThemeChart to only that city's audits.
- The city dropdown lists only cities that have audits matching the currently active content filters (Tags, Year, Organizer).
- If no city is selected, all cities' audits are shown.
- City can be selected via the dropdown in AuditFilters, or by clicking a town on the map.
- Clicking the same city again does not deselect it; use the X button or "Reset All" to clear.

### Tags

- Multiple tags can be selected simultaneously (multi-select).
- Tag filtering uses **AND logic**: an audit must contain **all** selected tags to pass the filter.
  - Example: selecting "Sidewalks" and "Crossings" shows only audits tagged with both.
- If no tags are selected, all audits pass the tag filter.
- The available tags list is recomputed based on the currently active City, Year, and Organizer filters — it does not include tags from audits that are already excluded by other filters.
- Tags are parsed from a comma-separated string (e.g., `"Sidewalks", "Crossings"`) and leading/trailing quotes are stripped.

### Organizer

- Exactly one organizer can be selected at a time (single-select).
- Selecting an organizer shows only audits led by that organization.
- If no organizer is selected, all audits pass the organizer filter.
- The available organizers list is recomputed based on the currently active City, Year, and Tag filters.

### Year

- A slider selects `selectedMaxYear`, ranging from the minimum to maximum year found across all audits.
- The slider has two modes, toggled by clicking the label above it:
  - **"Through [year]"** (default): shows audits from the earliest available year through `selectedMaxYear` (inclusive). Example: "Through 2022" shows all audits from 2015–2022.
  - **"In [year]"**: shows only audits from exactly `selectedMaxYear`. Example: "In 2020" shows only 2020 audits.
- The slider initializes to the maximum year (i.e., all audits visible) on first load.
- The year filter is considered "active" (counts toward activeFilterCount) if:
  - The mode is "In" (any year), OR
  - The mode is "Through" and `selectedMaxYear` is less than the dataset maximum.

---

## Filter Interactions & Cascading Options

Available options for each filter dimension update dynamically based on the other active filters:

| Filter     | Available options computed from                              |
| ---------- | ------------------------------------------------------------ |
| City       | `contentFilteredAudits` (Tag + Year + Org filtered, no City) |
| Tags       | City-scoped audits → Year-filtered → Organizer-filtered      |
| Organizers | City-scoped audits → Year-filtered → Tag-filtered            |

This ensures that:

- Selecting a tag cannot cause a city to disappear from the city list unless no audits for that city have that tag.
- Selecting an organizer cannot show tags that only appear in other organizers' audits.
- The city dropdown always reflects what's possible given the current content filters.

---

## Data Flow

### Two Filtered Sets

1. **`contentFilteredAudits`** — filtered by Tags, Year, Organizer only (no City). Emitted to `App.vue` via the `filter` event.
2. **`relevantAudits`** (computed in `App.vue`) — `contentFilteredAudits` further narrowed by the selected City. Used by DataPanel and ThemeChart.

### What Each Component Receives

| Component  | Audits received                                               | Notes                                    |
| ---------- | ------------------------------------------------------------- | ---------------------------------------- |
| Map        | `contentFilteredAudits` (or all audits if no content filters) | Shows all cities, colored by audit count |
| DataPanel  | `relevantAudits` (content + city filtered)                    | Shows the list of matching audits        |
| ThemeChart | `relevantAudits` (content + city filtered)                    | Shows theme counts for matching audits   |

---

## Sorting

- Audits in the DataPanel are always sorted **most recent first** (descending by `year`).
- This sort is applied after all filters.
- Audits with no year value are treated as year `0` and sorted to the bottom.

---

## Map Behavior

- The map colors towns by audit count using the **content-filtered** set (Tags, Year, Org), so the heatmap reflects active filters but all cities remain visible.
- When a city is selected, that town's border is highlighted in red.
- Clicking a town on the map sets `selectedCity` to that town's name.
- The map is bounded to Massachusetts and cannot be panned outside it.

---

## ThemeChart Behavior

- Bars are ordered by count (most common theme at top) within the current filtered set.
- The list of themes is stable: the full set of themes from all audits is always shown, even if some have a count of 0 in the current filtered set.
- Clicking a bar in the chart toggles that theme in the selected tags filter (adds if not selected, removes if already selected).
- The stat panel shows the count of matching audits and unique cities in the current filtered set.

---

## DataPanel Behavior

- Displays up to 20 audits initially; additional audits load automatically when scrolling near the bottom (infinite scroll, 20 at a time).
- The visible limit resets to 20 and the scroll position resets to the top whenever the audit set changes (i.e., when any filter changes).
- If the filtered audit set is empty, an empty state message is shown with a link to learn about doing a walk audit.

---

## Reset Behavior

- The **"Reset All"** button clears all active filters: City, Tags, Organizer, and Year (slider returns to max year in "Through" mode).
- Each filter dimension also has its own **X button** to clear just that filter.
- The "Reset All" button is only shown when `activeFilterCount > 0`.

### Active Filter Count

`activeFilterCount` is the total number of active filter dimensions:

- +1 per selected tag
- +1 if year is filtered (mode is "In", or slider is below max)
- +1 if an organizer is selected
- +1 if a city is selected

---

## Examples

### Example 1: City-only filter

- User selects "Boston"
- DataPanel shows only Boston audits, sorted most recent first
- Map still shows all cities colored by their audit counts (unaffected by city filter)
- ThemeChart updates to reflect only Boston audits

### Example 2: Tag AND filter

- User selects tags "Sidewalks" and "Lighting"
- Only audits containing **both** tags appear in DataPanel
- Map heatmap updates to reflect only audits with both tags
- City dropdown updates to show only cities that have audits with both tags

### Example 3: Year "Through" mode

- Slider set to "Through 2020"
- Audits from all years up to and including 2020 are shown
- Audits from 2021 onward are excluded

### Example 4: Year "In" mode

- Slider set to "In 2022"
- Only audits from exactly 2022 are shown

### Example 5: Combined filters

- User selects city "Cambridge", tag "Crossings", organizer "WalkBoston", year "Through 2023"
- Only audits matching **all four** criteria appear in DataPanel and ThemeChart
- Map still shows all cities, but heatmap reflects only audits matching the tag, organizer, and year filters (not the city filter)

### Example 6: Cascading options

- User selects organizer "WalkBoston"
- Available tags update to only show tags present in WalkBoston audits
- City dropdown updates to show only cities where WalkBoston has conducted audits

### Example 7: Chart interaction

- User clicks "Crossings" bar in ThemeChart
- "Crossings" is added to selected tags; DataPanel and map update immediately
- Clicking "Crossings" again removes it from selected tags

### Example 8: Map interaction

- User clicks on "Somerville" on the map
- `selectedCity` is set to "Somerville"
- DataPanel and ThemeChart narrow to Somerville audits
- Map highlights Somerville's border in red, all other city colors remain unchanged
