// Towns Data (public/data/towns.geojson)
export interface Towns {
  type: string
  features?: TownFeature[] | null
}

export interface TownFeature {
  type: string
  id?: number
  properties: TownProperties
  geometry: {
    type: string
    coordinates?: unknown
  }
}

export interface TownProperties {
  CITY: string
  TOWN_ID: number
}

// Audits Data
export type Audits = Audit[]

export interface Audit {
  city_town: string
  city: string
  neighborhood: string
  year: string
  summary: string
  long_term_recommendations: string
  short_term_recommendations: string
  streets_intersections: string
  themes: string
  view: string
  facilitator_author: string
  organizer_lead_organization: string
  // Sheet column L (apps-script/Slugs.gs); absent in older snapshots, empty until filled
  slug?: string
}
