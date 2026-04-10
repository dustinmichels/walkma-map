import type { Audit } from './types'

const STREET_STOP_WORDS = new Set([
  'between', 'from', 'to', 'and', 'at', 'along', 'near', 'via',
  'through', 'the', 'of', 'in', 'on', 'a', 'an', 'by', 'with',
])

export function generateAuditSlug(audit: Audit): string {
  const toSlug = (s: string) =>
    s.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

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
