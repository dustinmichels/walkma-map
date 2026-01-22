<template>
  <div
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex justify-center items-center p-4 animate-in fade-in duration-200"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white w-full max-w-[700px] max-h-[90vh] rounded-2xl flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 duration-300"
    >
      <!-- Header -->
      <header class="p-6 border-b border-zinc-100 flex justify-between items-start bg-white">
        <div>
          <span
            class="inline-block bg-zinc-100 text-zinc-600 px-3 py-1 rounded-full text-xs font-bold mb-2"
          >
            {{ audit.YEAR }}
          </span>
          <h2 class="text-2xl font-extrabold text-zinc-900 leading-tight font-display m-0">
            {{ audit['CITY/TOWN'] || audit.CITY }}
          </h2>
        </div>
        <button
          class="bg-transparent border-none text-xl text-zinc-400 cursor-pointer p-2 rounded-full transition-all w-10 h-10 flex items-center justify-center hover:bg-zinc-100 hover:text-zinc-800"
          @click="$emit('close')"
          aria-label="Close modal"
        >
          <i class="fas fa-times"></i>
        </button>
      </header>

      <!-- Scrollable Content -->
      <div class="p-6 overflow-y-auto flex-1 custom-scrollbar">
        <!-- Themes -->
        <div v-if="audit.THEMES" class="mb-6">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="theme in getThemes(audit.THEMES)"
              :key="theme"
              class="bg-emerald-50 text-emerald-600 text-xs px-3 py-1.5 rounded-md font-semibold uppercase tracking-wide"
            >
              {{ theme }}
            </span>
          </div>
        </div>

        <!-- Summary -->
        <div v-if="audit.SUMMARY" class="mb-6">
          <h3 class="text-sm font-bold uppercase text-zinc-500 mb-2 tracking-wide">Summary</h3>
          <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">
            {{ audit.SUMMARY }}
          </p>
        </div>

        <!-- Streets / Area -->
        <div v-if="audit['STREETS, INNTERSECTIONS + AREA COVERED']" class="mb-6">
          <h3 class="text-sm font-bold uppercase text-zinc-500 mb-2 tracking-wide">Area Covered</h3>
          <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">
            {{ audit['STREETS, INNTERSECTIONS + AREA COVERED'] }}
          </p>
        </div>

        <!-- Recommendations Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6 bg-zinc-50 p-4 rounded-xl">
          <!-- Short Term -->
          <div v-if="audit['SHORT TERM RECOMMENDATIONS']" class="flex flex-col">
            <h3 class="text-sm font-bold uppercase text-orange-600 mb-2 tracking-wide">
              Short Term Recommendations
            </h3>
            <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">
              {{ audit['SHORT TERM RECOMMENDATIONS'] }}
            </p>
          </div>

          <!-- Long Term -->
          <div v-if="audit['LONG TERM RECOMMENDATIONS']" class="flex flex-col">
            <h3 class="text-sm font-bold uppercase text-blue-600 mb-2 tracking-wide">
              Long Term Recommendations
            </h3>
            <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">
              {{ audit['LONG TERM RECOMMENDATIONS'] }}
            </p>
          </div>
        </div>

        <!-- Facilitator -->
        <div
          v-if="audit['FACILITATOR/AUTHOR']"
          class="bg-zinc-50 p-4 rounded-lg border border-zinc-200 flex gap-2 items-baseline mb-6"
        >
          <span class="font-semibold text-zinc-500 text-sm">Facilitator/Author:</span>
          <span class="text-zinc-700">{{ audit['FACILITATOR/AUTHOR'] }}</span>
        </div>
      </div>

      <!-- Footer -->
      <footer class="p-5 border-t border-zinc-100 bg-white flex justify-end">
        <button
          class="bg-zinc-900 text-white border-none py-3 px-6 rounded-xl text-sm font-semibold cursor-pointer flex items-center gap-2 transition-all shadow-md hover:bg-black hover:-translate-y-px hover:shadow-lg disabled:bg-zinc-400 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          @click="openReport"
          :disabled="!hasPdf"
        >
          <span class="text-lg">📄</span> View Full Report
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import type { Audit } from '../types'

const props = defineProps<{
  audit: Audit
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const getThemes = (themesStr: string) => {
  if (!themesStr) return []
  return themesStr
    .split(',')
    .map((s) => s.trim().replace(/^"|"$/g, ''))
    .filter((s) => s)
}

const hasPdf = computed(() => {
  return !!props.audit.VIEW_link
})

const openReport = () => {
  if (props.audit.VIEW_link) {
    window.open(props.audit.VIEW_link, '_blank')
  }
}

// Close on Escape key
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 20px;
  border: 3px solid transparent;
  background-clip: content-box;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #9ca3af;
}
</style>
