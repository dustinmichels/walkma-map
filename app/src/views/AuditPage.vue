<script setup lang="ts">
import { ArrowLeft, Check, FileText, Share2 } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Audit, Audits } from '../types'
import { generateAuditSlug, parseThemes } from '../utils'

const route = useRoute()
const router = useRouter()
const slug = computed(() => route.params.slug as string)

const audit = ref<Audit | null>(null)
const allAudits = ref<Audits>([])
const loading = ref(true)
const imageSrc = ref<string | null>(null)

const relatedAudits = computed(() => {
  if (!audit.value || !allAudits.value.length) return []
  const currentThemes = new Set(parseThemes(audit.value.themes))
  return allAudits.value
    .filter((a) => generateAuditSlug(a) !== slug.value)
    .map((a) => ({
      audit: a,
      score: parseThemes(a.themes).filter((t) => currentThemes.has(t)).length,
    }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((x) => x.audit)
})

const parseList = (text: string | undefined): string[] => {
  if (!text) return []
  // Strip zero-width spaces, then normalize inline list separators like "sentence.- Next"
  const normalized = text
    .replace(/[\u200b\u200c\u200d\ufeff]/g, '')
    .replace(/\.\s*-\s+/g, '.\n- ')
    .replace(/([^\s\n])-\s+([A-Z])/g, '$1\n$2')
  return normalized
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

const copied = ref(false)
const copyLink = async () => {
  await navigator.clipboard.writeText(window.location.href)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

const loadAudit = async () => {
  loading.value = true
  imageSrc.value = null
  try {
    if (!allAudits.value.length) {
      const res = await fetch('/.netlify/functions/gsheet')
      if (!res.ok) { loading.value = false; return }
      allAudits.value = await res.json()
    }
    audit.value = allAudits.value.find((a) => generateAuditSlug(a) === slug.value) ?? null
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
}

onMounted(loadAudit)
watch(slug, loadAudit)
</script>

<template>
  <div class="min-h-screen bg-zinc-50 font-sans text-slate-900">
    <!-- Header bar -->
    <header class="bg-brand-orange shadow-lg flex items-center sticky top-0 z-10">
      <button
        @click="router.push('/')"
        class="bg-black/20 text-white flex items-center gap-1.5 text-sm font-semibold hover:bg-black/30 transition-colors py-3 px-4 self-stretch"
        aria-label="Back to map"
      >
        <ArrowLeft :size="18" />
        Back to Map
      </button>
      <h1 class="text-white text-sm font-bold tracking-tight truncate px-4">
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
    <div v-else class="max-w-5xl mx-auto px-4 py-10">
      <!-- Title block -->
      <div class="mb-6">
        <div class="flex items-baseline gap-3 mb-2">
          <h2 class="text-4xl font-extrabold text-zinc-900 leading-tight font-display">
            {{ audit.city_town || audit.city }}
          </h2>
          <span class="inline-block bg-zinc-200 text-zinc-600 px-2 py-0.5 rounded-full text-xs font-bold shrink-0">{{ audit.year }}</span>
        </div>
        <p v-if="audit.facilitator_author" class="text-sm text-zinc-500">
          <span class="font-semibold">Facilitator/Author:</span> {{ audit.facilitator_author }}
        </p>
        <div class="mt-4 flex items-center gap-2">
          <button
            @click="openReport"
            :disabled="!audit.view"
            class="bg-zinc-900 text-white border-none py-2 px-5 rounded-xl text-sm font-semibold cursor-pointer inline-flex items-center gap-2 transition-all shadow-md hover:bg-black hover:-translate-y-px hover:shadow-lg disabled:bg-zinc-400 disabled:cursor-not-allowed"
          >
            <FileText :size="16" /> View Full Report
          </button>
          <button
            @click="copyLink"
            class="py-2 px-4 rounded-xl text-sm font-semibold inline-flex items-center gap-2 transition-all border shadow-sm"
            :class="copied ? 'bg-emerald-50 text-emerald-600 border-emerald-200' : 'bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50 hover:-translate-y-px hover:shadow-md'"
          >
            <Check v-if="copied" :size="15" />
            <Share2 v-else :size="15" />
            {{ copied ? 'Copied to clipboard' : 'Share' }}
          </button>
        </div>
      </div>

      <!-- Two-column grid: main content + sidebar -->
      <div class="lg:grid lg:grid-cols-[1fr_280px] gap-8 items-start">

        <!-- Main column -->
        <div>
          <!-- Themes -->
          <div v-if="audit.themes" class="mb-8">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="theme in parseThemes(audit.themes)"
                :key="theme"
                class="bg-emerald-50 text-emerald-600 text-xs px-3 py-1.5 rounded-md font-semibold uppercase tracking-wide border border-zinc-200"
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

          <!-- Image (smaller, below summary) -->
          <div v-if="imageSrc" class="mb-8 rounded-xl overflow-hidden shadow-md max-w-sm">
            <img
              :src="imageSrc"
              :alt="`Walk audit photo for ${audit.city_town || audit.city}`"
              class="w-full h-auto max-h-52 object-cover"
            />
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

        </div>

        <!-- Sidebar: Related Audits -->
        <aside class="sticky top-20 mt-8 lg:mt-0">
          <div class="bg-white rounded-2xl shadow-sm border border-zinc-200 p-5">
            <h3 class="text-sm font-bold uppercase text-zinc-500 mb-4 tracking-wide">Related Audits</h3>
            <div v-if="relatedAudits.length" class="flex flex-col gap-1">
              <router-link
                v-for="related in relatedAudits"
                :key="generateAuditSlug(related)"
                :to="`/audit/${generateAuditSlug(related)}`"
                class="group block rounded-xl p-3 hover:bg-zinc-50 transition-colors -mx-1"
              >
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="text-[10px] bg-zinc-200 text-zinc-600 px-2 py-0.5 rounded-full font-bold">
                    {{ related.year }}
                  </span>
                  <span class="text-sm font-semibold text-zinc-900 group-hover:text-brand-orange transition-colors leading-tight">
                    {{ related.city_town || related.city }}
                  </span>
                </div>
                <p v-if="related.streets_intersections" class="text-[11px] text-zinc-400 leading-snug line-clamp-2">
                  {{ related.streets_intersections }}
                </p>
              </router-link>
            </div>
            <p v-else class="text-sm text-zinc-400 italic">No related audits found.</p>
          </div>
        </aside>

      </div>
    </div>
  </div>
</template>
