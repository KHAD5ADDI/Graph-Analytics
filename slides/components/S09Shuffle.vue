<script setup lang="ts">
import { computed } from 'vue'
import { useBeat } from './useBeat'
import { sub } from '../world/clock'
import { TRAY, TRAYS, shuffleFrame } from '../world/states'
import nullData from '../data/shuffle_null.json'
const { active, click } = useBeat()
// opens on the real labels; click 1 runs the shuffles (timed), click 2 reveals the real line and p
const st = computed(() => click.value >= 2 ? 10 : click.value >= 1 ? sub.value : 0)
const N = nullData as any
const AX = { x: 140, w: 1640, lo: 0.2, hi: 0.7, base: 950, h: 170 }
const xs = (v: number) => AX.x + (v - AX.lo) / (AX.hi - AX.lo) * AX.w
const bins = computed(() => {
  const c = new Map<number, number>()
  for (const v of N.null as number[]) { const k = Math.round(v * 171); c.set(k, (c.get(k) ?? 0) + 1) }
  const max = Math.max(...c.values())
  return [...c.entries()].map(([k, n], i) => ({ x: xs(k / 171), h: n / max * AX.h, i }))
})
const grains = computed(() => {
  const out: { x: number, y: number }[] = []; const stack = new Map<number, number>()
  for (let s = 1; s <= Math.min(st.value, 8); s++) {
    const k = Math.round(shuffleFrame(s).agreement * 171); const n = stack.get(k) ?? 0; stack.set(k, n + 1)
    out.push({ x: xs(k / 171), y: AX.base - 12 - n * 22 })
  }
  return out
})
const readout = computed(() => {
  const s = st.value
  if (s === 0 || s >= 10) return { v: Math.round(N.observed * 100), l: 'real labels', pen: s >= 10 }
  if (s >= 9) return { v: Math.round(N.mean * 100), l: 'average of 1,000 shuffles', pen: false }
  return { v: Math.round(shuffleFrame(s).agreement * 100), l: `shuffle ${s}`, pen: false }
})
</script>
<template>
  <div class="slide s09">
    <div class="eyebrow fade" :class="{ on: active }">Is the match real?</div>
    <Kin class="h" text="Shuffled regions never come *close*" :on="active" />
    <div class="read fade" :class="{ on: active }" style="--d: 1s">
      <span class="num" :class="{ pen: readout.pen }">{{ readout.v }}%</span><p>{{ readout.l }}</p>
    </div>
    <div v-for="(t, k) in TRAYS" :key="k" class="tl fade" :class="{ on: active && t.size >= 6 }" :style="{ left: t.x - 40 + 'px', width: t.w + 80 + 'px', top: TRAY.base + 26 + 'px', '--d': 1.4 + 's' }">{{ t.majority }}</div>
    <div class="tl small fade" :class="{ on: active }" :style="{ left: TRAYS[6].x + 'px', top: TRAY.base + 26 + 'px', '--d': 1.4 + 's' }">+ 5 small</div>
    <p class="cap fade" :class="{ on: active }" style="--d: 1.6s">171 countries in their 11 communities · <b>filled</b>: in the community's main UN region</p>
    <svg class="hist" viewBox="0 0 1920 1080">
      <line :x1="AX.x" :x2="AX.x + AX.w" :y1="AX.base" :y2="AX.base" class="axis" />
      <g v-for="v in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]" :key="v"><line :x1="xs(v)" :x2="xs(v)" :y1="AX.base" :y2="AX.base + 8" class="axis" /><text :x="xs(v)" :y="AX.base + 34" class="tick">{{ Math.round(v * 100) }}%</text></g>
      <circle v-for="(g, i) in grains" :key="'g' + i" :cx="g.x" :cy="g.y" r="8" class="grain" />
      <rect v-for="b in bins" :key="b.i" :x="b.x - 6" :y="AX.base - b.h" width="12" :height="b.h" class="bar"
        :style="{ transform: `scaleY(${st >= 9 ? 1 : 0})`, transformOrigin: `${b.x}px ${AX.base}px`, transitionDelay: b.i * 0.03 + 's' }" />
      <g class="mark" :class="{ on: st >= 9 }"><line :x1="xs(N.mean)" :x2="xs(N.mean)" :y1="AX.base" :y2="AX.base - AX.h - 30" class="dash" /><text :x="xs(N.mean) - 12" :y="AX.base - AX.h - 40" text-anchor="end">shuffled mean {{ Math.round(N.mean * 100) }}%</text></g>
      <g class="mark" :class="{ on: st >= 9 }" style="transition-delay: .5s"><line :x1="xs(N.max)" :x2="xs(N.max)" :y1="AX.base" :y2="AX.base - 110" class="thin" /><text :x="xs(N.max) + 12" :y="AX.base - 92">best of 1,000: {{ Math.round(N.max * 100) }}%</text></g>
      <g class="mark real" :class="{ on: st >= 10 }"><line :x1="xs(N.observed)" :x2="xs(N.observed)" :y1="AX.base" :y2="AX.base - AX.h - 60" /><text :x="xs(N.observed) + 16" :y="AX.base - AX.h - 40">real labels {{ Math.round(N.observed * 100) }}%</text><text :x="xs(N.observed) + 16" :y="AX.base - AX.h + 10" class="p">p ≈ 0.001</text></g>
    </svg>
  </div>
</template>
<style scoped>
.s09 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s09 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s09 .read { position: absolute; right: 140px; top: 380px; text-align: right; }
.s09 .read .num { font-size: 170px; line-height: .85; transition: color .5s; } .s09 .read .num.pen { color: var(--pen); }
.s09 .read p { margin: 8px 0 0; font-size: 28px; color: var(--ink-2); }
.s09 .tl { position: absolute; text-align: center; font-size: 22px; color: var(--ink-2); }
.s09 .tl.small { text-align: left; width: 200px; }
.s09 .cap { position: absolute; left: 140px; top: 676px; margin: 0; font-size: 24px; color: var(--ink-2); } .s09 .cap b { color: var(--ink); }
.s09 .hist { position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: visible; }
.s09 .axis { stroke: var(--ink); stroke-width: 1.6; }
.s09 .tick { font: 500 22px var(--sans); fill: var(--ink-2); text-anchor: middle; }
.s09 .grain { fill: var(--ink-2); }
.s09 .bar { fill: rgba(117, 101, 90, .8); transition: transform .9s cubic-bezier(.3,.8,.2,1); }
.s09 .mark { opacity: 0; transition: opacity .7s; } .s09 .mark.on { opacity: 1; }
.s09 .mark text { font: 500 24px var(--sans); fill: var(--ink-2); }
.s09 .dash { stroke: var(--ink-2); stroke-width: 1.6; stroke-dasharray: 5 6; } .s09 .thin { stroke: var(--ink-2); stroke-width: 1.4; }
.s09 .real line { stroke: var(--pen); stroke-width: 5; } .s09 .real text { fill: var(--ink); font-weight: 650; font-size: 28px; }
.s09 .real .p { font: italic 400 54px var(--serif); fill: var(--pen); }
</style>
