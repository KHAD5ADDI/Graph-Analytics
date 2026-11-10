<script setup lang="ts">
import { computed } from 'vue'
// Kinetic serif line. Words wrapped in *stars* become the italic emphasis with a hand-drawn pen underline.
const props = withDefaults(defineProps<{ text: string, on: boolean, delay?: number, stagger?: number, tag?: string }>(),
  { delay: 0.15, stagger: 0.055, tag: 'h1' })
const words = computed(() => props.text.split(' ').map((raw, i) => {
  const em = raw.startsWith('*')
  const clean = raw.replace(/\*/g, '')
  return { text: clean, em, d: props.delay + i * props.stagger }
}))
const last = computed(() => props.delay + words.value.length * props.stagger + 0.35)
</script>

<template>
  <component :is="tag" class="kin" :class="{ on }">
    <template v-for="(w, i) in words" :key="i">
      <em v-if="w.em" class="w" :style="{ '--d': w.d + 's', '--ud': last + 's' }">{{ w.text }}<svg class="uline" viewBox="0 0 200 20" preserveAspectRatio="none"><path d="M2 13 C 40 6, 90 16, 130 9 S 185 8, 198 11" /></svg></em>
      <span v-else class="w" :style="{ '--d': w.d + 's' }">{{ w.text }}</span>{{ ' ' }}
    </template>
  </component>
</template>
