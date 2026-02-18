<template>
  <div
    class="group relative overflow-hidden bg-white rounded-xl p-4 mb-2 shadow-sm border-2 border-dotted border-zinc-300 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg cursor-pointer hover:bg-zinc-100 hover:border-zinc-400"
    @click="emit('view', audit)"
  >
    <div
      class="absolute top-0 right-0 bg-zinc-200/80 px-3 py-1 rounded-bl-lg text-xs font-bold text-zinc-600 border-b border-l border-zinc-300/50 backdrop-blur-sm"
    >
      {{ audit.year }}
    </div>

    <div class="flex flex-col mb-1 pr-12">
      <h3
        class="text-base font-bold text-zinc-900 font-display m-0 leading-tight"
      >
        {{ audit.city_town || audit.city }}
      </h3>
    </div>

    <div class="flex flex-wrap gap-1.5 mb-2" v-if="audit.themes">
      <span
        v-for="theme in parseThemes(audit.themes)"
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
import { parseThemes } from '../utils'

defineProps<{
  audit: Audit
}>()

const emit = defineEmits<{
  (e: 'view', audit: Audit): void
}>()

const formatText = (text: string) => {
  if (!text) return ''
  return text.length > 200 ? text.substring(0, 200) + '...' : text
}
</script>
