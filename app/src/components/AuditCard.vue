<template>
  <div class="audit-card">
    <div class="audit-header">
      <h3 class="audit-city">{{ audit.properties['CITY/TOWN'] || audit.properties.CITY }}</h3>
      <span class="audit-year">{{ audit.properties.YEAR }}</span>
    </div>

    <div class="audit-tags" v-if="audit.properties.THEMES">
      <span v-for="theme in getThemes(audit.properties.THEMES)" :key="theme" class="audit-tag">
        {{ theme }}
      </span>
    </div>

    <p class="audit-summary">{{ getSummary(audit.properties.SUMMARY) }}</p>

    <div class="audit-footer">
      <div class="audit-author" v-if="audit.properties['FACILITATOR/AUTHOR']">
        <span class="label">Facilitator:</span> {{ audit.properties['FACILITATOR/AUTHOR'] }}
      </div>

      <button class="view-btn" @click="handleView" :disabled="!hasPdf">
        <span class="icon">📄</span> View Report
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  audit: any
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

const hasPdf = computed(() => {
  return !!props.audit.properties.VIEW_link
})

const handleView = () => {
  if (props.audit.properties.VIEW_link) {
    window.open(props.audit.properties.VIEW_link, '_blank')
  }
}
</script>

<style scoped>
.audit-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  border: 1px solid #e5e7eb;
}

.audit-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.audit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.audit-city {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
  font-family: 'Outfit', sans-serif;
}

.audit-year {
  background: #f3f4f6;
  color: #4b5563;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.audit-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.audit-tag {
  background: #ecfdf5;
  color: #059669;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.audit-summary {
  color: #4b5563;
  font-size: 0.95rem;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.audit-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f3f4f6;
  padding-top: 1rem;
}

.audit-author {
  font-size: 0.85rem;
  color: #6b7280;
}

.audit-author .label {
  font-weight: 600;
  color: #374151;
}

.view-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.2s;
}

.view-btn:hover {
  background: #1d4ed8;
}

.view-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.icon {
  font-size: 1rem;
}
</style>
