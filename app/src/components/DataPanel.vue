<script setup lang="ts">
import { computed } from 'vue'
import type { Audits, AuditFeature } from '../types'
import AuditCard from './AuditCard.vue'

const props = defineProps<{
  selectedCity: string
  audits: Audits | null
}>()

const emit = defineEmits<{
  (e: 'update:selectedCity', value: string): void
}>()

const cities = computed(() => {
  if (!props.audits?.features) return []
  const uniqueCities = new Set<string>()
  props.audits.features.forEach((feature) => {
    const city = feature.properties.CITY
    if (city) uniqueCities.add(city)
  })
  return Array.from(uniqueCities).sort()
})

const filteredAudits = computed(() => {
  if (!props.selectedCity || !props.audits?.features) return []
  const filtered = props.audits.features.filter((feature) => {
    const city = feature.properties.CITY
    return city === props.selectedCity
  })
  // Sort by date (most recent first)
  return filtered.sort((a, b) => b.properties.YEAR - a.properties.YEAR)
})

const currentStats = computed(() => {
  if (!props.selectedCity) return null

  const cityAudits = filteredAudits.value
  const participants = cityAudits.reduce((acc, feat) => {
    // Estimating participants if not explicitly available, relying on summary text logic would be too complex here without NLP stats.
    // However, none of the properties strictly give a "participant count".
    // We can count distinct authors/facilitators maybe? Or keep hardcoded random-ish logic?
    // Let's just return the number of audits for count.
    return acc
  }, 0)

  // Extract unique themes as "focus areas"
  const allThemes = new Set<string>()
  cityAudits.forEach((audit) => {
    if (audit.properties.THEMES) {
      audit.properties.THEMES.split(',').forEach((t) => allThemes.add(t.trim().replace(/"/g, '')))
    }
  })

  return {
    audits: cityAudits.length,
    score: Math.floor(Math.random() * 40) + 60, // Placeholder score as it's not in the data
    users: 'N/A', // Not readily available in GeoJSON stats without parsing text
    areas: Array.from(allThemes).slice(0, 5), // Top 5 themes
  }
})
</script>

<template>
  <aside
    class="w-full md:w-[400px] flex flex-col bg-white rounded-xl shadow-xl border border-zinc-200 overflow-hidden h-full"
  >
    <!-- Interactive Elements -->
    <div class="flex-grow overflow-y-auto p-5 custom-scrollbar space-y-6">
      <!-- City Selection -->
      <div class="space-y-2">
        <label
          for="city-select"
          class="block text-sm font-bold text-zinc-600 uppercase tracking-wider"
        >
          Select City
        </label>
        <div class="relative">
          <select
            id="city-select"
            :value="selectedCity"
            @change="emit('update:selectedCity', ($event.target as HTMLSelectElement).value)"
            class="w-full appearance-none bg-white border-2 border-zinc-200 rounded-lg py-3 px-4 focus:outline-none focus:border-brand-orange transition-colors cursor-pointer pr-10"
          >
            <option value="" disabled>Choose a city...</option>
            <option v-for="city in cities" :key="city" :value="city">
              {{ city }}
            </option>
          </select>
          <div
            class="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-zinc-400"
          >
            <i class="fas fa-chevron-down"></i>
          </div>
        </div>
      </div>

      <!-- Statistics / Info Cards (Dynamic) -->
      <div
        v-if="selectedCity && currentStats"
        class="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
      >
        <div class="p-4 rounded-lg bg-orange-50 border-l-4 border-brand-orange">
          <h3 class="font-bold text-brand-orange text-sm uppercase">Active Audits</h3>
          <p class="text-3xl font-black text-black">
            {{ currentStats.audits }}
          </p>
        </div>

        <!-- Render list of audits -->
        <div class="mt-6">
          <h4 class="text-sm font-bold text-zinc-700 uppercase mb-3">Recent Reports</h4>
          <div class="space-y-4">
            <AuditCard v-for="(audit, index) in filteredAudits" :key="index" :audit="audit" />
          </div>
        </div>

        <div class="pt-4" v-if="currentStats.areas.length > 0">
          <h4 class="text-xs font-bold text-zinc-500 uppercase mb-3">Key Themes</h4>
          <ul class="space-y-2">
            <li
              v-for="area in currentStats.areas"
              :key="area"
              class="flex items-center gap-2 text-sm p-2 bg-white border border-zinc-100 rounded hover:shadow-sm transition-shadow"
            >
              <i class="fas fa-tag text-brand-orange text-xs"></i>
              {{ area }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Placeholder if no city selected -->
      <div
        v-else
        class="h-64 flex flex-col items-center justify-center text-zinc-400 text-center border-2 border-dashed border-zinc-100 rounded-xl"
      >
        <i class="fas fa-city text-4xl mb-3 opacity-20"></i>
        <p class="text-sm">
          Select a city from the menu above to view walk audit metrics and geospatial data layers.
        </p>
      </div>
    </div>

    <!-- Footer Action -->
    <div class="p-5 bg-zinc-50 border-t border-zinc-100">
      <button
        :disabled="!selectedCity"
        class="w-full py-3 rounded-lg font-bold text-white transition-all transform active:scale-95 shadow-lg"
        :class="selectedCity ? 'bg-black hover:bg-zinc-800' : 'bg-zinc-300 cursor-not-allowed'"
      >
        Export PDF Report
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* Custom Scrollbar for the Data Panel */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #ffa100;
}
</style>
