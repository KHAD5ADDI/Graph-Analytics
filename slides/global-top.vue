<script setup lang="ts">
import { computed, watch } from 'vue'
import { useNav } from '@slidev/client'
import { MAIN_PAGES, pageInfo } from './world/pages'
const nav = useNav()
const info = computed(() => pageInfo(nav.currentPage.value))
const total = MAIN_PAGES
// a slide change delays the new page's words until the world has mostly moved (style.css --base)
let baseTimer: number | undefined
watch(() => nav.currentPage.value, () => {
  if (typeof document === 'undefined') return
  document.documentElement.style.setProperty('--base', '.45s')
  clearTimeout(baseTimer)
  baseTimer = window.setTimeout(() => document.documentElement.style.setProperty('--base', '0s'), 1700)
})
const who = computed(() => info.value.speaker === 'Both' ? 'Khadidja · Ewan' : info.value.speaker)
</script>

<template>
  <div class="grain" />
  <div v-if="nav.currentPage.value > 1 && nav.currentPage.value <= total" class="chrome">
    <span>Ingredient networks</span>
    <span class="who"><i class="dot" />{{ who }}</span>
    <span class="pg">{{ String(nav.currentPage.value).padStart(2, '0') }}</span>
  </div>
  <div v-if="nav.currentPage.value <= total" class="progress">
    <i v-for="p in total" :key="p" :class="{ done: p < nav.currentPage.value, now: p === nav.currentPage.value }" />
  </div>
</template>
