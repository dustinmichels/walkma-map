<script setup lang="ts">
import { ArrowLeft, ChevronRight, Home, Menu } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { isMenuOpen } from '../state';

const router = useRouter();
</script>

<template>
  <div class="min-h-screen bg-zinc-50 font-sans text-slate-900">
    <header class="bg-brand-orange shadow-lg flex items-center sticky top-0 z-10">
      <button
        @click="router.push('/')"
        class="bg-black/20 text-white flex items-center gap-1.5 text-sm font-semibold hover:bg-black/30 transition-colors py-3 px-4 self-stretch"
        aria-label="Back to map"
      >
        <ArrowLeft :size="18" />
        Back to Map
      </button>
      <h1 class="text-white text-sm font-bold tracking-tight truncate px-4 flex-grow">
        Walk MA - Walk Audit Dashboard
      </h1>
      <button
        @click="isMenuOpen = true"
        class="text-white hover:bg-black/20 p-2 rounded-lg transition-colors ml-auto mr-4"
        aria-label="Open menu"
      >
        <Menu :size="24" />
      </button>
    </header>

    <main class="max-w-prose mx-auto px-4 py-8">
      <!-- Breadcrumb -->
      <nav class="flex items-center gap-1 text-sm text-zinc-500 mb-6">
        <router-link to="/" class="flex items-center gap-1 hover:text-brand-orange transition-colors font-medium">
          <Home :size="14" />
          Home
        </router-link>
        <ChevronRight :size="14" class="text-zinc-400" />
        <span class="text-zinc-700 font-medium">About</span>
      </nav>


      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-zinc-200 overflow-hidden space-y-4">
        <div class="p-8 space-y-4">
          <h2 class="text-2xl font-bold text-slate-800 mb-4">About</h2>
          <p class="text-slate-700 leading-relaxed">
            This data dashboard was created in 2026 in collaboration with a team of students in the
            <a href="https://as.tufts.edu/uep/" target="_blank"
              class="text-brand-orange hover:underline font-medium">Tufts University Urban and Environmental Policy and
              Planning (UEP)</a>
            program:
            <a href="https://dustinmichels.com/" target="_blank"
              class="text-brand-orange hover:underline font-medium">Dustin Michels</a>,
            Jordan Bryant, Olivia Franklin, Victoria Lendino, Ken Wang, and Marian Yabe.
          </p>
          <p class="text-slate-700 leading-relaxed">
            It fetches live data from the
            <a href="https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/edit?gid=379989993#gid=379989993"
              target="_blank" class="text-brand-orange hover:underline font-medium">Walk Massachusetts audit database
              spreadsheet</a>
            and displays it in an interactive manner.
          </p>
        </div>

        <!-- Team Photo -->
        <img src="/data/images/group/team.jpg" alt="Walk MA team" class="w-full object-cover" />
      </div>
    </main>
  </div>
</template>
