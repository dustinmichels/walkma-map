import type { Audits, Towns } from './types'

export interface AuditData {
  audits: Audits
  // Set when served from the last_run.json snapshot instead of the live function
  fallbackDate: string | null
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${url} returned ${res.status}`)
  return res.json()
}

async function fetchAudits(): Promise<AuditData> {
  try {
    return {
      audits: await fetchJSON<Audits>('/.netlify/functions/gsheet'),
      fallbackDate: null,
    }
  } catch (err) {
    console.warn('Live fetch failed, falling back to last_run.json:', err)
    const snapshot = await fetchJSON<{ date: string; data: Audits }>(
      `${import.meta.env.BASE_URL}data/last_run.json`
    )
    return { audits: snapshot.data, fallbackDate: snapshot.date }
  }
}

// Loaded once per page load and shared across views; retried on next call if it failed.
let auditsPromise: Promise<AuditData> | null = null
export function loadAudits(): Promise<AuditData> {
  auditsPromise ??= fetchAudits().catch((err) => {
    auditsPromise = null
    throw err
  })
  return auditsPromise
}

let townsPromise: Promise<Towns> | null = null
export function loadTowns(): Promise<Towns> {
  townsPromise ??= fetchJSON<Towns>(
    `${import.meta.env.BASE_URL}data/towns.geojson`
  ).catch((err) => {
    townsPromise = null
    throw err
  })
  return townsPromise
}
