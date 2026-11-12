<script setup lang="ts">
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@headlessui/vue'
import { Search } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Audit, Audits } from '../types'
import { fuzzyScore, generateAuditSlug, normalizeSearchText } from '../utils'

const props = defineProps<{ audits: Audits | null }>()

const router = useRouter()
const query = ref('')

const index = computed(() =>
  (props.audits ?? []).map((audit, i) => ({
    audit,
    // Row position, not slug: duplicate slugs exist in the sheet
    key: i,
    text: normalizeSearchText(
      [audit.city, audit.neighborhood, audit.streets_intersections].join(' ')
    ),
  }))
)

const results = computed(() => {
  if (!query.value.trim()) return []
  return index.value
    .map((entry) => ({ ...entry, score: fuzzyScore(query.value, entry.text) }))
    .filter((r): r is typeof r & { score: number } => r.score !== null)
    .sort((a, b) => b.score - a.score)
})

const openAudit = (audit: Audit | null) => {
  if (audit) router.push(`/audit/${generateAuditSlug(audit)}`)
}
</script>

<template>
  <Combobox :model-value="null" nullable @update:model-value="openAudit">
    <div class="relative w-full">
      <Search
        :size="16"
        class="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none"
      />
      <ComboboxInput
        class="w-full bg-white rounded-lg py-1.5 pl-8 pr-3 text-sm text-zinc-800 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-black/30"
        placeholder="Search audits by city, neighborhood, or street…"
        autocomplete="off"
        @change="query = $event.target.value"
      />
      <ComboboxOptions
        v-if="query.trim()"
        class="absolute mt-1 max-h-96 w-full overflow-auto rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 focus:outline-none z-30 custom-scrollbar"
      >
        <ComboboxOption
          v-for="r in results"
          :key="r.key"
          v-slot="{ active }"
          :value="r.audit"
          as="template"
        >
          <li
            :class="[
              active ? 'bg-orange-50 text-orange-900' : 'text-zinc-900',
              'cursor-pointer select-none px-3 py-2',
            ]"
          >
            <div class="text-sm font-medium truncate">
              {{ r.audit.city }}
              <span v-if="r.audit.neighborhood" class="font-normal">
                · {{ r.audit.neighborhood }}
              </span>
              <span class="font-normal text-zinc-400">
                · {{ r.audit.year }}
              </span>
            </div>
            <div class="text-xs text-zinc-500 truncate">
              {{ r.audit.streets_intersections }}
            </div>
          </li>
        </ComboboxOption>
        <li
          v-if="results.length === 0"
          class="px-3 py-2 text-sm italic text-zinc-500 select-none"
        >
          No audits found
        </li>
      </ComboboxOptions>
    </div>
  </Combobox>
</template>
