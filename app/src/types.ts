export interface Crs {
  type: string
  properties: Properties
}

export interface Properties {
  name: string
}

export interface Geometry {
  type: string
  coordinates?: (((number[] | null)[] | null)[] | null)[] | null
}

// Towns Data
export interface Towns {
  type: string
  name: string
  crs: Crs
  features?: TownFeature[] | null
}

export interface TownFeature {
  type: string
  properties: TownProperties
  geometry: Geometry
}

export interface TownProperties {
  CITY: string
  TOWN_ID: number
  TYPE: string
  COUNTY: string
  FIPS_STCO: number
  FOURCOLOR: number
  POP1960: number
  POP1970: number
  POP1980: number
  POP1990: number
  POP2000: number
  POP2010: number
  POP2020: number
  POPCH10_20: number
  AREA_ACRES: number
  AREA_SQMI: number
  SHAPE_Length: number
  SHAPE_Area: number
}

// Audits Data
// Audits Data
export type Audits = Audit[]

export interface Audit {
  'CITY/TOWN': string
  YEAR: number
  SUMMARY: string
  'LONG TERM RECOMMENDATIONS': string
  'SHORT TERM RECOMMENDATIONS': string
  'STREETS, INNTERSECTIONS + AREA COVERED': string
  THEMES: string
  VIEW: string
  'FACILITATOR/AUTHOR': string
  VIEW_link: string
  CITY: string
  NEIGHBORHOOD: any
  TOWN_ID?: number
  TYPE?: string
  COUNTY?: string
}
