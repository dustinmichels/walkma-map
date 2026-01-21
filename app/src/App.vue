<script setup>
import { ref } from 'vue'

const selectedCity = ref('')
const cities = ['Belchertown', 'Blandford', 'Boston']

// Just generating some random variations based on city choice for visual flavor
const getMockStats = () => {
  if (!selectedCity.value) return {}

  const statsMap = {
    Boston: {
      audits: 482,
      score: 74,
      users: 1250,
      areas: ['Downtown Crossings', 'Dorchester Ave Intersections', 'School Zones'],
    },
    Belchertown: {
      audits: 12,
      score: 42,
      users: 45,
      areas: ['Route 202 Corridor', 'Town Common Sidewalks'],
    },
    Blandford: {
      audits: 3,
      score: 31,
      users: 12,
      areas: ['Main St Sightlines', 'State Route Accessibility'],
    },
  }
  return statsMap[selectedCity.value] || statsMap['Boston']
}
</script>

<template>
  <div class="min-h-screen flex flex-col font-sans text-slate-900">
    <!-- Header -->
    <header class="bg-brand-orange shadow-lg py-4 px-6 flex justify-between items-center z-10">
      <div class="flex items-center gap-3">
        <div class="bg-black p-2 rounded-lg">
          <i class="fas fa-walking text-white text-2xl"></i>
        </div>
        <h1 class="text-white text-2xl font-bold tracking-tight">Walk MA - Walk Audit Dashboard</h1>
      </div>
      <!-- Navigation removed as requested -->
    </header>

    <!-- Main Content Area -->
    <main
      class="flex-grow flex flex-col md:flex-row p-4 md:p-6 gap-6 h-[calc(100vh-72px)] overflow-hidden"
    >
      <!-- Left Side: Map Placeholder -->
      <div
        class="flex-grow relative rounded-xl overflow-hidden border-2 border-zinc-200 bg-zinc-100 shadow-inner group"
      >
        <div
          class="map-placeholder w-full h-full flex flex-col items-center justify-center opacity-60"
        >
          <i
            class="fas fa-map-marked-alt text-6xl text-zinc-400 mb-4 group-hover:scale-110 transition-transform duration-500"
          ></i>
          <p class="text-zinc-500 font-medium text-lg uppercase tracking-widest">
            Interactive Map Canvas
          </p>
          <p class="text-zinc-400 text-sm mt-2">Geospatial Data Engine Loading...</p>
        </div>

        <!-- Floating Controls -->
        <div class="absolute top-4 left-4 flex flex-col gap-2">
          <button class="bg-white p-2 rounded shadow hover:bg-zinc-50 border border-zinc-200">
            <i class="fas fa-plus"></i>
          </button>
          <button class="bg-white p-2 rounded shadow hover:bg-zinc-50 border border-zinc-200">
            <i class="fas fa-minus"></i>
          </button>
        </div>

        <div class="absolute bottom-6 right-6">
          <div class="bg-white/90 backdrop-blur-sm p-3 rounded-lg shadow-lg border border-zinc-200">
            <div class="flex items-center gap-2 mb-1">
              <span class="w-3 h-3 rounded-full bg-brand-orange"></span>
              <span class="text-xs font-bold">Audit Completed</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-black"></span>
              <span class="text-xs font-bold">Pending Audit</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Side: Data Panel -->
      <aside
        class="w-full md:w-[400px] flex flex-col bg-white rounded-xl shadow-xl border border-zinc-200 overflow-hidden"
      >
        <!-- Panel Header -->
        <div class="p-5 border-b border-zinc-100 bg-zinc-50/50">
          <h2 class="text-lg font-bold flex items-center gap-2 text-zinc-800">
            <i class="fas fa-sliders-h text-brand-orange"></i>
            Analysis Parameters
          </h2>
        </div>

        <!-- Interactive Elements -->
        <div class="flex-grow overflow-y-auto p-5 custom-scrollbar space-y-6">
          <!-- City Selection -->
          <div class="space-y-2">
            <label
              for="city-select"
              class="block text-sm font-bold text-zinc-600 uppercase tracking-wider"
            >
              Select City
            </label>
            <div class="relative">
              <select
                id="city-select"
                v-model="selectedCity"
                class="w-full appearance-none bg-white border-2 border-zinc-200 rounded-lg py-3 px-4 focus:outline-none focus:border-brand-orange transition-colors cursor-pointer pr-10"
              >
                <option value="" disabled>Choose a city...</option>
                <option v-for="city in cities" :key="city" :value="city">
                  {{ city }}
                </option>
              </select>
              <div
                class="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-zinc-400"
              >
                <i class="fas fa-chevron-down"></i>
              </div>
            </div>
          </div>

          <!-- Statistics / Info Cards (Dynamic) -->
          <div
            v-if="selectedCity"
            class="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
          >
            <div class="p-4 rounded-lg bg-orange-50 border-l-4 border-brand-orange">
              <h3 class="font-bold text-brand-orange text-sm uppercase">Active Audits</h3>
              <p class="text-3xl font-black text-black">
                {{ getMockStats().audits }}
              </p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="bg-zinc-50 p-3 rounded border border-zinc-100">
                <span class="text-[10px] font-bold text-zinc-400 uppercase">Walkability Score</span>
                <p class="text-xl font-bold">{{ getMockStats().score }}/100</p>
              </div>
              <div class="bg-zinc-50 p-3 rounded border border-zinc-100">
                <span class="text-[10px] font-bold text-zinc-400 uppercase">Participants</span>
                <p class="text-xl font-bold">{{ getMockStats().users }}</p>
              </div>
            </div>

            <div class="pt-4">
              <h4 class="text-xs font-bold text-zinc-500 uppercase mb-3">Priority Focus Areas</h4>
              <ul class="space-y-2">
                <li
                  v-for="area in getMockStats().areas"
                  class="flex items-center gap-2 text-sm p-2 bg-white border border-zinc-100 rounded hover:shadow-sm transition-shadow"
                >
                  <i class="fas fa-exclamation-triangle text-brand-orange text-xs"></i>
                  {{ area }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Placeholder if no city selected -->
          <div
            v-else
            class="h-64 flex flex-col items-center justify-center text-zinc-400 text-center border-2 border-dashed border-zinc-100 rounded-xl"
          >
            <i class="fas fa-city text-4xl mb-3 opacity-20"></i>
            <p class="text-sm">
              Select a city from the menu above to view walk audit metrics and geospatial data
              layers.
            </p>
          </div>
        </div>

        <!-- Footer Action -->
        <div class="p-5 bg-zinc-50 border-t border-zinc-100">
          <button
            :disabled="!selectedCity"
            class="w-full py-3 rounded-lg font-bold text-white transition-all transform active:scale-95 shadow-lg"
            :class="selectedCity ? 'bg-black hover:bg-zinc-800' : 'bg-zinc-300 cursor-not-allowed'"
          >
            Export PDF Report
          </button>
        </div>
      </aside>
    </main>

    <!-- Footer -->
    <footer class="bg-zinc-900 text-zinc-500 py-3 px-6 text-xs flex justify-between">
      <p>&copy; 2024 MassDOT Walkability Initiative</p>
      <div class="flex gap-4">
        <a href="#" class="hover:text-white">Privacy Policy</a>
        <a href="#" class="hover:text-white">Data Sources</a>
      </div>
    </footer>
  </div>
</template>

<style>
:root {
  --brand-orange: #ffa100;
}
.bg-brand-orange {
  background-color: var(--brand-orange);
}
.text-brand-orange {
  color: var(--brand-orange);
}
.border-brand-orange {
  border-color: var(--brand-orange);
}

body {
  background-color: #f8f9fa;
  margin: 0; /* Reset default margin which might be there */
}

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

.map-placeholder {
  background-image:
    linear-gradient(45deg, #e5e7eb 25%, transparent 25%),
    linear-gradient(-45deg, #e5e7eb 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #e5e7eb 75%),
    linear-gradient(-45deg, transparent 75%, #e5e7eb 75%);
  background-size: 20px 20px;
  background-position:
    0 0,
    0 10px,
    10px -10px,
    -10px 0px;
}
</style>
