<script setup lang="ts">
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { Audits } from '../types'
import { parseThemes } from '../utils'

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Title
)

// Set default font
Chart.defaults.font.family = '"Inter", sans-serif'
Chart.defaults.color = '#71717a'

const props = defineProps<{
  audits: Audits | null
  allAudits?: Audits | null
  selectedTags?: string[]
}>()

const emit = defineEmits<{
  (e: 'select', value: string): void
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const chartHeight = ref(0)
const scrollContainer = ref<HTMLDivElement | null>(null)

const totalAudits = computed(() => props.audits?.length || 0)

const totalCities = computed(() => {
  if (!props.audits) return 0
  const cities = new Set(props.audits.map((a) => a.city))
  return cities.size
})

const getThemeCounts = (audits: Audits | null) => {
  const counts = new Map<string, number>()
  if (audits) {
    audits.forEach((audit) => {
      const themes = parseThemes(audit.themes)
      themes.forEach((theme) => {
        counts.set(theme, (counts.get(theme) || 0) + 1)
      })
    })
  }
  return counts
}

const processData = (
  currentAudits: Audits | null,
  allAudits: Audits | null | undefined
) => {
  // Use allAudits to determine the list of themes (so it stays stable)
  // Fallback to currentAudits if allAudits isn't provided yet
  const universeAudits = allAudits || currentAudits
  const globalCounts = getThemeCounts(universeAudits)

  // Identify all global themes to establish the "Full List"
  const topGlobalThemes = Array.from(globalCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .map((item) => item[0])

  // Get counts for the current filtered set
  const currentCounts = getThemeCounts(currentAudits)

  // Create combined objects for sorting locally
  const combined = topGlobalThemes.map((theme) => ({
    label: theme,
    count: currentCounts.get(theme) || 0,
  }))

  // Sort by current count descending (Most Popular at Top)
  combined.sort((a, b) => b.count - a.count)

  return {
    labels: combined.map((c) => c.label),
    data: combined.map((c) => c.count),
  }
}

const updateChart = async () => {
  if (!chartInstance) return

  const { labels, data } = processData(props.audits, props.allAudits)

  // Calculate dynamic height: 35px per bar
  // Minimum equal to container height, but usually content drives height here
  const minHeight = scrollContainer.value?.clientHeight || 200
  chartHeight.value = Math.max(labels.length * 35, minHeight)

  // Wait for DOM update
  await nextTick()

  if (chartInstance.data.datasets[0]) {
    chartInstance.data.labels = labels
    chartInstance.data.datasets[0].data = [...data]

    const activeTags = props.selectedTags || []
    chartInstance.data.datasets[0].backgroundColor = labels.map((label) =>
      activeTags.includes(label as string) ? '#dc2626' : '#ffa100'
    )
    chartInstance.data.datasets[0].hoverBackgroundColor = labels.map((label) =>
      activeTags.includes(label as string) ? '#b91c1c' : '#cc8100'
    )
    chartInstance.data.datasets[0].borderColor = 'transparent'
    chartInstance.data.datasets[0].borderWidth = 0

    if (chartInstance.data.datasets[1]) {
      chartInstance.data.datasets[1].data = [...data]
    }
    // chartInstance.resize() - Removing to prevent interrupting animation
    chartInstance.update()
  }
}

onMounted(() => {
  if (chartCanvas.value) {
    const ctx = chartCanvas.value.getContext('2d')
    if (ctx) {
      chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: [],
          datasets: [
            {
              label: 'Audits',
              data: [],
              backgroundColor: '#ffa100',
              hoverBackgroundColor: '#cc8100',
              borderRadius: 4,
              barPercentage: 0.6,
              categoryPercentage: 0.9,
              xAxisID: 'x',
              borderSkipped: false,
            },
            {
              label: 'Audits Top',
              data: [],
              xAxisID: 'x2',
              backgroundColor: 'transparent',
              borderColor: 'transparent',
              barThickness: 0,
              grouped: false,
              hoverBackgroundColor: 'transparent',
              hoverBorderColor: 'transparent',
            },
          ],
        },
        options: {
          onClick: (evt, elements, chart) => {
            if (elements.length > 0 && chart.data.labels) {
              const element = elements[0]
              if (element) {
                const i = element.index
                const label = chart.data.labels[i]
                if (typeof label === 'string') {
                  emit('select', label)
                }
              }
            }
          },
          onHover: (evt, elements) => {
            if (chartCanvas.value) {
              chartCanvas.value.style.cursor =
                elements.length > 0 ? 'pointer' : 'default'
            }
          },
          indexAxis: 'y', // Horizontal bars
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: false,
            },
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              titleColor: '#18181b',
              bodyColor: '#18181b',
              borderColor: '#e4e4e7',
              borderWidth: 1,
              padding: 10,
              displayColors: false,
              filter: (tooltipItem) => tooltipItem.datasetIndex === 0,
              callbacks: {
                label: (context) => `${context.parsed.x} audits`,
              },
            },
          },
          scales: {
            x: {
              beginAtZero: true,
              grid: {
                display: true,
                color: '#f4f4f5',
              },
              ticks: {
                font: {
                  size: 10,
                },
                color: '#3f3f46',
                maxTicksLimit: 6,
                maxRotation: 0,
                minRotation: 0,
              },
              border: {
                display: false,
              },
            },
            x2: {
              position: 'top',
              beginAtZero: true,
              grid: {
                display: true,
                color: '#f4f4f5',
                drawOnChartArea: false, // Prevent double grid lines
              },
              ticks: {
                font: {
                  size: 10,
                },
                color: '#3f3f46',
                maxTicksLimit: 6,
                maxRotation: 0,
                minRotation: 0,
              },
              border: {
                display: false,
              },
            },
            y: {
              grid: {
                display: false,
              },
              ticks: {
                font: {
                  size: 11,
                },
                color: '#3f3f46',
                autoSkip: false,
              },
              border: {
                display: false,
              },
            },
          },
          layout: {
            padding: { left: 0, right: 10, top: 0, bottom: 0 },
          },
        },
      })
      updateChart()

      // Update chart size on window resize
      window.addEventListener('resize', updateChart)
    }
  }
})

watch(
  () => [props.audits, props.allAudits, props.selectedTags],
  () => {
    updateChart()
  },
  { deep: true }
)

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
    window.removeEventListener('resize', updateChart)
  }
})
</script>

<template>
  <div class="w-full h-full flex gap-4">
    <!-- Combined Stats Panel -->
    <div
      class="flex-shrink-0 bg-white rounded-xl border-2 border-zinc-200 shadow-sm flex items-center justify-center p-4 gap-6 w-44"
    >
      <!-- Audits -->
      <div class="flex flex-col justify-center items-center">
        <span
          class="text-4xl font-black text-brand-orange leading-none mb-1 w-16 text-center"
        >
          {{ totalAudits }}
        </span>
        <span
          class="text-xs font-bold text-zinc-500 uppercase tracking-wide text-center leading-tight"
        >
          Total<br />Audits
        </span>
      </div>

      <!-- Divider -->
      <div class="h-8 w-0.5 bg-zinc-100 rounded-full"></div>

      <!-- Cities -->
      <div class="flex flex-col justify-center items-center">
        <span
          class="text-4xl font-black text-brand-orange leading-none mb-1 w-16 text-center"
        >
          {{ totalCities }}
        </span>
        <span
          class="text-xs font-bold text-zinc-500 uppercase tracking-wide text-center leading-tight"
        >
          Total<br />Cities
        </span>
      </div>
    </div>

    <!-- Chart Panel -->
    <div
      class="flex-grow min-w-0 bg-white rounded-xl border-2 border-zinc-200 shadow-sm flex flex-col overflow-hidden"
    >
      <!-- Scrollable Vertical Container -->
      <div
        class="flex-grow overflow-y-auto custom-scrollbar-subtle relative p-2"
        ref="scrollContainer"
      >
        <div class="w-full relative" :style="{ height: `${chartHeight}px` }">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>
