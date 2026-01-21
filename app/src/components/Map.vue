<script setup lang="ts">
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { onMounted, onUnmounted, ref, shallowRef, watch } from 'vue';
import type { Audits, Towns } from '../types';

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

  if (audits.features) {
    audits.features.forEach((feature) => {
      // Convert TOWN_ID to integer (it comes as float in the data)
      let townId: number | undefined = feature.properties.TOWN_ID
        ? Math.floor(feature.properties.TOWN_ID)
        : undefined

      // Fallback: Lookup by City Name if TOWN_ID is missing or 0
      if (!townId) {
        const cityName = feature.properties['CITY/TOWN'] || feature.properties.CITY
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

  const initialState = { lng: -71.7, lat: 42.15, zoom: 7.5 }

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
            'background-color': '#f0f0f0',
          },
        },
      ],
    },
    center: [initialState.lng, initialState.lat],
    zoom: initialState.zoom,
  })

  map.value.addControl(new maplibregl.NavigationControl(), 'top-left')

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
      newAudits ? `${newAudits.features?.length} features` : 'null',
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
  <div class="map-wrap">
    <div class="map" ref="mapContainer"></div>
    <div class="legend">
      <div class="legend-title">Audit Count</div>
      <div class="legend-scale">
        <div class="legend-item">
          <span class="legend-color" style="background: #cccccc"></span>
          <span class="legend-label">0</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #ff9800"></span>
          <span class="legend-label">1</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #e65100"></span>
          <span class="legend-label">5</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #b71c1c"></span>
          <span class="legend-label">10+</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-wrap {
  position: relative;
  width: 100%;
  height: 100%;
}

.map {
  position: absolute;
  width: 100%;
  height: 100%;
}

.legend {
  position: absolute;
  bottom: 30px;
  left: 10px;
  background: white;
  padding: 10px 14px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.legend-scale {
  display: flex;
  flex-direction: row;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.legend-label {
  font-size: 12px;
  color: #555;
}
</style>
