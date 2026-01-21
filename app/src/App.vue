<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Map from './components/Map.vue'
import DataPanel from './components/DataPanel.vue'
import type { Audits } from './types'

const selectedCity = ref('')
const audits = ref<Audits | null>(null)

onMounted(async () => {
  try {
    const response = await fetch('/data/audits.geojson')
    audits.value = await response.json()
  } catch (error) {
    console.error('Failed to load audits data:', error)
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col font-sans text-slate-900">
    <!-- Header -->
    <header class="bg-brand-orange shadow-lg py-4 px-6 flex justify-between items-center z-10">
      <div class="flex items-center gap-3">
        <div class="bg-black p-2 rounded-lg">
          <i class="fas fa-walking text-white text-2xl"></i>
        </div>
        <h1 class="text-white text-2xl font-bold tracking-tight">Walk MA - Walk Audit Dashboard</h1>
      </div>
    </header>

    <!-- Main Content Area -->
    <main
      class="flex-grow flex flex-col md:flex-row p-4 md:p-6 gap-6 h-[calc(100vh-72px)] overflow-hidden"
    >
      <!-- Left Side: Map Placeholder -->
      <div
        class="flex-grow relative rounded-xl overflow-hidden border-2 border-zinc-200 bg-zinc-100 shadow-inner group"
      >
        <Map :audits="audits" v-model:selectedCity="selectedCity" />
      </div>

      <!-- Right Side: Data Panel -->
      <DataPanel v-model:selectedCity="selectedCity" :audits="audits" />
    </main>

    <!-- Footer -->
    <footer class="bg-zinc-900 text-zinc-500 py-3 px-6 text-xs flex justify-between">
      <p>&copy; 2024 MassDOT Walkability Initiative</p>
      <div class="flex gap-4">
        <a href="#" class="hover:text-white">Privacy Policy</a>
        <a href="#" class="hover:text-white">Data Sources</a>
      </div>
    </footer>
  </div>
</template>

<style>
/* Global overrides if necessary, but try to use utility classes */
body {
  margin: 0;
}
</style>
