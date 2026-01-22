<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <!-- Header -->
      <header class="modal-header">
        <div>
          <span class="modal-year">{{ audit.YEAR }}</span>
          <h2 class="modal-title">{{ audit['CITY/TOWN'] || audit.CITY }}</h2>
        </div>
        <button class="close-btn" @click="$emit('close')" aria-label="Close modal">
          <i class="fas fa-times"></i>
        </button>
      </header>

      <!-- Scrollable Content -->
      <div class="modal-body custom-scrollbar">
        <!-- Themes -->
        <div v-if="audit.THEMES" class="section">
          <div class="tags">
            <span v-for="theme in getThemes(audit.THEMES)" :key="theme" class="tag">
              {{ theme }}
            </span>
          </div>
        </div>

        <!-- Summary -->
        <div v-if="audit.SUMMARY" class="section">
          <h3 class="section-title">Summary</h3>
          <p class="text-content">{{ audit.SUMMARY }}</p>
        </div>

        <!-- Streets / Area -->
        <div v-if="audit['STREETS, INNTERSECTIONS + AREA COVERED']" class="section">
          <h3 class="section-title">Area Covered</h3>
          <p class="text-content">
            {{ audit['STREETS, INNTERSECTIONS + AREA COVERED'] }}
          </p>
        </div>

        <!-- Recommendations Grid -->
        <div class="recommendations-grid">
          <!-- Short Term -->
          <div v-if="audit['SHORT TERM RECOMMENDATIONS']" class="recommendation-col">
            <h3 class="section-title text-orange">Short Term Recommendations</h3>
            <p class="text-content">{{ audit['SHORT TERM RECOMMENDATIONS'] }}</p>
          </div>

          <!-- Long Term -->
          <div v-if="audit['LONG TERM RECOMMENDATIONS']" class="recommendation-col">
            <h3 class="section-title text-blue">Long Term Recommendations</h3>
            <p class="text-content">{{ audit['LONG TERM RECOMMENDATIONS'] }}</p>
          </div>
        </div>

        <!-- Facilitator -->
        <div v-if="audit['FACILITATOR/AUTHOR']" class="section meta-section">
          <span class="label">Facilitator/Author:</span>
          <span class="value">{{ audit['FACILITATOR/AUTHOR'] }}</span>
        </div>
      </div>

      <!-- Footer -->
      <footer class="modal-footer">
        <button class="view-report-btn" @click="openReport" :disabled="!hasPdf">
          <span class="icon">📄</span> View Full Report
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  audit: any // Using specific type is better but 'any' allows flexibility with the GeoJSON feature structure
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
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  animation: fadeIn 0.2s ease-out;
}

.modal-container {
  background: white;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: #fff;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #111827;
  margin: 0;
  line-height: 1.2;
  font-family: 'Outfit', sans-serif;
}

.modal-year {
  display: inline-block;
  background: #f3f4f6;
  color: #4b5563;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.25rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.section {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #6b7280;
  margin-bottom: 0.5rem;
  letter-spacing: 0.05em;
}

.text-content {
  font-size: 1rem;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  background: #ecfdf5;
  color: #059669;
  font-size: 0.75rem;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.recommendations-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  background: #f9fafb;
  padding: 1rem;
  border-radius: 12px;
}

@media (min-width: 640px) {
  .recommendations-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.recommendation-col {
  display: flex;
  flex-direction: column;
}

.text-orange {
  color: #ea580c;
}

.text-blue {
  color: #2563eb;
}

.meta-section {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
}

.meta-section .label {
  font-weight: 600;
  color: #64748b;
  font-size: 0.875rem;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  background: #fff;
  display: flex;
  justify-content: flex-end;
}

.view-report-btn {
  background: #111827;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.view-report-btn:hover {
  background: #000;
  transform: translateY(-1px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.view-report-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

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
