<script setup lang="ts">
import { Pane, Splitpanes } from 'splitpanes'
import { computed, onMounted, ref } from 'vue'
import { Menu } from 'lucide-vue-next'
import { isMenuOpen } from '../state'
import AuditFilters from '../components/AuditFilters.vue'
import DataPanel from '../components/DataPanel.vue'
import Map from '../components/Map.vue'
import ThemeChart from '../components/ThemeChart.vue'
import type { Audits, Towns } from '../types'

const selectedCity = ref('')
const audits = ref<Audits | null>(null)
const filteredAudits = ref<Audits | null>(null)
const selectedTags = ref<string[]>([])
const allTownNames = ref<string[]>([])
const fallbackDate = ref<string | null>(null)

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

const relevantAudits = computed(() => {
  const base = filteredAudits.value || audits.value
  if (!base) return null
  if (selectedCity.value) {
    return base.filter((a) => a.city === selectedCity.value)
  }
  return base
})

async function loadAudits() {
  try {
    const res = await fetch('/.netlify/functions/gsheet')
    if (!res.ok) throw new Error(`gsheet returned ${res.status}`)
    audits.value = await res.json()
  } catch (err) {
    console.warn('Live fetch failed, falling back to last_run.json:', err)
    try {
      const fallbackRes = await fetch('/data/last_run.json')
      if (!fallbackRes.ok) throw new Error(`last_run.json returned ${fallbackRes.status}`)
      const fallback = await fallbackRes.json()
      audits.value = fallback.data
      fallbackDate.value = fallback.date
    } catch (fallbackErr) {
      console.error('Fallback also failed:', fallbackErr)
    }
  }
}

onMounted(async () => {
  await Promise.all([
    loadAudits(),
    fetch('/data/towns.geojson')
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((townsData: Towns) => {
        allTownNames.value = (townsData.features ?? [])
          .map((f) => f.properties.CITY || (f.properties as any).TOWN)
          .filter(Boolean)
          .sort()
      })
      .catch((err) => console.error('Failed to load towns:', err)),
  ])
})
</script>

<template>
  <div class="h-screen overflow-hidden flex flex-col font-sans text-slate-900">
    <!-- Header -->
    <header
      class="bg-brand-orange shadow-lg py-2 px-4 flex justify-between items-center z-10 flex-shrink-0"
    >
      <div class="flex items-center gap-2">
        <div class="bg-black p-1.5 rounded-lg">
          <i class="fas fa-walking text-white text-lg"></i>
        </div>
        <h1 class="text-white text-lg font-bold tracking-tight">
          Walk MA - Walk Audit Dashboard
        </h1>
      </div>
      <button
        @click="isMenuOpen = true"
        class="text-white hover:bg-black/20 p-2 rounded-lg transition-colors ml-4"
        aria-label="Open menu"
      >
        <Menu :size="24" />
      </button>
    </header>

    <!-- Main Content Area -->
    <main class="flex-grow overflow-hidden">
      <Splitpanes class="h-full">
        <!-- Left: Filters + DataPanel -->
        <Pane :size="35" :min-size="20">
          <div class="h-full flex flex-col shadow-sm">
            <div class="flex-none z-10 w-full">
              <AuditFilters
                :audits="audits"
                :all-town-names="allTownNames"
                v-model:selectedCity="selectedCity"
                v-model:selectedTags="selectedTags"
                @filter="handleFilter"
              />
            </div>
            <div class="flex-grow flex flex-col min-h-0 relative z-0">
              <DataPanel :audits="relevantAudits" :selected-tags="selectedTags" />
            </div>
          </div>
        </Pane>

        <!-- Right: Map + Chart -->
        <Pane :size="65" :min-size="30">
          <Splitpanes horizontal class="h-full">
            <Pane :size="72" :min-size="20">
              <div class="h-full w-full relative">
                <Map
                  :audits="filteredAudits || audits"
                  v-model:selectedCity="selectedCity"
                />
              </div>
            </Pane>
            <Pane :size="28" :min-size="10">
              <div class="h-full w-full">
                <ThemeChart
                  :audits="relevantAudits"
                  :all-audits="audits"
                  :selected-tags="selectedTags"
                  @select="handleThemeClick"
                />
              </div>
            </Pane>
          </Splitpanes>
        </Pane>
      </Splitpanes>
    </main>

    <div
      v-if="fallbackDate"
      class="fixed bottom-3 right-3 z-50 bg-red-600 text-white text-xs px-3 py-1.5 rounded shadow-lg"
    >
      data last refreshed: {{ new Date(fallbackDate).toLocaleString() }}
    </div>
  </div>
</template>
