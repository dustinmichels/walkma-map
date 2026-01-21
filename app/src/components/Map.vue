<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const mapContainer = ref<HTMLElement | null>(null)
const map = shallowRef<maplibregl.Map | null>(null)
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (!mapContainer.value) return

  const initialState = { lng: -71.5, lat: 42.15, zoom: 8 }

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
    if (!map.value) return

    map.value.addSource('towns', {
      type: 'geojson',
      data: '/data/towns.geojson',
    })

    map.value.addLayer({
      id: 'towns-fill',
      type: 'fill',
      source: 'towns',
      paint: {
        'fill-color': '#088',
        'fill-opacity': 0.8,
      },
    })

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
  })

  map.value.on('error', (e) => {
    console.error('Map error:', e)
  })

  // ResizeObserver to handle container size changes
  // ResizeObserver to handle container size changes
  resizeObserver = new ResizeObserver(() => {
    map.value?.resize()
  })
  resizeObserver.observe(mapContainer.value)
})

onUnmounted(() => {
  map.value?.remove()
  resizeObserver?.disconnect()
})
</script>

<template>
  <div class="map-wrap">
    <div class="map" ref="mapContainer"></div>
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
</style>
