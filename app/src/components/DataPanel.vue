<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Audit, Audits } from '../types'
import AuditCard from './AuditCard.vue'
import AuditModal from './AuditModal.vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'

const props = defineProps<{
  selectedCity: string
  audits: Audits | null
}>()

const emit = defineEmits<{
  (e: 'update:selectedCity', value: string): void
}>()

// Modal State
const selectedAudit = ref<Audit | null>(null)
const isAuditModalOpen = ref(false)

const handleViewAudit = (audit: Audit) => {
  selectedAudit.value = audit
  isAuditModalOpen.value = true
}

const cities = computed(() => {
  if (!props.audits) return []

  const cityCounts = new Map<string, number>()

  props.audits.forEach((audit) => {
    const city = audit.CITY
    if (city) {
      cityCounts.set(city, (cityCounts.get(city) || 0) + 1)
    }
  })

  // Ensure selectedCity is in the list even if it has no audits
  if (props.selectedCity && !cityCounts.has(props.selectedCity)) {
    cityCounts.set(props.selectedCity, 0)
  }

  return Array.from(cityCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

const filteredAudits = computed(() => {
  if (!props.selectedCity || !props.audits) return []
  const filtered = props.audits.filter((audit) => {
    const city = audit.CITY
    return city === props.selectedCity
  })
  // Sort by date (most recent first)
  return filtered.sort((a, b) => b.YEAR - a.YEAR)
})

const currentStats = computed(() => {
  if (!props.selectedCity) return null

  const cityAudits = filteredAudits.value

  // Extract unique themes as "focus areas"
  const allThemes = new Set<string>()
  cityAudits.forEach((audit) => {
    if (audit.THEMES) {
      audit.THEMES.split(',').forEach((t) => allThemes.add(t.trim().replace(/"/g, '')))
    }
  })

  return {
    audits: cityAudits.length,
    areas: Array.from(allThemes).slice(0, 5), // Top 5 themes
  }
})

const selectedCityProxy = computed({
  get: () => props.selectedCity,
  set: (val) => emit('update:selectedCity', val),
})
</script>

<template>
  <aside
    class="w-full md:w-[400px] flex flex-col bg-white rounded-xl shadow-xl border border-zinc-200 overflow-hidden h-full relative"
  >
    <!-- Interactive Elements -->
    <div class="flex-grow overflow-y-auto p-5 custom-scrollbar space-y-6">
      <!-- City Selection -->
      <div class="space-y-2 relative z-20">
        <label class="block text-sm font-bold text-zinc-600 uppercase tracking-wider">
          Select City
        </label>

        <Listbox v-model="selectedCityProxy">
          <div class="relative mt-1">
            <ListboxButton
              class="relative w-full cursor-pointer bg-white border-2 border-zinc-200 rounded-lg py-3 pl-4 pr-10 text-left focus:outline-none focus-visible:border-brand-orange focus-visible:ring-2 focus-visible:ring-white/75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm hover:border-zinc-300 transition-colors"
            >
              <span class="block truncate text-base text-zinc-800">
                {{ selectedCity || 'Choose a city...' }}
              </span>
              <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <i class="fas fa-chevron-down text-zinc-400"></i>
              </span>
            </ListboxButton>

            <transition
              leave-active-class="transition duration-100 ease-in"
              leave-from-class="opacity-100"
              leave-to-class="opacity-0"
            >
              <ListboxOptions
                class="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-50 custom-scrollbar"
              >
                <ListboxOption
                  v-slot="{ active, selected }"
                  v-for="city in cities"
                  :key="city.name"
                  :value="city.name"
                  as="template"
                >
                  <li
                    :class="[
                      active ? 'bg-orange-50 text-orange-900' : 'text-zinc-900',
                      'relative cursor-default select-none py-2 pl-10 pr-4',
                    ]"
                  >
                    <span :class="[selected ? 'font-medium' : 'font-normal', 'block truncate']">
                      {{ city.name }} ({{ city.count }})
                    </span>
                    <span
                      v-if="selected"
                      class="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-orange"
                    >
                      <i class="fas fa-check"></i>
                    </span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </transition>
          </div>
        </Listbox>
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
            <AuditCard
              v-for="(audit, index) in filteredAudits"
              :key="index"
              :audit="audit"
              @view="handleViewAudit"
            />
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
        <p class="text-sm">Select a city from the menu above to discover its walk audits</p>
      </div>
    </div>

    <!-- Modal -->
    <AuditModal
      :isOpen="isAuditModalOpen"
      :audit="selectedAudit"
      @close="isAuditModalOpen = false"
    />
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
