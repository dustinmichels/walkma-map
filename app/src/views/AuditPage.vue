<script setup lang="ts">
import { ArrowLeft, FileText } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Audit, Audits } from '../types'
import { generateAuditSlug, parseThemes } from '../utils'

const route = useRoute()
const router = useRouter()
const slug = computed(() => route.params.slug as string)

const audit = ref<Audit | null>(null)
const loading = ref(true)
const imageSrc = ref<string | null>(null)

const parseList = (text: string | undefined): string[] => {
  if (!text) return []
  return text
    .split('\n')
    .map((line) => line.trim())
    .map((line) => line.replace(/^[-*•]\s*|^(\d+)[\.)]\s*/, ''))
    .filter((line) => line.length > 0)
}

const getAuditIdentifier = (cityRaw: string, yearRaw: string | number, streetRaw: string): string | null => {
  const toSlug = (s: string) =>
    s.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  const raw = String(cityRaw ?? '').trim()
  const match = raw.match(/^(.*?)\s*\(([^)]+)\)\s*$/)
  const city = match ? toSlug(match[1]!) : toSlug(raw)
  if (!city) return null
  const neighborhood = match ? toSlug(match[2]!) : null
  const year = yearRaw != null ? String(parseInt(String(yearRaw))) : 'unknown'
  const street = toSlug(streetRaw).split('-').slice(0, 4).join('-')
  const parts = [city, year]
  if (neighborhood) parts.push(neighborhood)
  if (street) parts.push(street)
  return parts.join('_')
}

const openReport = () => {
  if (audit.value?.view) window.open(audit.value.view, '_blank')
}

onMounted(async () => {
  try {
    const res = await fetch('/.netlify/functions/gsheet')
    if (!res.ok) { loading.value = false; return }
    const audits: Audits = await res.json()
    audit.value = audits.find((a) => generateAuditSlug(a) === slug.value) ?? null
    loading.value = false

    if (audit.value) {
      const identifier = getAuditIdentifier(
        audit.value.city_town || audit.value.city,
        audit.value.year,
        audit.value.streets_intersections ?? '',
      )
      if (identifier) {
        const src = `/data/images/${identifier}.jpeg`
        const img = new Image()
        img.onload = () => { imageSrc.value = src }
        img.src = src
      }
    }
  } catch {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-zinc-50 font-sans text-slate-900">
    <!-- Header bar -->
    <header class="bg-brand-orange shadow-lg py-2 px-4 flex items-center gap-3 sticky top-0 z-10">
      <button
        @click="router.push('/')"
        class="text-white flex items-center gap-1.5 text-sm font-semibold hover:text-orange-100 transition-colors"
        aria-label="Back to map"
      >
        <ArrowLeft :size="18" />
        Back to Map
      </button>
      <span class="text-orange-200 text-sm">|</span>
      <h1 class="text-white text-sm font-bold tracking-tight truncate">
        Walk MA - Walk Audit Dashboard
      </h1>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <p class="text-zinc-400 text-lg">Loading audit…</p>
    </div>

    <!-- Not found -->
    <div v-else-if="!audit" class="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <p class="text-zinc-500 text-xl">Audit not found.</p>
      <button
        @click="router.push('/')"
        class="bg-zinc-900 text-white py-2 px-5 rounded-xl text-sm font-semibold hover:bg-black transition-colors"
      >
        Back to Map
      </button>
    </div>

    <!-- Audit content -->
    <div v-else class="max-w-3xl mx-auto px-4 py-10">
      <!-- Title block -->
      <div class="mb-6">
        <span class="inline-block bg-zinc-200 text-zinc-600 px-3 py-1 rounded-full text-xs font-bold mb-2">
          {{ audit.year }}
        </span>
        <h2 class="text-4xl font-extrabold text-zinc-900 leading-tight font-display">
          {{ audit.city_town || audit.city }}
        </h2>
      </div>

      <!-- Image -->
      <div v-if="imageSrc" class="mb-8 rounded-2xl overflow-hidden shadow-md">
        <img
          :src="imageSrc"
          :alt="`Walk audit photo for ${audit.city_town || audit.city}`"
          class="w-full h-auto max-h-[420px] object-cover"
        />
      </div>

      <!-- Themes -->
      <div v-if="audit.themes" class="mb-8">
        <div class="flex flex-wrap gap-2">
          <span
            v-for="theme in parseThemes(audit.themes)"
            :key="theme"
            class="bg-emerald-50 text-emerald-600 text-xs px-3 py-1.5 rounded-md font-semibold uppercase tracking-wide"
          >
            {{ theme }}
          </span>
        </div>
      </div>

      <!-- Summary -->
      <div v-if="audit.summary" class="mb-8">
        <h3 class="text-sm font-bold uppercase text-zinc-500 mb-2 tracking-wide">Summary</h3>
        <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">{{ audit.summary }}</p>
      </div>

      <!-- Area Covered -->
      <div v-if="audit.streets_intersections" class="mb-8">
        <h3 class="text-sm font-bold uppercase text-zinc-500 mb-2 tracking-wide">Area Covered</h3>
        <p class="text-base leading-relaxed text-zinc-700 whitespace-pre-wrap">{{ audit.streets_intersections }}</p>
      </div>

      <!-- Recommendations -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8 bg-zinc-100 p-6 rounded-2xl">
        <div v-if="audit.short_term_recommendations" class="flex flex-col">
          <h3 class="text-sm font-bold uppercase text-orange-600 mb-3 tracking-wide">Short Term Recommendations</h3>
          <ul class="space-y-3 m-0 p-0 list-none">
            <li
              v-for="(item, index) in parseList(audit.short_term_recommendations)"
              :key="index"
              class="flex gap-3 items-start"
            >
              <div class="mt-2 w-1.5 h-1.5 rounded-full bg-orange-400 shrink-0"></div>
              <span class="text-base leading-relaxed text-zinc-700">{{ item }}</span>
            </li>
          </ul>
        </div>
        <div v-if="audit.long_term_recommendations" class="flex flex-col">
          <h3 class="text-sm font-bold uppercase text-blue-600 mb-3 tracking-wide">Long Term Recommendations</h3>
          <ul class="space-y-3 m-0 p-0 list-none">
            <li
              v-for="(item, index) in parseList(audit.long_term_recommendations)"
              :key="index"
              class="flex gap-3 items-start"
            >
              <div class="mt-2 w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0"></div>
              <span class="text-base leading-relaxed text-zinc-700">{{ item }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Facilitator -->
      <div v-if="audit.facilitator_author" class="bg-zinc-100 p-4 rounded-xl border border-zinc-200 flex gap-2 items-baseline mb-8">
        <span class="font-semibold text-zinc-500 text-sm">Facilitator/Author:</span>
        <span class="text-zinc-700">{{ audit.facilitator_author }}</span>
      </div>

      <!-- Footer action -->
      <div class="flex justify-end">
        <button
          @click="openReport"
          :disabled="!audit.view"
          class="bg-zinc-900 text-white border-none py-3 px-6 rounded-xl text-sm font-semibold cursor-pointer flex items-center gap-2 transition-all shadow-md hover:bg-black hover:-translate-y-px hover:shadow-lg disabled:bg-zinc-400 disabled:cursor-not-allowed"
        >
          <FileText :size="20" /> View Full Report
        </button>
      </div>
    </div>
  </div>
</template>
