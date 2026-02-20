<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AuditFilters from './components/AuditFilters.vue'
import DataPanel from './components/DataPanel.vue'
import Map from './components/Map.vue'
import ThemeChart from './components/ThemeChart.vue'
import type { Audits } from './types'

const selectedCity = ref('')
const audits = ref<Audits | null>(null)
const filteredAudits = ref<Audits | null>(null)
const selectedTags = ref<string[]>([])

const handleFilter = (filtered: Audits) => {
  filteredAudits.value = filtered
}

const handleThemeClick = (theme: string) => {
  if (selectedTags.value.includes(theme)) {
    selectedTags.value = selectedTags.value.filter((t) => t !== theme)
  } else {
    selectedTags.value = [...selectedTags.value, theme]
  }
}

// Compute audits relevant to the chart (includes city filter)
const relevantAudits = computed(() => {
  const base = filteredAudits.value || audits.value
  if (!base) return null
  if (selectedCity.value) {
    return base.filter((a) => a.city === selectedCity.value)
  }
  return base
})

onMounted(async () => {
  try {
    const response = await fetch('/.netlify/functions/gsheet')
    if (!response.ok) {
      const text = await response.text()
      console.error(`gsheet function returned ${response.status}:`, text)
      return
    }
    audits.value = await response.json()
  } catch (error) {
    console.error('Failed to load audits data:', error)
  }
})
</script>

<template>
  <div class="h-screen overflow-hidden flex flex-col font-sans text-slate-900">
    <!-- Header -->
    <header
      class="bg-brand-orange shadow-lg py-2 px-4 flex justify-between items-center z-10"
    >
      <div class="flex items-center gap-2">
        <div class="bg-black p-1.5 rounded-lg">
          <i class="fas fa-walking text-white text-lg"></i>
        </div>
        <h1 class="text-white text-lg font-bold tracking-tight">
          Walk MA - Walk Audit Dashboard
        </h1>
      </div>
    </header>

    <!-- Main Content Area -->
    <main
      class="flex-grow flex flex-col md:flex-row p-2 md:p-4 gap-4 overflow-hidden"
    >
      <!-- Left Side: Map & Chart -->
      <div class="flex-grow flex flex-col gap-4 overflow-hidden h-full min-w-0">
        <!-- Map -->
        <div
          class="flex-grow relative rounded-xl overflow-hidden border-2 border-zinc-200 bg-white shadow-inner group min-h-0"
        >
          <Map
            :audits="filteredAudits || audits"
            v-model:selectedCity="selectedCity"
          />
        </div>

        <!-- Chart -->
        <div class="h-48 flex-shrink-0">
          <ThemeChart
            :audits="relevantAudits"
            :all-audits="audits"
            :selected-tags="selectedTags"
            @select="handleThemeClick"
          />
        </div>
      </div>

      <!-- Right Side: Data Panel & Filters -->
      <div
        class="flex-shrink-0 w-full md:w-[420px] flex flex-col gap-2 h-full min-w-0"
      >
        <AuditFilters
          :audits="audits"
          v-model:selectedCity="selectedCity"
          v-model:selectedTags="selectedTags"
          @filter="handleFilter"
        />
        <DataPanel :audits="relevantAudits" />
      </div>
    </main>

    <!-- Footer -->
    <footer
      class="bg-zinc-900 text-zinc-500 py-3 px-6 text-xs flex justify-between"
    >
      <p>&copy; 2026 WalkMA</p>
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
