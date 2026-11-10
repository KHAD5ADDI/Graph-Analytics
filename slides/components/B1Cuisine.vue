<script setup lang="ts">
import { computed } from 'vue'
import extra from '../data/extra.json'
const COLS = ['#2F5A2A', '#9B3F6B', '#E2704A', '#3B7F8C', '#D99A1A']
const NAMES = ['vegetables, herbs', 'sweet, baking', 'salad, sauce, beef', 'ginger, soy, fish', 'spices, legumes']
const rows = computed(() => {
  const by = new Map<string, { n: number, r: number[] }>()
  for (const r of (extra as any).cuisine) {
    if (r.cuisine.startsWith('Misc')) continue
    const e = by.get(r.cuisine) ?? { n: +r.n_recipes, r: [0, 0, 0, 0, 0] }
    e.r[+r.community] = +r.ratio; by.set(r.cuisine, e)
  }
  const list = [...by.entries()].map(([c, e]) => ({ c, ...e, top: e.r.indexOf(Math.max(...e.r)) }))
  return list.sort((a, b) => a.top - b.top || Math.max(...b.r) - Math.max(...a.r))
})
const cell = (v: number, k: number) => {
  const a = v > 1 ? Math.min(1, Math.log2(v) / 2.4) : 0
  return { background: a ? COLS[k] + Math.round(a * 230).toString(16).padStart(2, '0') : 'transparent', color: a > 0.55 ? '#F5EFE3' : 'var(--ink)', fontWeight: v >= 2 ? 650 : 400 }
}
</script>
<template>
  <div class="slide b1">
    <div class="eyebrow">Backup · not in the report</div>
    <h1 class="h">Each group is <em>over-used</em> by a few cuisines</h1>
    <table>
      <thead><tr><th /><th v-for="(n, k) in NAMES" :key="k"><i :style="{ background: COLS[k] }" />{{ n }}</th></tr></thead>
      <tbody><tr v-for="r in rows" :key="r.c"><td class="c">{{ r.c }}</td><td v-for="(v, k) in r.r" :key="k" :style="cell(v, k)">{{ v.toFixed(2) }}×</td></tr></tbody>
    </table>
    <p class="cap">observed / expected use of each community's ingredients, CulinaryDB cuisine labels · a descriptive check on the same data</p>
  </div>
</template>
<style scoped>
.b1 .eyebrow { position: absolute; left: 140px; top: 150px; }
.b1 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 72px/1 var(--serif); letter-spacing: -.01em; }
.b1 .h em { color: var(--pen); }
.b1 table { position: absolute; left: 140px; top: 300px; width: 1640px; border-collapse: collapse; font-size: 18px; font-variant-numeric: tabular-nums; }
.b1 th { font: 600 19px/1.2 var(--sans); text-align: center; padding: 0 6px 8px; color: var(--ink-2); }
.b1 th i { display: block; width: 26px; height: 4px; margin: 0 auto 6px; }
.b1 td { text-align: center; padding: 0 6px; height: 27px; border-bottom: 1px solid rgba(42,32,25,.06); }
.b1 td.c { text-align: left; font-weight: 600; width: 330px; }
.b1 .cap { position: absolute; left: 140px; top: 952px; margin: 0; font-size: 19px; color: var(--ink-2); }
</style>
