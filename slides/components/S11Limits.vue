<script setup lang="ts">
import { useBeat } from './useBeat'
const { active, click } = useBeat()
const items = [
  ['Sampled recipes', 'about half of them are US or Italian'],
  ['Small country profiles', 'around 16 ingredients: one ingredient can add or remove an edge'],
  ['Seed-dependent Louvain', 'which is why we checked 30 seeds'],
  ['The distance choice', 'weighted brokers depend on how PMI becomes a distance'],
]
</script>
<template>
  <div class="slide s11">
    <div class="eyebrow fade" :class="{ on: active }">Limits</div>
    <Kin class="h" text="What our answer *depends on*" :on="active" />
    <div class="items">
      <div v-for="(it, i) in items" :key="i" class="it fade" :class="{ on: active && click >= i + 1 }">
        <span class="num">0{{ i + 1 }}</span><b>{{ it[0] }}</b><p>{{ it[1] }}</p>
      </div>
    </div>
  </div>
</template>
<style scoped>
.s11 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s11 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s11 .items { position: absolute; left: 140px; top: 370px; width: 760px; display: flex; flex-direction: column; gap: 28px; }
.s11 .it { display: grid; grid-template-columns: 90px 1fr; column-gap: 10px; border-top: 1px solid var(--rule); padding-top: 18px; }
.s11 .it .num { grid-row: span 2; font-size: 44px; color: var(--pen); line-height: 1; }
.s11 .it b { font: 400 54px/1 var(--serif); }
.s11 .it p { margin: 8px 0 0; font-size: 25px; line-height: 1.3; text-wrap: balance; color: var(--ink-2); }
</style>
