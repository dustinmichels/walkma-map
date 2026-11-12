// Stable audit slugs for the "Walk Audit Database" tab (see apps-script/README.md).
//
// Column L (SLUG) holds each audit's permanent /audit/<slug> URL segment. A slug
// is written once into a blank cell and never recomputed, so later edits to
// city/year/neighborhood/streets don't break shared links. Only column L of the
// database tab is ever written; the form's responses tab is never touched.

const SHEET_GID = 379989993 // the tab the website reads
const SLUG_COL = 12 // L. The site reads A–K by position, so SLUG must stay right after ORGANIZATIONS (K).
const COL = { city: 0, year: 1, neighborhood: 2, streets: 6 } // 0-based sheet columns A, B, C, G
const PROTECTION_NOTE = 'Audit slugs: changing one breaks its shared links'

const STREET_STOP_WORDS = new Set([
  'between', 'from', 'to', 'and', 'at', 'along', 'near', 'via', 'through',
  'the', 'of', 'in', 'on', 'a', 'an', 'by', 'with',
])

function toSlug_(s) {
  return s
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

// Same slug the website generated before this column existed (generateAuditSlug in
// app/src/utils.ts after ParseCity in internal/audits/audits.go), so the backfill
// keeps every existing link working. `row` holds display values.
function slugFromRow_(row) {
  const city = toSlug_(row[COL.city].trim().toUpperCase().replace(/\s*\(.*?\)/g, ''))
  const year = row[COL.year].trim()
  const neighborhood = row[COL.neighborhood].trim()
  // The website reads the published HTML, which drops line breaks inside cells.
  const streets = row[COL.streets].replace(/\n/g, '').trim()

  const streetTokens = streets
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, ' ')
    .split(/\s+/)
    .filter((t) => t.length > 1 && !STREET_STOP_WORDS.has(t))
    .slice(0, 4)

  const parts = [city, year ? String(parseInt(year)) : 'unknown']
  if (neighborhood) parts.push(toSlug_(neighborhood))
  if (streetTokens.length) parts.push(streetTokens.join('-'))
  return parts.join('_')
}

// Returns [rowIndex, slug] pairs for rows the website shows that have no slug yet.
// Rows are scanned top to bottom, so of two identical rows the upper one keeps the
// plain slug (the one the website already resolved to) and later ones get -2, -3, …
function missingSlugs_(values) {
  const header = values.findIndex((r) => r[COL.city].trim().toUpperCase() === 'CITY/TOWN')
  if (header < 0) throw new Error('No header row with CITY/TOWN in column A')
  if ((values[header][SLUG_COL - 1] || '').trim().toUpperCase() !== 'SLUG') {
    throw new Error('Column L must be headed SLUG (add it right after ORGANIZATIONS)')
  }

  const rows = values.slice(header + 1)
  const taken = new Set(rows.map((r) => r[SLUG_COL - 1].trim()).filter(Boolean))
  const result = []
  rows.forEach((row, i) => {
    if (row[SLUG_COL - 1].trim()) return
    if (!row[COL.city].trim() && !row[COL.neighborhood].trim()) return // blank row, skipped by the site
    const base = slugFromRow_(row)
    let slug = base
    for (let n = 2; taken.has(slug); n++) slug = `${base}-${n}`
    taken.add(slug)
    result.push([header + 1 + i, slug])
  })
  return result
}

function auditSheet_() {
  const sheet = SpreadsheetApp.getActive().getSheets().find((s) => s.getSheetId() === SHEET_GID)
  if (!sheet) throw new Error(`No tab with gid ${SHEET_GID}`)
  return sheet
}

// Filled slugs used by more than one row: the website only shows the first of them.
function duplicateSlugs_(values) {
  const seen = new Set()
  const dupes = new Set()
  values.forEach((r) => {
    const s = (r[SLUG_COL - 1] || '').trim()
    if (s) seen.has(s) ? dupes.add(s) : seen.add(s)
  })
  return [...dupes]
}

// Fills blank SLUG cells. Never changes a filled one. Runs hourly and from the menu.
// Throws on duplicates (usually a copy-pasted row) so the trigger's failure email flags them.
function fillMissingSlugs() {
  const lock = LockService.getDocumentLock()
  lock.waitLock(30000)
  try {
    const sheet = auditSheet_()
    const values = sheet.getDataRange().getDisplayValues()
    const missing = missingSlugs_(values)
    missing.forEach(([i, slug]) => sheet.getRange(i + 1, SLUG_COL).setValue(slug))
    console.log(`Filled ${missing.length} slug(s)`)
    const dupes = duplicateSlugs_(values)
    if (dupes.length) {
      throw new Error(`Duplicate slugs; clear SLUG on the newer row so it gets its own: ${dupes.join(', ')}`)
    }
    return missing.length
  } finally {
    lock.releaseLock()
  }
}

function fillMissingSlugsFromMenu() {
  const n = fillMissingSlugs()
  SpreadsheetApp.getActive().toast(`Filled ${n} missing slug(s)`, 'Audit slugs')
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Audit slugs')
    .addItem('Fill missing slugs now', 'fillMissingSlugsFromMenu')
    .addToUi()
}

// Run once from the editor: backfills every row, adds an edit warning on column L,
// and schedules the hourly fill. Safe to rerun.
function setup() {
  const sheet = auditSheet_()
  fillMissingSlugs()

  sheet.getProtections(SpreadsheetApp.ProtectionType.RANGE)
    .filter((p) => p.getDescription() === PROTECTION_NOTE)
    .forEach((p) => p.remove())
  sheet.getRange(1, SLUG_COL, sheet.getMaxRows())
    .protect()
    .setDescription(PROTECTION_NOTE)
    .setWarningOnly(true)

  ScriptApp.getProjectTriggers()
    .filter((t) => t.getHandlerFunction() === 'fillMissingSlugs')
    .forEach((t) => ScriptApp.deleteTrigger(t))
  ScriptApp.newTrigger('fillMissingSlugs').timeBased().everyHours(1).create()
}
