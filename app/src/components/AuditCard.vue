<template>
  <div
    class="group bg-white rounded-xl p-4 mb-2 shadow-sm border border-zinc-200 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg cursor-pointer hover:bg-zinc-100 hover:border-zinc-300 hover:border-dashed"
    @click="emit('view', audit)"
  >
    <div class="flex justify-between items-center mb-1">
      <h3 class="text-base font-bold text-zinc-900 font-display m-0">
        {{ audit.city_town || audit.city }}
      </h3>
      <span
        class="bg-zinc-100 text-zinc-600 px-2 py-0.5 rounded-full text-xs font-semibold"
      >
        {{ audit.year }}
      </span>
    </div>

    <div class="flex flex-wrap gap-1.5 mb-2" v-if="audit.themes">
      <span
        v-for="theme in getThemes(audit.themes)"
        :key="theme"
        class="bg-emerald-50 text-emerald-600 text-[10px] px-2 py-0.5 rounded-full font-medium uppercase border border-emerald-100/50"
      >
        {{ theme }}
      </span>
    </div>

    <p class="text-zinc-600 text-xs leading-snug mb-3 line-clamp-3">
      <span class="font-semibold text-zinc-900">Area covered:</span>
      {{ formatText(audit.streets_intersections) }}
    </p>

    <div class="flex items-center border-t border-zinc-100 pt-2 min-h-[2rem]">
      <div class="text-xs text-zinc-500" v-if="audit.facilitator_author">
        <span class="font-semibold text-zinc-700">Facilitator:</span>
        {{ audit.facilitator_author }}
      </div>

      <div
        class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200"
      >
        <span
          class="bg-zinc-100 text-zinc-600 p-1.5 rounded-md inline-flex items-center justify-center"
        >
          <Eye class="w-4 h-4" />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Eye } from 'lucide-vue-next'
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

const formatText = (text: string) => {
  if (!text) return ''
  return text.length > 200 ? text.substring(0, 200) + '...' : text
}
</script>
