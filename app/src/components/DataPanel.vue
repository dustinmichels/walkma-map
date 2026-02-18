<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Audit, Audits } from '../types'
import AuditCard from './AuditCard.vue'
import AuditModal from './AuditModal.vue'

const props = defineProps<{
  audits: Audits | null
}>()

// Modal State
const selectedAudit = ref<Audit | null>(null)
const isAuditModalOpen = ref(false)

const handleViewAudit = (audit: Audit) => {
  selectedAudit.value = audit
  isAuditModalOpen.value = true
}

// Navigation Logic
const selectedAuditIndex = computed(() => {
  if (!selectedAudit.value || !props.audits) return -1
  return props.audits.indexOf(selectedAudit.value)
})

const hasPrevAudit = computed(() => selectedAuditIndex.value > 0)
// Check if current index is valid and not the last one
const hasNextAudit = computed(() => {
  return (
    !!props.audits &&
    selectedAuditIndex.value !== -1 &&
    selectedAuditIndex.value < props.audits.length - 1
  )
})

const handlePrevAudit = () => {
  if (hasPrevAudit.value && props.audits) {
    const prev = props.audits[selectedAuditIndex.value - 1]
    if (prev) selectedAudit.value = prev
  }
}

const handleNextAudit = () => {
  if (hasNextAudit.value && props.audits) {
    const next = props.audits[selectedAuditIndex.value + 1]
    if (next) selectedAudit.value = next
  }
}

// Infinite loading
const visibleLimit = ref(20)
const loadingMore = ref(false)

const displayedAudits = computed(() => {
  if (!props.audits) return []
  return props.audits.slice(0, visibleLimit.value)
})

const scrollContainer = ref<HTMLElement | null>(null)

watch(
  () => props.audits,
  () => {
    // Reset limit when filters change (detected by audits prop change)
    visibleLimit.value = 20
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = 0
    }
  }
)

const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement
  scrollContainer.value = target // update ref

  if (loadingMore.value || !props.audits) return

  // Check if scrolled near bottom (within 100px)
  if (target.scrollHeight - target.scrollTop - target.clientHeight < 100) {
    if (visibleLimit.value < props.audits.length) {
      loadingMore.value = true
      // Small delay to show spinner/prevent hammering
      setTimeout(() => {
        visibleLimit.value += 20
        loadingMore.value = false
      }, 300)
    }
  }
}
</script>

<template>
  <aside
    class="w-full flex flex-col bg-white rounded-xl shadow-xl border border-zinc-200 overflow-hidden flex-1 min-h-0 relative"
  >
    <!-- Interactive Elements -->
    <div
      class="flex-grow overflow-y-auto p-3 custom-scrollbar space-y-3"
      @scroll="handleScroll"
    >
      <div
        class="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
      >
        <div
          v-if="!audits || audits.length === 0"
          class="h-64 flex flex-col items-center justify-center text-center border-2 border-dashed border-zinc-100 rounded-xl bg-orange-50/30"
        >
          <p class="text-lg font-medium text-zinc-700 mb-2">
            Hey! You could do a walk audit here!
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
          <!-- Render list of audits -->
          <div class="mt-2">
            <h4 class="text-xs font-bold text-zinc-700 uppercase mb-1.5">
              Audits
            </h4>
            <div class="space-y-4">
              <AuditCard
                v-for="(audit, index) in displayedAudits"
                :key="index"
                :audit="audit"
                @view="handleViewAudit"
              />
              <div v-if="loadingMore" class="py-4 text-center">
                <span class="text-sm text-zinc-400">Loading more...</span>
              </div>
            </div>
          </div>
        </template>
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
