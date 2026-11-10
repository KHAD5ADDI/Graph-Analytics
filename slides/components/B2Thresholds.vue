<script setup lang="ts">
import extra from '../data/extra.json'
const keep = ['10/0.0', '10/0.5', '10/1.0', '20/0.0', '50/0.0']
const ing = (extra as any).sens_ing.filter((r: any) => keep.includes(r.min_cooccurrence + '/' + r.pmi_threshold))
const cty = (extra as any).sens_cty.filter((r: any) => r.profile === 'all' && ['0.2', '0.25', '0.3', '0.35', '0.4'].includes(String(+r.jaccard_threshold)))
const chosenIng = (r: any) => r.min_cooccurrence === '10' && r.pmi_threshold === '0.0'
const chosenCty = (r: any) => String(+r.jaccard_threshold) === '0.3'
</script>
<template>
  <div class="slide b2">
    <div class="eyebrow">Backup · thresholds</div>
    <h1 class="h">Modularity alone <em>cannot</em> choose the thresholds</h1>
    <div class="t ing"><p class="tt">Ingredient graph</p>
      <table><thead><tr><th>shared ≥</th><th>PMI &gt;</th><th>edges</th><th>components</th><th>communities</th><th>modularity</th></tr></thead>
        <tbody><tr v-for="r in ing" :key="r.min_cooccurrence + r.pmi_threshold" :class="{ on: chosenIng(r) }"><td>{{ r.min_cooccurrence }}</td><td>{{ r.pmi_threshold }}</td><td>{{ (+r.edges).toLocaleString('en-US') }}</td><td>{{ r.components }}</td><td>{{ r.louvain_communities }}</td><td>{{ (+r.modularity).toFixed(3) }}</td></tr></tbody></table></div>
    <div class="t cty"><p class="tt">Country graph</p>
      <table><thead><tr><th>Jaccard ≥</th><th>edges</th><th>components</th><th>largest</th><th>communities</th><th>modularity</th></tr></thead>
        <tbody><tr v-for="r in cty" :key="r.jaccard_threshold" :class="{ on: chosenCty(r) }"><td>{{ (+r.jaccard_threshold).toFixed(2) }}</td><td>{{ (+r.edges).toLocaleString('en-US') }}</td><td>{{ r.components }}</td><td>{{ r.lcc_size }}</td><td>{{ r.louvain_communities }}</td><td>{{ (+r.modularity).toFixed(3) }}</td></tr></tbody></table></div>
    <p class="cap">our choice is underlined · each threshold gives a different graph, and modularity rises as the graph falls apart</p>
  </div>
</template>
<style scoped>
.b2 .eyebrow { position: absolute; left: 140px; top: 150px; }
.b2 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 76px/1 var(--serif); } .b2 .h em { color: var(--pen); }
.b2 .t { position: absolute; top: 380px; width: 780px; } .b2 .t.ing { left: 140px; } .b2 .t.cty { left: 1000px; }
.b2 .tt { margin: 0 0 14px; font: 400 40px/1 var(--serif); }
.b2 table { width: 100%; border-collapse: collapse; font-size: 25px; font-variant-numeric: tabular-nums; }
.b2 th { font: 600 17px/1.2 var(--sans); letter-spacing: .05em; text-transform: uppercase; color: var(--ink-2); text-align: right; white-space: nowrap; padding: 8px; border-bottom: 1px solid var(--rule); }
.b2 td { text-align: right; padding: 10px 8px; border-bottom: 1px solid rgba(42,32,25,.07); }
.b2 tr.on td { font-weight: 700; background: rgba(194,65,45,.08); border-bottom: 2px solid var(--pen); }
.b2 .cap { position: absolute; left: 140px; top: 900px; margin: 0; font-size: 22px; color: var(--ink-2); }
</style>
