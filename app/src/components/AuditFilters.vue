<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
import { Check, ChevronDown, ListFilter, Tag, Users, X } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import type { Audits } from '../types'

const props = defineProps<{
  audits: Audits | null
  selectedCity: string
}>()

const emit = defineEmits<{
  (e: 'update:selectedCity', value: string): void
  (e: 'filter', value: Audits): void
}>()

// Filter State
const selectedTags = defineModel<string[]>('selectedTags', {
  default: () => [],
})
const selectedMaxYear = ref<number | null>(null)
const selectedOrganizer = ref('')
const yearFilterMode = ref<'through' | 'in'>('through')

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

const yearRange = computed(() => {
  if (!props.audits) return { min: 0, max: 0 }
  const years: number[] = []
  props.audits.forEach((audit) => {
    if (audit.year) years.push(Number(audit.year))
  })
  if (years.length === 0) return { min: 0, max: 0 }
  return { min: Math.min(...years), max: Math.max(...years) }
})

// Initialize slider to max year (show all) when data loads
watch(yearRange, (range) => {
  if (range.max > 0 && selectedMaxYear.value === null) {
    selectedMaxYear.value = range.max
  }
})

// Helper to filter a list of audits by Year
const filterByYear = (
  audits: Audits,
  maxYear: number | null,
  mode: 'through' | 'in'
) => {
  if (maxYear === null || yearRange.value.max === 0) return audits
  return audits.filter((a) => {
    const y = Number(a.year)
    if (mode === 'in') return y === maxYear
    return y <= maxYear
  })
}

// Helper to filter by Tags
const filterByTags = (audits: Audits, tags: string[]) => {
  if (tags.length === 0) return audits
  return audits.filter((a) => {
    const auditTags = parseThemes(a.themes)
    return tags.every((tag) => auditTags.includes(tag))
  })
}

// Helper to filter by Organizer
const filterByOrganizer = (audits: Audits, org: string) => {
  if (!org) return audits
  return audits.filter((a) => a.organizer_lead_organization === org)
}

const availableTags = computed(() => {
  // Start with base (City)
  let audits = baseAuditsForFilters.value
  // Filter by Year
  audits = filterByYear(audits, selectedMaxYear.value, yearFilterMode.value)
  // Filter by Organizer (so tags are relevant to selected org)
  audits = filterByOrganizer(audits, selectedOrganizer.value)

  const tags = new Set<string>()
  audits.forEach((audit) => {
    parseThemes(audit.themes).forEach((tag) => tags.add(tag))
  })
  return Array.from(tags).sort()
})

const availableOrganizers = computed(() => {
  // Start with base (City)
  let audits = baseAuditsForFilters.value
  // Filter by Year
  audits = filterByYear(audits, selectedMaxYear.value, yearFilterMode.value)
  // Filter by Tags (so orgs are relevant to selected tags)
  audits = filterByTags(audits, selectedTags.value)

  const orgs = new Set<string>()
  audits.forEach((audit) => {
    if (audit.organizer_lead_organization)
      orgs.add(audit.organizer_lead_organization)
  })
  return Array.from(orgs).sort()
})

// Global filtered audits based on Tags, Year, Organizer AND City
const filteredAudits = computed(() => {
  if (!props.audits) return []
  let result = props.audits.filter((audit) => {
    // Filter by Year
    if (selectedMaxYear.value !== null && yearRange.value.max > 0) {
      if (yearFilterMode.value === 'in') {
        if (Number(audit.year) !== selectedMaxYear.value) return false
      } else {
        if (Number(audit.year) > selectedMaxYear.value) return false
      }
    }

    // Filter by Tags (AND logic: audit must have ALL selected tags)
    if (selectedTags.value.length > 0) {
      const auditTags = parseThemes(audit.themes)
      const hasMatch = selectedTags.value.every((tag) =>
        auditTags.includes(tag)
      )
      if (!hasMatch) return false
    }

    // Filter by Organizer
    if (selectedOrganizer.value) {
      if (audit.organizer_lead_organization !== selectedOrganizer.value)
        return false
    }

    return true
  })

  // Filter by City
  if (props.selectedCity) {
    result = result.filter((audit) => audit.city === props.selectedCity)
  }

  // Sort by date (most recent first)
  return result.sort((a, b) => Number(b.year) - Number(a.year))
})

// Note: In the original DataPanel, 'globalFilteredAudits' (without city filter)
// was watched to emit 'filter'. 'filteredAudits' (with city) was used for display.
// Here we are emitting the FINAL filtered list (including city) to be displayed by DataPanel.
// However, the Map and Chart might expect 'global' filters ignoring city?
// Original App.vue:
// relevantAudits = filteredAudits.value || audits.value.
// If selectedCity, it filters base.
// So App.vue expected 'filteredAudits' to be mostly global?
// Let's re-read DataPanel.
// DataPanel emit('filter', newVal) where newVal is globalFilteredAudits (NO city filter).
// Then App.vue computes `relevantAudits` which ADDS city filter if needed.
// AND Map.vue takes `filteredAudits || audits`. Map.vue usually wants to show all dots,
// but highlight selected city. If we pass it only the selected city's audits, the other dots disappear.
//
// So, we should emit the audits filtered by Tags/Year/Org but NOT City.
// Call it 'contentFilteredAudits'.

const contentFilteredAudits = computed(() => {
  if (!props.audits) return []
  return props.audits.filter((audit) => {
    // Filter by Year
    if (selectedMaxYear.value !== null && yearRange.value.max > 0) {
      if (yearFilterMode.value === 'in') {
        if (Number(audit.year) !== selectedMaxYear.value) return false
      } else {
        if (Number(audit.year) > selectedMaxYear.value) return false
      }
    }
    // Filter by Tags
    if (selectedTags.value.length > 0) {
      const auditTags = parseThemes(audit.themes)
      const hasMatch = selectedTags.value.every((tag) =>
        auditTags.includes(tag)
      )
      if (!hasMatch) return false
    }
    // Filter by Organizer
    if (selectedOrganizer.value) {
      if (audit.organizer_lead_organization !== selectedOrganizer.value)
        return false
    }
    return true
  })
})

watch(
  contentFilteredAudits,
  (newVal) => {
    emit('filter', newVal)
  },
  { immediate: true }
)

// For the City Listbox: compute cities from contentFilteredAudits
// (This matches lines 137-155 in DataPanel)
const cities = computed(() => {
  if (!contentFilteredAudits.value) return []

  const cityCounts = new Map<string, number>()

  contentFilteredAudits.value.forEach((audit) => {
    const city = audit.city
    if (city) {
      cityCounts.set(city, (cityCounts.get(city) || 0) + 1)
    }
  })

  return Array.from(cityCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

const selectedCityProxy = computed({
  get: () => props.selectedCity,
  set: (val) => emit('update:selectedCity', val),
})

const clearFilters = () => {
  selectedCityProxy.value = ''
  selectedTags.value = []
  selectedMaxYear.value = yearRange.value.max || null
  selectedOrganizer.value = ''
  yearFilterMode.value = 'through'
}

const resetYear = () => {
  selectedMaxYear.value = yearRange.value.max || null
  yearFilterMode.value = 'through'
}

const isYearFiltered = computed(() => {
  if (selectedMaxYear.value === null || yearRange.value.max === 0) return false
  if (yearFilterMode.value === 'in') return true
  return selectedMaxYear.value < yearRange.value.max
})

const activeFilterCount = computed(
  () =>
    selectedTags.value.length +
    (isYearFiltered.value ? 1 : 0) +
    (selectedOrganizer.value ? 1 : 0) +
    (props.selectedCity ? 1 : 0)
)
</script>

<template>
  <div
    class="bg-white rounded-xl shadow-xl border border-zinc-200 p-2 bg-zinc-50 space-y-2"
  >
    <!-- Header -->
    <div class="flex items-center justify-between">
      <label
        class="flex items-center gap-1.5 text-xs font-bold text-zinc-600 uppercase tracking-wider"
      >
        <ListFilter :size="16" />
        Filter
      </label>
      <div class="flex items-center gap-3">
        <button
          v-if="activeFilterCount > 0"
          @click="clearFilters"
          class="px-2 py-0.5 text-xs text-brand-orange font-bold rounded hover:bg-orange-50 transition-colors"
        >
          Reset All
        </button>
      </div>
    </div>

    <!-- City Selection -->
    <div class="space-y-2">
      <Listbox v-model="selectedCityProxy">
        <div class="flex items-center gap-2 mt-1">
          <div class="relative flex-grow">
            <ListboxButton
              class="relative w-full cursor-pointer bg-white border border-zinc-200 rounded-lg py-1.5 pl-3 pr-8 text-left focus:outline-none focus-visible:border-brand-orange focus-visible:ring-2 focus-visible:ring-white/75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 text-xs sm:text-sm hover:border-zinc-300 transition-colors"
              :class="{ 'opacity-50': cities.length === 0 }"
            >
              <span class="block truncate text-sm text-zinc-800">
                {{ selectedCity || 'All Cities' }}
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
                      active ? 'bg-orange-50 text-orange-900' : 'text-zinc-900',
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

          <button
            @click="selectedCityProxy = ''"
            :disabled="!selectedCity"
            class="p-1.5 rounded-md hover:bg-zinc-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Clear city selection"
          >
            <X
              :size="20"
              :class="selectedCity ? 'text-brand-orange' : 'text-zinc-300'"
            />
          </button>
        </div>
      </Listbox>
    </div>

    <!-- Filter Controls -->
    <div class="space-y-2">
      <div class="flex flex-col gap-3">
        <!-- Tags Filter -->
        <Listbox v-model="selectedTags" multiple>
          <div class="flex items-center gap-2">
            <div class="relative flex-grow min-w-0">
              <ListboxButton
                class="relative w-full cursor-pointer bg-white border border-zinc-200 rounded-lg py-1.5 pl-2 pr-6 text-left focus:outline-none focus:border-brand-orange sm:text-xs hover:border-zinc-300 transition-colors h-8"
              >
                <span class="block truncate text-zinc-700">
                  <span
                    v-if="selectedTags.length > 0"
                    class="flex items-center gap-1 overflow-hidden"
                  >
                    <span
                      v-for="tag in selectedTags"
                      :key="tag"
                      class="bg-orange-100 text-orange-800 px-1.5 rounded font-medium whitespace-nowrap"
                    >
                      {{ tag }}
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

            <button
              @click="selectedTags = []"
              :disabled="selectedTags.length === 0"
              class="p-1.5 rounded-md hover:bg-zinc-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear tags"
            >
              <X
                :size="20"
                :class="
                  selectedTags.length > 0
                    ? 'text-brand-orange'
                    : 'text-zinc-300'
                "
              />
            </button>
          </div>
        </Listbox>

        <!-- Organizer Filter -->
        <Listbox v-model="selectedOrganizer">
          <div class="flex items-center gap-2">
            <div class="relative flex-grow min-w-0">
              <ListboxButton
                class="relative w-full cursor-pointer bg-white border border-zinc-200 rounded-lg py-1.5 pl-2 pr-6 text-left focus:outline-none focus:border-brand-orange sm:text-xs hover:border-zinc-300 transition-colors h-8"
              >
                <span class="block truncate text-zinc-700">
                  <span
                    v-if="selectedOrganizer"
                    class="bg-orange-100 text-orange-800 px-1.5 rounded font-medium inline-block max-w-full truncate align-bottom"
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
                  <ListboxOption v-slot="{ active }" :value="''" as="template">
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

            <button
              @click="selectedOrganizer = ''"
              :disabled="!selectedOrganizer"
              class="p-1.5 rounded-md hover:bg-zinc-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear organizer"
            >
              <X
                :size="20"
                :class="
                  selectedOrganizer ? 'text-brand-orange' : 'text-zinc-300'
                "
              />
            </button>
          </div>
        </Listbox>
      </div>

      <!-- Year Slider -->
      <div
        v-if="yearRange.max > 0"
        class="pt-1"
        :class="{
          'opacity-40 pointer-events-none': baseAuditsForFilters.length === 0,
        }"
      >
        <div class="flex items-center gap-2">
          <div
            class="relative flex-grow min-w-0 bg-white border border-zinc-200 rounded-lg p-1.5 hover:border-zinc-300 transition-colors"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-zinc-500">{{ yearRange.min }}</span>
              <span class="text-xs font-bold text-zinc-700">
                <button
                  @click="
                    yearFilterMode =
                      yearFilterMode === 'through' ? 'in' : 'through'
                  "
                  class="underline decoration-dotted underline-offset-2 cursor-pointer text-brand-orange hover:text-orange-600 transition-colors"
                  :title="
                    yearFilterMode === 'through'
                      ? 'Click to show only this year'
                      : 'Click to show all years up to this year'
                  "
                >
                  {{ yearFilterMode === 'through' ? 'Through' : 'In' }}
                </button>
                {{ selectedMaxYear }}
              </span>
              <span class="text-xs text-zinc-500">{{ yearRange.max }}</span>
            </div>
            <input
              type="range"
              :min="yearRange.min"
              :max="yearRange.max"
              :value="selectedMaxYear"
              :disabled="baseAuditsForFilters.length === 0"
              @input="
                selectedMaxYear = Number(
                  ($event.target as HTMLInputElement).value
                )
              "
              class="year-slider w-full h-2 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <button
            @click="resetYear"
            :disabled="!isYearFiltered"
            class="p-1.5 rounded-md hover:bg-zinc-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Reset year"
          >
            <X
              :size="20"
              :class="isYearFiltered ? 'text-brand-orange' : 'text-zinc-300'"
            />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom Scrollbar */
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

/* Year Slider */
.year-slider {
  background: linear-gradient(to right, #ffa100, #fed7aa);
}
.year-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffa100;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
.year-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffa100;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
</style>
