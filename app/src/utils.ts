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
