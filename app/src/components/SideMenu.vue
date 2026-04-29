<script setup lang="ts">
import { isMenuOpen } from '../state'
import { Home, ExternalLink, Info, X } from 'lucide-vue-next'
</script>

<template>
  <div class="fixed inset-0 z-50 pointer-events-none">
    <!-- Backdrop: fade in when open -->
    <div
      class="absolute inset-0 bg-black/50 transition-opacity duration-300 pointer-events-auto"
      :class="isMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'"
      @click="isMenuOpen = false"
    ></div>

    <!-- Side Panel: slide in from right -->
    <div
      class="absolute top-0 right-0 h-full w-64 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col pointer-events-auto"
      :class="isMenuOpen ? 'translate-x-0' : 'translate-x-full'"
    >
      <div class="p-4 border-b flex justify-between items-center bg-brand-orange text-white">
        <h2 class="text-lg font-bold tracking-tight">Menu</h2>
        <button
          @click="isMenuOpen = false"
          class="p-1 hover:bg-black/20 rounded-md transition-colors"
          aria-label="Close menu"
        >
          <X :size="20" />
        </button>
      </div>

      <nav class="flex-grow p-2">
        <ul class="space-y-1 font-medium text-slate-800">
          <li>
            <router-link
              to="/"
              class="flex items-center gap-3 p-3 hover:bg-zinc-100 rounded-lg transition-colors"
              @click="isMenuOpen = false"
            >
              <Home :size="18" class="text-slate-500" />
              Home Dashboard
            </router-link>
          </li>
          <li>
            <router-link
              to="/about"
              class="flex items-center gap-3 p-3 hover:bg-zinc-100 rounded-lg transition-colors"
              @click="isMenuOpen = false"
            >
              <Info :size="18" class="text-slate-500" />
              About
            </router-link>
          </li>
          <li>
            <a
              href="https://walkmass.org/"
              target="_blank"
              class="flex items-center gap-3 p-3 hover:bg-zinc-100 rounded-lg transition-colors mt-2"
            >
              <ExternalLink :size="18" class="text-slate-500" />
              Visit Walk MA
            </a>
          </li>
        </ul>
      </nav>
      
      <div class="p-4 border-t text-sm text-zinc-500 text-center">
        Walk MA Audit Dashboard
      </div>
    </div>
  </div>
</template>
