<script setup lang="ts">
import { Home, Layers, Loader2, Minus, Plus } from 'lucide-vue-next'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { loadTowns } from '../data'
import type { Audits, Towns } from '../types'

const props = defineProps<{
  audits: Audits | null
  selectedCity: string
}>()

const emit = defineEmits<{
  (e: 'update:selectedCity', value: string): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
const map = shallowRef<maplibregl.Map | null>(null)
let resizeObserver: ResizeObserver | null = null
const townIdMap = ref<Record<string, number>>({})
const townIdToNameMap = ref<Record<number, string>>({})
const mapReady = ref(false)
const isLoading = computed(() => !mapReady.value || !props.audits)

const initialState = { lng: -71.7, lat: 42.15, zoom: 7.5 }

const zoomIn = () => {
  map.value?.zoomIn()
}

const zoomOut = () => {
  map.value?.zoomOut()
}

const resetMap = () => {
  map.value?.flyTo({
    center: [initialState.lng, initialState.lat],
    zoom: initialState.zoom,
    pitch: 0,
    bearing: 0,
  })
}

// Town styling per mode: opaque on plain white, translucent over the basemap
const townPaint = {
  off: {
    noAuditColor: '#cccccc',
    noAuditOpacity: 0.8,
    auditedOpacity: 0.8,
    lineColor: '#ffffff',
    lineWidth: 1,
    lineOpacity: 0.5,
  },
  on: {
    noAuditColor: '#a1a1aa',
    noAuditOpacity: 0.15,
    auditedOpacity: 0.75,
    lineColor: '#52525b',
    lineWidth: 0.5,
    lineOpacity: 0.35,
  },
}

const showBasemap = ref(false)
let basemapLayerIds: string[] = []
const noAuditSwatch = computed(() =>
  showBasemap.value ? 'rgba(161, 161, 170, 0.15)' : townPaint.off.noAuditColor
)

const applyBasemap = () => {
  const m = map.value
  if (!m?.getLayer('towns-fill')) return

  const visibility = showBasemap.value ? 'visible' : 'none'
  for (const id of basemapLayerIds) {
    m.setLayoutProperty(id, 'visibility', visibility)
  }

  const p = showBasemap.value ? townPaint.on : townPaint.off
  const hasAudits = ['>', ['feature-state', 'auditCount'], 0]
  m.setPaintProperty('towns-fill', 'fill-color', [
    'case',
    hasAudits,
    [
      'interpolate',
      ['linear'],
      ['feature-state', 'auditCount'],
      1,
      '#ff9800', // Orange for 1
      5,
      '#e65100', // Darker Orange for 5+
      10,
      '#b71c1c', // Deep red/orange for many
    ],
    p.noAuditColor,
  ])
  m.setPaintProperty('towns-fill', 'fill-opacity', [
    'case',
    hasAudits,
    p.auditedOpacity,
    p.noAuditOpacity,
  ])
  m.setPaintProperty('towns-line', 'line-color', p.lineColor)
  m.setPaintProperty('towns-line', 'line-width', p.lineWidth)
  m.setPaintProperty('towns-line', 'line-opacity', p.lineOpacity)
}

watch(showBasemap, applyBasemap)

const updateMapData = (audits: Audits | null) => {
  if (!map.value || !audits) {
    console.log('updateMapData skipped:', {
      hasMap: !!map.value,
      hasAudits: !!audits,
    })
    return
  }

  // Check if source exists
  if (!map.value.getSource('towns')) {
    console.log('Towns source not yet added to map')
    return
  }

  // Reset all towns to 0 first
  for (const id of Object.values(townIdMap.value)) {
    map.value.setFeatureState(
      { source: 'towns', id: Number(id) },
      { auditCount: 0 }
    )
  }

  const counts: Record<number, number> = {}

  if (audits) {
    audits.forEach((audit) => {
      // Lookup by City Name
      let townId: number | undefined
      const cityName = audit.city_town || audit.city
      if (cityName) {
        // Strip parenthetical neighborhood info for matching
        const baseName = cityName
          .replace(/\s*\(.*\)/, '')
          .toUpperCase()
          .trim()
        townId = townIdMap.value[baseName]
      }

      if (townId) {
        counts[townId] = (counts[townId] || 0) + 1
      }
    })
  }

  console.log('Audit counts by town:', counts)

  let matched = 0
  for (const [id, count] of Object.entries(counts)) {
    if (map.value.getSource('towns')) {
      map.value.setFeatureState(
        { source: 'towns', id: Number(id) },
        { auditCount: count }
      )
      matched++
    }
  }
  console.log(`Updated feature state for ${matched} towns`)
}

// Watch for selectedCity changes to update the map selection state
watch(
  () => props.selectedCity,
  (newCity) => {
    if (!map.value || !map.value.isStyleLoaded()) return

    if (newCity) {
      const townId = townIdMap.value[newCity.toUpperCase().trim()]
      if (townId) {
        // Update the filter for the selected town layers
        const filter: any = ['==', ['get', 'TOWN_ID'], townId]
        map.value.setFilter('towns-selected-fill', filter)
        map.value.setFilter('towns-selected-border', filter)
      } else {
        const filter: any = ['==', ['get', 'TOWN_ID'], -1]
        map.value.setFilter('towns-selected-fill', filter)
        map.value.setFilter('towns-selected-border', filter)
      }
    } else {
      const filter: any = ['==', ['get', 'TOWN_ID'], -1]
      map.value.setFilter('towns-selected-fill', filter)
      map.value.setFilter('towns-selected-border', filter)
    }
  }
)

onMounted(async () => {
  if (!mapContainer.value) return

  // Fetch Towns Data first to build lookup map & ensure source data is available
  let townsData: Towns | null = null
  try {
    townsData = await loadTowns()

    if (townsData && townsData.features) {
      townsData.features.forEach((f) => {
        const p = f.properties
        if (p.TOWN_ID) {
          // Manually assign ID for setFeatureState to work reliably
          f.id = p.TOWN_ID

          const name = p.CITY
          if (name) {
            const standardName = name.toUpperCase().trim()
            townIdMap.value[standardName] = p.TOWN_ID
            townIdToNameMap.value[p.TOWN_ID] = name
          }
        }
      })
      console.log(
        'Loaded town ID map with',
        Object.keys(townIdMap.value).length,
        'towns'
      )
    }
  } catch (err) {
    console.error('Failed to load towns data', err)
  }

  map.value = new maplibregl.Map({
    container: mapContainer.value,
    // Free, keyless vector basemap (OpenMapTiles schema); hidden unless toggled on
    style: 'https://tiles.openfreemap.org/styles/positron',
    center: [initialState.lng, initialState.lat],
    zoom: initialState.zoom,
    minZoom: 7,
    maxZoom: 14,
    maxBounds: [
      [-74.5, 41.0], // Southwest coordinates
      [-69.0, 43.5], // Northeast coordinates
    ],
  })

  // map.value.addControl(new maplibregl.NavigationControl(), 'top-left') // Removed default controls

  map.value.on('load', () => {
    console.log('Map loaded')
    if (!map.value || !townsData) return

    // Everything in the loaded style belongs to the basemap; capture before adding ours
    basemapLayerIds = map.value.getStyle().layers.map((l) => l.id)

    // Plain white backdrop shown when the basemap is hidden
    map.value.addLayer(
      {
        id: 'blank-background',
        type: 'background',
        paint: { 'background-color': '#ffffff' },
      },
      basemapLayerIds[0]
    )

    map.value.addSource('towns', {
      type: 'geojson',
      data: townsData as any,
    })

    // Insert town layers beneath the basemap's labels so place names stay readable
    const firstLabelLayer = map.value
      .getStyle()
      .layers.find((l) => l.type === 'symbol')?.id

    // Paint for both town layers is set by applyBasemap()
    map.value.addLayer(
      { id: 'towns-fill', type: 'fill', source: 'towns' },
      firstLabelLayer
    )
    map.value.addLayer(
      { id: 'towns-line', type: 'line', source: 'towns' },
      firstLabelLayer
    )
    applyBasemap()

    // Selected Town Highlight Layer - Fill
    map.value.addLayer({
      id: 'towns-selected-fill',
      type: 'fill',
      source: 'towns',
      filter: ['==', ['get', 'TOWN_ID'], -1], // Initially hide
      paint: {
        'fill-color': 'transparent',
        'fill-opacity': 0.0,
      },
      layout: {
        'fill-sort-key': 100, // Ensure it renders on top
      },
    })

    // Selected Town Highlight Layer - Border
    map.value.addLayer({
      id: 'towns-selected-border',
      type: 'line',
      source: 'towns',
      filter: ['==', ['get', 'TOWN_ID'], -1], // Initially hide
      paint: {
        'line-color': '#dc2626', // Red-600
        'line-width': 3,
        'line-opacity': 1,
      },
    })

    // Click to Select
    map.value.on('click', 'towns-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const feature = e.features[0]
        if (feature && feature.properties) {
          const townId = feature.properties.TOWN_ID
          if (townId) {
            const city = townIdToNameMap.value[townId]
            // If we found a name, emit it
            if (city) {
              emit('update:selectedCity', city)
            }
          }
        }
      }
    })

    // Change cursor on hover
    map.value.on('mouseenter', 'towns-fill', () => {
      map.value!.getCanvas().style.cursor = 'pointer'
    })
    map.value.on('mouseleave', 'towns-fill', () => {
      map.value!.getCanvas().style.cursor = ''
    })

    // Mark map as ready
    mapReady.value = true
    console.log('Map fully initialized and ready')

    // Initial load if audits are already available
    if (props.audits) {
      updateMapData(props.audits)
    }
  })

  // ResizeObserver to handle container size changes
  resizeObserver = new ResizeObserver(() => {
    map.value?.resize()
  })
  resizeObserver.observe(mapContainer.value)
})

watch(
  () => props.audits,
  (newAudits) => {
    console.log(
      'Audits changed, updating map. Audits:',
      newAudits ? `${newAudits.length} features` : 'null',
      'mapReady:',
      mapReady.value
    )
    if (mapReady.value) {
      updateMapData(newAudits)
    } else {
      console.log('Map not ready yet, will update when loaded')
    }
  }
)

onUnmounted(() => {
  map.value?.remove()
  resizeObserver?.disconnect()
})
</script>

<template>
  <div class="relative w-full h-full group">
    <div
      v-if="isLoading"
      class="absolute inset-0 z-50 flex flex-col items-center justify-center bg-white/90 backdrop-blur-sm"
    >
      <div class="text-brand-orange mb-3">
        <Loader2 class="h-10 w-10 animate-spin" />
      </div>
      <p class="text-zinc-600 font-semibold animate-pulse">Loading Map...</p>
    </div>
    <div class="absolute w-full h-full" ref="mapContainer"></div>

    <!-- Legend -->
    <div
      class="absolute bottom-6 left-4 bg-white/95 backdrop-blur-sm py-3 px-4 rounded-lg shadow-lg z-10 flex items-center gap-4 border border-zinc-100"
    >
      <div class="text-xs font-bold text-zinc-800 uppercase tracking-wide">
        Audit Count
      </div>
      <div class="flex flex-row gap-3">
        <div class="flex items-center gap-2">
          <span
            class="w-5 h-5 rounded border border-zinc-200"
            :style="{ background: noAuditSwatch }"
          ></span>
          <span class="text-xs text-zinc-600 font-medium">0</span>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="w-5 h-5 rounded border border-zinc-200"
            style="background: #ff9800"
          ></span>
          <span class="text-xs text-zinc-600 font-medium">1</span>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="w-5 h-5 rounded border border-zinc-200"
            style="background: #e65100"
          ></span>
          <span class="text-xs text-zinc-600 font-medium">5</span>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="w-5 h-5 rounded border border-zinc-200"
            style="background: #b71c1c"
          ></span>
          <span class="text-xs text-zinc-600 font-medium">10+</span>
        </div>
      </div>
    </div>

    <!-- Custom Map Controls -->
    <div class="absolute top-5 right-5 z-10 flex flex-col gap-3">
      <div
        class="flex flex-col bg-white rounded-lg shadow-lg overflow-hidden border border-zinc-200"
      >
        <button
          class="flex items-center justify-center w-9 h-9 bg-white border-0 cursor-pointer text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-black active:bg-zinc-200"
          @click="zoomIn"
          title="Zoom In"
        >
          <Plus class="w-5 h-5" />
        </button>
        <div class="h-px bg-zinc-100 w-full"></div>
        <button
          class="flex items-center justify-center w-9 h-9 bg-white border-0 cursor-pointer text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-black active:bg-zinc-200"
          @click="zoomOut"
          title="Zoom Out"
        >
          <Minus class="w-5 h-5" />
        </button>
        <div class="h-px bg-zinc-100 w-full"></div>
        <button
          class="flex items-center justify-center w-9 h-9 bg-white border-0 cursor-pointer text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-black active:bg-zinc-200"
          @click="resetMap"
          title="Reset View"
        >
          <Home class="w-5 h-5" />
        </button>
      </div>

      <!-- Basemap Toggle -->
      <button
        class="flex items-center justify-center w-9 h-9 rounded-lg shadow-lg border cursor-pointer transition-colors"
        :class="
          showBasemap
            ? 'bg-orange-50 border-orange-200 text-brand-orange hover:bg-orange-100'
            : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-100 hover:text-black'
        "
        @click="showBasemap = !showBasemap"
        :title="showBasemap ? 'Hide Basemap' : 'Show Basemap'"
        :aria-pressed="showBasemap"
      >
        <Layers class="w-5 h-5" />
      </button>
    </div>
  </div>
</template>
