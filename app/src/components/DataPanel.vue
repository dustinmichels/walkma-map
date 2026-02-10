<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
import { Building2, Check, ChevronDown, Filter, Tag, Users, X } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import type { Audit, Audits } from '../types'
import AuditCard from './AuditCard.vue'
import AuditModal from './AuditModal.vue'

const props = defineProps<{
  selectedCity: string
  audits: Audits | null
}>()

const emit = defineEmits<{
  (e: 'update:selectedCity', value: string): void
  (e: 'filter', value: Audits): void
}>()

// Filter State
const selectedTags = ref<string[]>([])
const selectedYears = ref<string[]>([])
const selectedOrganizer = ref('')

// Helper: Parse themes string to array
const parseThemes = (themesStr: string | undefined): string[] => {
  if (!themesStr) return []
  return themesStr
    .split(',')
    .map((s) => s.trim().replace(/^"|"$/g, ''))
    .filter(Boolean)
}

// Compute available options based on selected city
const baseAuditsForFilters = computed(() => {
  if (!props.audits) return []
  if (props.selectedCity) {
    return props.audits.filter((audit) => audit.city === props.selectedCity)
  }
  return props.audits
})

const availableTags = computed(() => {
  const tags = new Set<string>()
  baseAuditsForFilters.value.forEach((audit) => {
    parseThemes(audit.themes).forEach((tag) => tags.add(tag))
  })
  return Array.from(tags).sort()
})

const availableYears = computed(() => {
  const years = new Set<string>()
  baseAuditsForFilters.value.forEach((audit) => {
    if (audit.year) years.add(audit.year)
  })
  return Array.from(years).sort((a, b) => Number(b) - Number(a))
})

const availableOrganizers = computed(() => {
  const orgs = new Set<string>()
  baseAuditsForFilters.value.forEach((audit) => {
    if (audit.organizer_lead_organization) orgs.add(audit.organizer_lead_organization)
  })
  return Array.from(orgs).sort()
})

// Global filtered audits based on Tags and Year
const globalFilteredAudits = computed(() => {
  if (!props.audits) return []
  return props.audits.filter((audit) => {
    // Filter by Year
    if (selectedYears.value.length > 0) {
      if (!selectedYears.value.includes(audit.year)) return false
    }

    // Filter by Tags (OR logic: if audit has ANY of the selected tags)
    if (selectedTags.value.length > 0) {
      const auditTags = parseThemes(audit.themes)
      const hasMatch = selectedTags.value.some((tag) => auditTags.includes(tag))
      if (!hasMatch) return false
    }

    // Filter by Organizer
    if (selectedOrganizer.value) {
      if (audit.organizer_lead_organization !== selectedOrganizer.value) return false
    }

    return true
  })
})

watch(
  globalFilteredAudits,
  (newVal) => {
    if (!props.audits) return
    emit('filter', newVal)
  },
  { immediate: true }
)

// Modal State
const selectedAudit = ref<Audit | null>(null)
const isAuditModalOpen = ref(false)

const handleViewAudit = (audit: Audit) => {
  selectedAudit.value = audit
  isAuditModalOpen.value = true
}

// Update cities based on globalFilteredAudits
const cities = computed(() => {
  if (!globalFilteredAudits.value) return []

  const cityCounts = new Map<string, number>()

  globalFilteredAudits.value.forEach((audit) => {
    const city = audit.city
    if (city) {
      cityCounts.set(city, (cityCounts.get(city) || 0) + 1)
    }
  })

  // Note: We removed the logic that forced selectedCity to be in the list
  // because the requirement is to "sometimes remove cities entirely".

  return Array.from(cityCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

const filteredAudits = computed(() => {
  if (!props.selectedCity || !globalFilteredAudits.value) return []
  const filtered = globalFilteredAudits.value.filter((audit) => {
    const city = audit.city
    return city === props.selectedCity
  })
  // Sort by date (most recent first)
  return filtered.sort((a, b) => Number(b.year) - Number(a.year))
})

const currentStats = computed(() => {
  if (!props.selectedCity) return null

  const cityAudits = filteredAudits.value

  // Count theme occurrences across all audits for this city
  const themeCounts = new Map<string, number>()
  cityAudits.forEach((audit) => {
    if (audit.themes) {
      audit.themes.split(',').forEach((t) => {
        const theme = t.trim().replace(/"/g, '')
        if (theme) {
          themeCounts.set(theme, (themeCounts.get(theme) || 0) + 1)
        }
      })
    }
  })

  // Top 5 themes by frequency
  const areas = Array.from(themeCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([theme, count]) => ({ theme, count }))

  return {
    audits: cityAudits.length,
    areas,
  }
})

const selectedCityProxy = computed({
  get: () => props.selectedCity,
  set: (val) => emit('update:selectedCity', val),
})

// Navigation Logic
const selectedAuditIndex = computed(() => {
  if (!selectedAudit.value || !filteredAudits.value) return -1
  return filteredAudits.value.indexOf(selectedAudit.value)
})

const hasPrevAudit = computed(() => selectedAuditIndex.value > 0)
// Check if current index is valid and not the last one
const hasNextAudit = computed(() => {
  return (
    selectedAuditIndex.value !== -1 &&
    selectedAuditIndex.value < filteredAudits.value.length - 1
  )
})

const handlePrevAudit = () => {
  if (hasPrevAudit.value) {
    const prev = filteredAudits.value[selectedAuditIndex.value - 1]
    if (prev) selectedAudit.value = prev
  }
}

const handleNextAudit = () => {
  if (hasNextAudit.value) {
    const next = filteredAudits.value[selectedAuditIndex.value + 1]
    if (next) selectedAudit.value = next
  }
}

const clearFilters = () => {
  selectedTags.value = []
  selectedYears.value = []
  selectedOrganizer.value = ''
}

const activeFilterCount = computed(() =>
  selectedTags.value.length + selectedYears.value.length + (selectedOrganizer.value ? 1 : 0)
)
</script>

<template>
  <aside
    class="w-full md:w-[400px] flex flex-col bg-white rounded-xl shadow-xl border border-zinc-200 overflow-hidden h-full relative"
  >
    <!-- Interactive Elements -->
    <div class="flex-grow overflow-y-auto p-5 custom-scrollbar space-y-6">
      <!-- City & Filters Section -->
      <div class="space-y-4 relative z-20">
        <!-- City Selection -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label
              class="block text-sm font-bold text-zinc-600 uppercase tracking-wider"
            >
              Select City
            </label>
            <button
              v-if="selectedCity"
              @click="selectedCityProxy = ''"
              class="text-xs text-brand-orange font-bold hover:underline flex items-center gap-1"
            >
              <X :size="12" /> Deselect City
            </button>
          </div>

          <Listbox v-model="selectedCityProxy">
            <div class="relative mt-1">
              <ListboxButton
                class="relative w-full cursor-pointer bg-white border-2 border-zinc-200 rounded-lg py-3 pl-4 pr-10 text-left focus:outline-none focus-visible:border-brand-orange focus-visible:ring-2 focus-visible:ring-white/75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm hover:border-zinc-300 transition-colors"
                :class="{ 'opacity-50': cities.length === 0 }"
              >
                <span class="block truncate text-base text-zinc-800">
                  {{ selectedCity || 'Choose a city...' }}
                </span>
                <span
                  class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
                >
                  <ChevronDown class="text-zinc-400" :size="16" />
                </span>
              </ListboxButton>

              <transition
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <ListboxOptions
                  class="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-30 custom-scrollbar"
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
                        active
                          ? 'bg-orange-50 text-orange-900'
                          : 'text-zinc-900',
                        'relative cursor-default select-none py-2 pl-10 pr-4',
                      ]"
                    >
                      <span
                        :class="[
                          selected ? 'font-medium' : 'font-normal',
                          'block truncate',
                        ]"
                      >
                        {{ city.name }} ({{ city.count }})
                      </span>
                      <span
                        v-if="selected"
                        class="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-orange"
                      >
                        <Check :size="16" />
                      </span>
                    </li>
                  </ListboxOption>
                  <li
                    v-if="cities.length === 0"
                    class="relative cursor-default select-none py-2 pl-4 pr-4 text-zinc-500 italic text-sm"
                  >
                    No cities match current filters
                  </li>
                </ListboxOptions>
              </transition>
            </div>
          </Listbox>
        </div>

        <!-- Filter Controls -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label
              class="block text-sm font-bold text-zinc-600 uppercase tracking-wider"
            >
              Filter Audits
            </label>
            <button
              v-if="activeFilterCount > 0"
              @click="clearFilters"
              class="text-xs text-brand-orange font-bold hover:underline flex items-center gap-1"
            >
              <X :size="12" /> Clear ({{ activeFilterCount }})
            </button>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <!-- Tags Filter -->
            <Listbox v-model="selectedTags" multiple>
              <div class="relative">
                <ListboxButton
                  class="relative w-full cursor-pointer bg-white border border-zinc-200 rounded-lg py-2 pl-3 pr-8 text-left focus:outline-none focus:border-brand-orange sm:text-xs hover:border-zinc-300 transition-colors h-10"
                >
                  <span class="block truncate text-zinc-700">
                    <span
                      v-if="selectedTags.length > 0"
                      class="flex items-center gap-1"
                    >
                      <span
                        class="bg-orange-100 text-orange-800 px-1.5 rounded font-medium"
                      >
                        {{ selectedTags.length }} matches
                      </span>
                    </span>
                    <span v-else class="text-zinc-500">All Tags</span>
                  </span>
                  <span
                    class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
                  >
                    <Tag class="text-zinc-400" :size="14" />
                  </span>
                </ListboxButton>

                <transition
                  leave-active-class="transition duration-100 ease-in"
                  leave-from-class="opacity-100"
                  leave-to-class="opacity-0"
                >
                  <ListboxOptions
                    class="absolute mt-1 max-h-48 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-50 custom-scrollbar"
                  >
                    <ListboxOption
                      v-slot="{ active, selected }"
                      v-for="tag in availableTags"
                      :key="tag"
                      :value="tag"
                      as="template"
                    >
                      <li
                        :class="[
                          active
                            ? 'bg-orange-50 text-orange-900'
                            : 'text-zinc-900',
                          'relative cursor-default select-none py-2 pl-9 pr-4 text-xs',
                        ]"
                      >
                        <span
                          :class="[
                            selected ? 'font-medium' : 'font-normal',
                            'block truncate',
                          ]"
                        >
                          {{ tag }}
                        </span>
                        <span
                          v-if="selected"
                          class="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-orange"
                        >
                          <Check :size="14" />
                        </span>
                      </li>
                    </ListboxOption>
                  </ListboxOptions>
                </transition>
              </div>
            </Listbox>

            <!-- Year Filter -->
            <Listbox v-model="selectedYears" multiple>
              <div class="relative">
                <ListboxButton
                  class="relative w-full cursor-pointer bg-white border border-zinc-200 rounded-lg py-2 pl-3 pr-8 text-left focus:outline-none focus:border-brand-orange sm:text-xs hover:border-zinc-300 transition-colors h-10"
                >
                  <span class="block truncate text-zinc-700">
                    <span
                      v-if="selectedYears.length > 0"
                      class="flex items-center gap-1"
                    >
                      <span
                        class="bg-orange-100 text-orange-800 px-1.5 rounded font-medium"
                      >
                        {{ selectedYears.join(', ') }}
                      </span>
                    </span>
                    <span v-else class="text-zinc-500">All Years</span>
                  </span>
                  <span
                    class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
                  >
                    <Filter class="text-zinc-400" :size="14" />
                  </span>
                </ListboxButton>

                <transition
                  leave-active-class="transition duration-100 ease-in"
                  leave-from-class="opacity-100"
                  leave-to-class="opacity-0"
                >
                  <ListboxOptions
                    class="absolute mt-1 max-h-48 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-50 custom-scrollbar"
                  >
                    <ListboxOption
                      v-slot="{ active, selected }"
                      v-for="year in availableYears"
                      :key="year"
                      :value="year"
                      as="template"
                    >
                      <li
                        :class="[
                          active
                            ? 'bg-orange-50 text-orange-900'
                            : 'text-zinc-900',
                          'relative cursor-default select-none py-2 pl-9 pr-4 text-xs',
                        ]"
                      >
                        <span
                          :class="[
                            selected ? 'font-medium' : 'font-normal',
                            'block truncate',
                          ]"
                        >
                          {{ year }}
                        </span>
                        <span
                          v-if="selected"
                          class="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-orange"
                        >
                          <Check :size="14" />
                        </span>
                      </li>
                    </ListboxOption>
                  </ListboxOptions>
                </transition>
              </div>
            </Listbox>

            <!-- Organizer Filter -->
            <Listbox v-model="selectedOrganizer">
              <div class="relative">
                <ListboxButton
                  class="relative w-full cursor-pointer bg-white border border-zinc-200 rounded-lg py-2 pl-3 pr-8 text-left focus:outline-none focus:border-brand-orange sm:text-xs hover:border-zinc-300 transition-colors h-10"
                >
                  <span class="block truncate text-zinc-700">
                    <span
                      v-if="selectedOrganizer"
                      class="bg-orange-100 text-orange-800 px-1.5 rounded font-medium"
                    >
                      {{ selectedOrganizer }}
                    </span>
                    <span v-else class="text-zinc-500">All Orgs</span>
                  </span>
                  <span
                    class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
                  >
                    <Users class="text-zinc-400" :size="14" />
                  </span>
                </ListboxButton>

                <transition
                  leave-active-class="transition duration-100 ease-in"
                  leave-from-class="opacity-100"
                  leave-to-class="opacity-0"
                >
                  <ListboxOptions
                    class="absolute right-0 mt-1 max-h-48 w-56 overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-50 custom-scrollbar"
                  >
                    <ListboxOption
                      v-slot="{ active }"
                      :value="''"
                      as="template"
                    >
                      <li
                        :class="[
                          active
                            ? 'bg-orange-50 text-orange-900'
                            : 'text-zinc-500',
                          'relative cursor-default select-none py-2 pl-9 pr-4 text-xs italic',
                        ]"
                      >
                        All Organizations
                      </li>
                    </ListboxOption>
                    <ListboxOption
                      v-slot="{ active, selected }"
                      v-for="org in availableOrganizers"
                      :key="org"
                      :value="org"
                      as="template"
                    >
                      <li
                        :class="[
                          active
                            ? 'bg-orange-50 text-orange-900'
                            : 'text-zinc-900',
                          'relative cursor-default select-none py-2 pl-9 pr-4 text-xs',
                        ]"
                      >
                        <span
                          :class="[
                            selected ? 'font-medium' : 'font-normal',
                            'block truncate',
                          ]"
                        >
                          {{ org }}
                        </span>
                        <span
                          v-if="selected"
                          class="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-orange"
                        >
                          <Check :size="14" />
                        </span>
                      </li>
                    </ListboxOption>
                  </ListboxOptions>
                </transition>
              </div>
            </Listbox>
          </div>
        </div>
      </div>

      <!-- Statistics / Info Cards (Dynamic) -->
      <div
        v-if="selectedCity && currentStats"
        class="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
      >
        <div
          v-if="currentStats.audits === 0"
          class="h-64 flex flex-col items-center justify-center text-center border-2 border-dashed border-zinc-100 rounded-xl bg-orange-50/30"
        >
          <p class="text-lg font-medium text-zinc-700 mb-2">
            Hey! You could do a walk audit here!
          </p>
          <p
            v-if="activeFilterCount > 0"
            class="text-xs text-zinc-500 mb-2"
          >
            (No audits found matching your filters)
          </p>
          <a
            href="https://walkmass.org/walk-audit-academy/"
            target="_blank"
            class="text-brand-orange font-bold hover:underline"
          >
            Learn how
          </a>
        </div>

        <template v-else>
          <div
            class="px-4 py-2 rounded-lg bg-orange-50 border-l-4 border-brand-orange flex items-center justify-between"
          >
            <h3 class="font-bold text-brand-orange text-sm uppercase">
              Audits To Date
            </h3>
            <p class="text-2xl font-black text-black">
              {{ currentStats.audits }}
            </p>
          </div>

          <!-- Render list of audits -->
          <div class="mt-6">
            <h4 class="text-sm font-bold text-zinc-700 uppercase mb-3">
              Audits
            </h4>
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
            <h4 class="text-xs font-bold text-zinc-500 uppercase mb-3">
              Key Themes
            </h4>
            <ul class="space-y-2">
              <li
                v-for="area in currentStats.areas"
                :key="area.theme"
                class="flex items-center gap-2 text-sm p-2 bg-white border border-zinc-100 rounded hover:shadow-sm transition-shadow"
              >
                <Tag class="text-brand-orange flex-shrink-0" :size="12" />
                <span class="flex-1">{{ area.theme }}</span>
                <span class="text-xs text-zinc-400 font-medium"
                  >(x{{ area.count }})</span
                >
              </li>
            </ul>
          </div>
        </template>
      </div>

      <!-- Placeholder if no city selected -->
      <div
        v-else
        class="h-64 flex flex-col items-center justify-center text-zinc-400 text-center border-2 border-dashed border-zinc-100 rounded-xl"
      >
        <Building2 class="text-zinc-400 mb-3 opacity-20" :size="36" />
        <p class="text-sm">
          Select a city from the menu above to discover its walk audits
        </p>
      </div>
    </div>

    <!-- Modal -->
    <AuditModal
      :isOpen="isAuditModalOpen"
      :audit="selectedAudit"
      :hasPrev="hasPrevAudit"
      :hasNext="hasNextAudit"
      @close="isAuditModalOpen = false"
      @prev="handlePrevAudit"
      @next="handleNextAudit"
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
