<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
// A Manim clip on the paper: transparent WebM (MP4 fallback); the poster stands in for print and reduced motion.
const props = defineProps<{ name: string, active: boolean, print?: boolean }>()
const video = ref<HTMLVideoElement | null>(null)
const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
const still = computed(() => props.print || reduced)
async function play() {
  await nextTick()
  const v = video.value
  if (!v || !props.active) return
  v.currentTime = 0
  v.play().catch(() => {})
}
watch(() => [props.name, props.active], play, { immediate: true })
</script>

<template>
  <div class="clip">
    <img v-if="still" :src="`/media/${name}.png`" alt="">
    <video v-else ref="video" :key="name" muted playsinline preload="auto" :poster="`/media/${name}.png`" @loadeddata="play">
      <source :src="`/media/${name}.webm`" type="video/webm">
      <source :src="`/media/${name}.mp4`" type="video/mp4">
    </video>
  </div>
</template>

<style scoped>
.clip { position: absolute; inset: 0; width: 1920px; height: 1080px; z-index: 1; pointer-events: none; }
.clip video, .clip img { width: 1920px; height: 1080px; display: block; }
</style>
