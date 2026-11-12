<script setup lang="ts">
import { Menu } from 'lucide-vue-next'
import { Pane, Splitpanes } from 'splitpanes'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AuditFilters from '../components/AuditFilters.vue'
import AuditSearch from '../components/AuditSearch.vue'
import DataPanel from '../components/DataPanel.vue'
import Map from '../components/Map.vue'
import ThemeChart from '../components/ThemeChart.vue'
import { loadAudits, loadTowns } from '../data'
import { isMenuOpen } from '../state'
import type { Audits } from '../types'

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

// Esc clears the selected town, unless an open dialog/dropdown handled it
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key !== 'Escape' || e.defaultPrevented || !selectedCity.value) return
  if (document.querySelector('[role="dialog"]')) return
  selectedCity.value = ''
}

onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  await Promise.all([
    loadAudits()
      .then((result) => {
        audits.value = result.audits
        fallbackDate.value = result.fallbackDate
      })
      .catch((err) => console.error('Failed to load audits:', err)),
    loadTowns()
      .then((townsData) => {
        allTownNames.value = (townsData.features ?? [])
          .map((f) => f.properties.CITY)
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
      <div class="flex-1 max-w-md ml-4">
        <AuditSearch :audits="audits" />
      </div>
      <button
        @click="isMenuOpen = true"
        class="text-white hover:bg-black/20 p-2 rounded-lg transition-colors ml-4 flex-shrink-0"
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
              <DataPanel
                :audits="relevantAudits"
                :selected-tags="selectedTags"
              />
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
