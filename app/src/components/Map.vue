<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onMounted, onUnmounted, ref, shallowRef, watch, computed } from 'vue'
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

const updateMapData = (audits: Audits | null) => {
  if (!map.value || !audits) {
    console.log('updateMapData skipped:', { hasMap: !!map.value, hasAudits: !!audits })
    return
  }

  // Check if source exists
  if (!map.value.getSource('towns')) {
    console.log('Towns source not yet added to map')
    return
  }

  // Reset all towns to 0 first
  for (const id of Object.values(townIdMap.value)) {
    map.value.setFeatureState({ source: 'towns', id: Number(id) }, { auditCount: 0 })
  }

  const counts: Record<number, number> = {}

  if (audits) {
    audits.forEach((audit) => {
      // Convert TOWN_ID to integer (it comes as float in the data)
      let townId: number | undefined = audit.TOWN_ID ? Math.floor(audit.TOWN_ID) : undefined

      // Fallback: Lookup by City Name if TOWN_ID is missing or 0
      if (!townId) {
        const cityName = audit['CITY/TOWN'] || audit.CITY
        if (cityName) {
          const standardizedName = cityName.toUpperCase().trim()
          townId = townIdMap.value[standardizedName]
        }
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
      map.value.setFeatureState({ source: 'towns', id: Number(id) }, { auditCount: count })
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
        // Update the filter for the selected line layer
        map.value.setFilter('towns-selected', ['==', ['get', 'TOWN_ID'], townId])

        // Optional: Fly to the town if needed, but simple highlighting is requested
      } else {
        map.value.setFilter('towns-selected', ['==', ['get', 'TOWN_ID'], -1])
      }
    } else {
      map.value.setFilter('towns-selected', ['==', ['get', 'TOWN_ID'], -1])
    }
  },
)

onMounted(async () => {
  if (!mapContainer.value) return

  // Fetch Towns Data first to build lookup map & ensure source data is available
  let townsData: Towns | null = null
  try {
    const res = await fetch('/data/towns.geojson')
    townsData = await res.json()

    if (townsData && townsData.features) {
      townsData.features.forEach((f: any) => {
        const p = f.properties
        if (p.TOWN_ID) {
          // Manually assign ID for setFeatureState to work reliably
          f.id = p.TOWN_ID

          const name = p.CITY || p.TOWN
          if (name) {
            const standardName = name.toUpperCase().trim()
            townIdMap.value[standardName] = p.TOWN_ID
            townIdToNameMap.value[p.TOWN_ID] = name
          }
        }
      })
      console.log('Loaded town ID map with', Object.keys(townIdMap.value).length, 'towns')
    }
  } catch (err) {
    console.error('Failed to load towns data', err)
  }

  map.value = new maplibregl.Map({
    container: mapContainer.value,
    style: {
      version: 8,
      sources: {},
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: {
            'background-color': '#ffffff',
          },
        },
      ],
    },
    center: [initialState.lng, initialState.lat],
    zoom: initialState.zoom,
    minZoom: 7,
    maxBounds: [
      [-74.5, 41.0], // Southwest coordinates
      [-69.0, 43.5], // Northeast coordinates
    ],
  })

  // map.value.addControl(new maplibregl.NavigationControl(), 'top-left') // Removed default controls

  map.value.on('load', () => {
    console.log('Map loaded')
    if (!map.value || !townsData) return

    map.value.addSource('towns', {
      type: 'geojson',
      data: townsData as any,
      // promoteId: 'TOWN_ID', // Removing promoteId, we manually set id on features
    })

    // Fill Layer
    map.value.addLayer({
      id: 'towns-fill',
      type: 'fill',
      source: 'towns',
      paint: {
        'fill-color': [
          'case',
          ['>', ['feature-state', 'auditCount'], 0],
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
          '#cccccc', // Grey for no audits
        ],
        'fill-opacity': 0.8,
      },
    })

    // Standard Border Layer
    map.value.addLayer({
      id: 'towns-line',
      type: 'line',
      source: 'towns',
      paint: {
        'line-color': '#fff',
        'line-width': 1,
        'line-opacity': 0.5,
      },
    })

    // Selected Town Border Layer
    map.value.addLayer({
      id: 'towns-selected',
      type: 'line',
      source: 'towns',
      filter: ['==', ['get', 'TOWN_ID'], -1], // Initially hide
      paint: {
        'line-color': '#ff0000', // Bright Red
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
      mapReady.value,
    )
    if (mapReady.value) {
      updateMapData(newAudits)
    } else {
      console.log('Map not ready yet, will update when loaded')
    }
  },
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
      <div class="animate-spin text-brand-orange mb-3">
        <svg class="h-10 w-10" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      </div>
      <p class="text-zinc-600 font-semibold animate-pulse">Loading Map...</p>
    </div>
    <div class="absolute w-full h-full" ref="mapContainer"></div>

    <!-- Legend -->
    <div
      class="absolute bottom-6 left-4 bg-white/95 backdrop-blur-sm py-3 px-4 rounded-lg shadow-lg z-10 flex items-center gap-4 border border-zinc-100"
    >
      <div class="text-xs font-bold text-zinc-800 uppercase tracking-wide">Audit Count</div>
      <div class="flex flex-row gap-3">
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded border border-zinc-200" style="background: #cccccc"></span>
          <span class="text-xs text-zinc-600 font-medium">0</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded border border-zinc-200" style="background: #ff9800"></span>
          <span class="text-xs text-zinc-600 font-medium">1</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded border border-zinc-200" style="background: #e65100"></span>
          <span class="text-xs text-zinc-600 font-medium">5</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded border border-zinc-200" style="background: #b71c1c"></span>
          <span class="text-xs text-zinc-600 font-medium">10+</span>
        </div>
      </div>
    </div>

    <!-- Custom Map Controls -->
    <div
      class="absolute top-5 left-5 z-10 flex flex-col bg-white rounded-lg shadow-lg overflow-hidden border border-zinc-200"
    >
      <button
        class="flex items-center justify-center w-9 h-9 bg-white border-0 cursor-pointer text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-black active:bg-zinc-200"
        @click="zoomIn"
        title="Zoom In"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-5 h-5"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
      <div class="h-px bg-zinc-100 w-full"></div>
      <button
        class="flex items-center justify-center w-9 h-9 bg-white border-0 cursor-pointer text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-black active:bg-zinc-200"
        @click="zoomOut"
        title="Zoom Out"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-5 h-5"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
        </svg>
      </button>
      <div class="h-px bg-zinc-100 w-full"></div>
      <button
        class="flex items-center justify-center w-9 h-9 bg-white border-0 cursor-pointer text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-black active:bg-zinc-200"
        @click="resetMap"
        title="Reset View"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-5 h-5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75v4.5m0-4.5h-4.5m4.5 0L15 9m5.25 11.25v-4.5m0 4.5h-4.5m4.5 0L15 15"
          />
        </svg>
      </button>
    </div>
  </div>
</template>
