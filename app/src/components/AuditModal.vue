<template>
  <TransitionRoot appear :show="isOpen" as="template">
    <Dialog as="div" @close="$emit('close')" class="relative z-[9999]">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95 translate-y-4"
            enter-to="opacity-100 scale-100 translate-y-0"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100 translate-y-0"
            leave-to="opacity-0 scale-95 translate-y-4"
          >
            <DialogPanel class="relative w-full max-w-[700px] group">
              <!-- Left Arrow (Previous) -->
              <button
                v-if="hasPrev"
                class="fixed left-4 top-1/2 -translate-y-1/2 md:absolute md:-left-16 md:translate-y-0 z-50 bg-white/90 md:bg-white text-zinc-500 hover:text-zinc-900 rounded-full p-2 shadow-lg hover:shadow-xl transition-all border border-zinc-200 focus:outline-none backdrop-blur-sm"
                @click="$emit('prev')"
                aria-label="Previous audit"
              >
                <ChevronLeft :size="32" />
              </button>

              <div
                v-if="audit"
                class="w-full transform overflow-hidden rounded-2xl bg-white text-left align-middle shadow-xl transition-all flex flex-col max-h-[90vh]"
              >
                <!-- Header -->
                <header
                  class="p-6 border-b border-zinc-100 flex justify-between items-start bg-white shrink-0"
                >
                  <div>
                    <span
                      class="inline-block bg-zinc-100 text-zinc-600 px-3 py-1 rounded-full text-xs font-bold mb-2"
                    >
                      {{ audit.YEAR }}
                    </span>
                    <DialogTitle
                      as="h3"
                      class="text-2xl font-extrabold text-zinc-900 leading-tight font-display m-0"
                    >
                      {{ audit['CITY/TOWN'] || audit.CITY }}
                    </DialogTitle>
                  </div>
                  <button
                    class="bg-transparent border-none text-xl text-zinc-400 cursor-pointer p-2 rounded-full transition-all w-10 h-10 flex items-center justify-center hover:bg-zinc-100 hover:text-zinc-800 focus:outline-none"
                    @click="$emit('close')"
                    aria-label="Close modal"
                  >
                    <X :size="24" />
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
                    <h3 class="text-sm font-bold uppercase text-zinc-500 mb-2 tracking-wide">
                      Summary
                    </h3>
                    <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">
                      {{ audit.SUMMARY }}
                    </p>
                  </div>

                  <!-- Streets / Area -->
                  <div v-if="audit['STREETS, INNTERSECTIONS + AREA COVERED']" class="mb-6">
                    <h3 class="text-sm font-bold uppercase text-zinc-500 mb-2 tracking-wide">
                      Area Covered
                    </h3>
                    <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">
                      {{ audit['STREETS, INNTERSECTIONS + AREA COVERED'] }}
                    </p>
                  </div>

                  <!-- Recommendations Grid -->
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6 bg-zinc-50 p-4 rounded-xl">
                    <!-- Short Term -->
                    <div v-if="audit['SHORT TERM RECOMMENDATIONS']" class="flex flex-col">
                      <h3 class="text-sm font-bold uppercase text-orange-600 mb-3 tracking-wide">
                        Short Term Recommendations
                      </h3>
                      <ul class="space-y-3 m-0 p-0 list-none">
                        <li
                          v-for="(item, index) in parseList(audit['SHORT TERM RECOMMENDATIONS'])"
                          :key="index"
                          class="flex gap-3 items-start group"
                        >
                          <div
                            class="mt-2 w-1.5 h-1.5 rounded-full bg-orange-400 group-hover:bg-orange-600 group-hover:scale-125 transition-all shrink-0"
                          ></div>
                          <span class="text-base leading-relaxed text-zinc-700">{{ item }}</span>
                        </li>
                      </ul>
                    </div>

                    <!-- Long Term -->
                    <div v-if="audit['LONG TERM RECOMMENDATIONS']" class="flex flex-col">
                      <h3 class="text-sm font-bold uppercase text-blue-600 mb-3 tracking-wide">
                        Long Term Recommendations
                      </h3>
                      <ul class="space-y-3 m-0 p-0 list-none">
                        <li
                          v-for="(item, index) in parseList(audit['LONG TERM RECOMMENDATIONS'])"
                          :key="index"
                          class="flex gap-3 items-start group"
                        >
                          <div
                            class="mt-2 w-1.5 h-1.5 rounded-full bg-blue-400 group-hover:bg-blue-600 group-hover:scale-125 transition-all shrink-0"
                          ></div>
                          <span class="text-base leading-relaxed text-zinc-700">{{ item }}</span>
                        </li>
                      </ul>
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
                <footer class="p-5 border-t border-zinc-100 bg-white flex justify-end shrink-0">
                  <button
                    class="bg-zinc-900 text-white border-none py-3 px-6 rounded-xl text-sm font-semibold cursor-pointer flex items-center gap-2 transition-all shadow-md hover:bg-black hover:-translate-y-px hover:shadow-lg disabled:bg-zinc-400 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
                    @click="openReport"
                    :disabled="!hasPdf"
                  >
                    <FileText :size="20" /> View Full Report
                  </button>
                </footer>
              </div>

              <!-- Right Arrow (Next) -->
              <button
                v-if="hasNext"
                class="fixed right-4 top-1/2 -translate-y-1/2 md:absolute md:-right-16 md:translate-y-0 z-50 bg-white/90 md:bg-white text-zinc-500 hover:text-zinc-900 rounded-full p-2 shadow-lg hover:shadow-xl transition-all border border-zinc-200 focus:outline-none backdrop-blur-sm"
                @click="$emit('next')"
                aria-label="Next audit"
              >
                <ChevronRight :size="32" />
              </button>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { TransitionRoot, TransitionChild, Dialog, DialogPanel, DialogTitle } from '@headlessui/vue'
import { X, FileText, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { Audit } from '../types'

const props = defineProps<{
  audit: Audit | null
  isOpen: boolean
  hasPrev: boolean
  hasNext: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'prev'): void
  (e: 'next'): void
}>()

const handleKeydown = (e: KeyboardEvent) => {
  if (!props.isOpen) return

  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    if (props.hasPrev) emit('prev')
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    if (props.hasNext) emit('next')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const getThemes = (themesStr: string) => {
  if (!themesStr) return []
  return themesStr
    .split(',')
    .map((s) => s.trim().replace(/^"|"$/g, ''))
    .filter((s) => s)
}

const hasPdf = computed(() => {
  return !!props.audit?.VIEW_link
})

const parseList = (text: string | undefined): string[] => {
  if (!text) return []
  return (
    text
      .split('\n')
      .map((line) => line.trim())
      // Remove leading dashes, asterisks, or numbers followed by dot/paren
      .map((line) => line.replace(/^[-*•]\s*|^(\d+)[\.)]\s*/, ''))
      .filter((line) => line.length > 0)
  )
}

const openReport = () => {
  if (props.audit?.VIEW_link) {
    window.open(props.audit.VIEW_link, '_blank')
  }
}
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
