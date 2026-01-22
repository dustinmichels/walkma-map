<template>
  <div
    class="group bg-white rounded-xl p-6 mb-4 shadow-sm border border-zinc-200 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg cursor-pointer hover:bg-zinc-100 hover:border-zinc-300 hover:border-dashed"
    @click="emit('view', audit)"
  >
    <div class="flex justify-between items-center mb-2">
      <h3 class="text-xl font-bold text-zinc-900 font-display m-0">
        {{ audit['CITY/TOWN'] || audit.CITY }}
      </h3>
      <span class="bg-zinc-100 text-zinc-600 px-3 py-1 rounded-full text-sm font-semibold">
        {{ audit.YEAR }}
      </span>
    </div>

    <div class="flex flex-wrap gap-2 mb-4" v-if="audit.THEMES">
      <span
        v-for="theme in getThemes(audit.THEMES)"
        :key="theme"
        class="bg-emerald-50 text-emerald-600 text-xs px-2 py-1 rounded-md font-medium uppercase tracking-wide"
      >
        {{ theme }}
      </span>
    </div>

    <p class="text-zinc-600 text-sm leading-relaxed mb-6 line-clamp-3">
      {{ getSummary(audit.SUMMARY) }}
    </p>

    <div class="flex items-center border-t border-zinc-100 pt-4 min-h-[3rem]">
      <div class="text-xs text-zinc-500" v-if="audit['FACILITATOR/AUTHOR']">
        <span class="font-semibold text-zinc-700">Facilitator:</span>
        {{ audit['FACILITATOR/AUTHOR'] }}
      </div>

      <div class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <span class="bg-zinc-800 text-white text-xs px-2.5 py-1.5 rounded-md font-medium shadow-sm">
          Open
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Audit } from '../types'

defineProps<{
  audit: Audit
}>()

const emit = defineEmits<{
  (e: 'view', audit: Audit): void
}>()

const getThemes = (themesStr: string) => {
  if (!themesStr) return []
  return themesStr
    .split(',')
    .map((s) => s.trim().replace(/^"|"$/g, ''))
    .filter((s) => s)
}

const getSummary = (summary: string) => {
  if (!summary) return ''
  return summary.length > 200 ? summary.substring(0, 200) + '...' : summary
}
</script>
