export const parseThemes = (themesStr: string | undefined): string[] => {
  if (!themesStr) return []
  return themesStr
    .split(',')
    .map((s) => s.trim().replace(/^"|"$/g, ''))
    .filter(Boolean)
}

export const parseOrgs = (orgsStr: string | undefined): string[] => {
  if (!orgsStr) return []
  return orgsStr
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}
