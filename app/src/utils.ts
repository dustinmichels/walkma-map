export const parseThemes = (themesStr: string | undefined): string[] => {
  if (!themesStr) return []
  return themesStr
    .split(',')
    .map((s) => s.trim().replace(/^"|"$/g, ''))
    .filter(Boolean)
}
