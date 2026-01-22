<template>
  <div
    class="bg-white rounded-xl p-6 mb-4 shadow-sm border border-zinc-200 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
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

    <div class="flex justify-between items-center border-t border-zinc-100 pt-4">
      <div class="text-xs text-zinc-500" v-if="audit['FACILITATOR/AUTHOR']">
        <span class="font-semibold text-zinc-700">Facilitator:</span>
        {{ audit['FACILITATOR/AUTHOR'] }}
      </div>

      <button
        @click="openModal"
        class="bg-white text-blue-600 border border-blue-600 px-3 py-1.5 rounded-lg text-sm font-semibold cursor-pointer flex items-center gap-2 transition-all hover:bg-blue-50 ml-auto"
      >
        <i class="fas fa-eye text-base"></i> View
      </button>
    </div>

    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <AuditModal v-if="isModalOpen" :audit="audit" @close="closeModal" />
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AuditModal from './AuditModal.vue'
import type { Audit } from '../types'

const props = defineProps<{
  audit: Audit
}>()

const isModalOpen = ref(false)

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

const openModal = () => {
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}
</script>
