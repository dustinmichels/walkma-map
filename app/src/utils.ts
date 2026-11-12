import type { Audit } from './types'

const STREET_STOP_WORDS = new Set([
  'between',
  'from',
  'to',
  'and',
  'at',
  'along',
  'near',
  'via',
  'through',
  'the',
  'of',
  'in',
  'on',
  'a',
  'an',
  'by',
  'with',
])

// lowercase, non-alphanumeric runs → hyphens, trim hyphens
const toSlug = (s: string): string =>
  s
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')

// Page URL slug: /audit/<slug>. Uses the sheet's frozen SLUG column (apps-script/Slugs.gs).
// Rows without one fall back to the generated slug, which the sheet script reproduces
// exactly when it fills them: changing the generator breaks shared links.
export function generateAuditSlug(audit: Audit): string {
  if (audit.slug) return audit.slug
  const city = toSlug(audit.city)
  const year = audit.year ? String(parseInt(audit.year)) : 'unknown'
  const neighborhood = audit.neighborhood ? toSlug(audit.neighborhood) : null

  // Skip connector/stop words, keep first 4 meaningful tokens
  const streetTokens = (audit.streets_intersections ?? '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, ' ')
    .split(/\s+/)
    .filter((t) => t.length > 1 && !STREET_STOP_WORDS.has(t))
    .slice(0, 4)
  const street = streetTokens.join('-')

  const parts = [city, year]
  if (neighborhood) parts.push(neighborhood)
  if (street) parts.push(street)
  return parts.join('_')
}

// Image filename under /data/images/. Deliberately differs from generateAuditSlug:
// it must match the names of the existing images, produced by the archived experiment
// archive/old-py/01_scrape.py (get_audit_identifier),
// which takes the neighborhood from parentheses in the city name and the first 4
// street words. Changing it orphans every existing image.
function auditImageId(audit: Audit): string | null {
  const raw = String(audit.city_town || audit.city || '').trim()
  const match = raw.match(/^(.*?)\s*\(([^)]+)\)\s*$/)
  const city = toSlug(match ? match[1]! : raw)
  if (!city) return null
  const neighborhood = match ? toSlug(match[2]!) : null
  const year =
    audit.year != null ? String(parseInt(String(audit.year))) : 'unknown'
  const street = toSlug(audit.streets_intersections ?? '')
    .split('-')
    .slice(0, 4)
    .join('-')
  const parts = [city, year]
  if (neighborhood) parts.push(neighborhood)
  if (street) parts.push(street)
  return parts.join('_')
}

// Resolves to the audit's image URL, or null if it has none.
export function loadAuditImage(audit: Audit): Promise<string | null> {
  const id = auditImageId(audit)
  if (!id) return Promise.resolve(null)
  const src = `/data/images/${id}.jpeg`
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(src)
    img.onerror = () => resolve(null)
    img.src = src
  })
}

// Splits free-text recommendations into list items.
export const parseList = (text: string | undefined): string[] => {
  if (!text) return []
  // Strip zero-width spaces, then normalize inline list separators like "sentence.- Next"
  const normalized = text
    .replace(/[\u200b\u200c\u200d\ufeff]/g, '')
    .replace(/\.\s*-\s+/g, '.\n- ')
    .replace(/([^\s\n])-\s+([A-Z])/g, '$1\n$2')
  return (
    normalized
      .split('\n')
      .map((line) => line.trim())
      // Remove leading dashes, asterisks, or numbers followed by dot/paren
      .map((line) => line.replace(/^[-*•]\s*|^(\d+)[\.)]\s*/, ''))
      .filter((line) => line.length > 0)
  )
}

export const parseThemes = (themesStr: string | undefined): string[] => {
  if (!themesStr) return []
  const results: string[] = []
  let current = ''
  let inQuotes = false
  for (const char of themesStr) {
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      const trimmed = current.trim()
      if (trimmed) results.push(trimmed)
      current = ''
    } else {
      current += char
    }
  }
  const trimmed = current.trim()
  if (trimmed) results.push(trimmed)
  return results
}

export const parseOrgs = (orgsStr: string | undefined): string[] => {
  if (!orgsStr) return []
  return orgsStr
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}
