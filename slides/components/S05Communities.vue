<script setup lang="ts">
import { useBeat } from './useBeat'
import extra from '../data/extra.json'
const { active, click } = useBeat()
const seeds = (extra as any).seeds as { seed: number, n: number }[]
const groups = [
  { x: 300, name: 'Vegetables, herbs, mushrooms', ex: 'shallot · laurel · carrot', n: 112, c: 'var(--c0)' },
  { x: 660, name: 'Sweet and baking', ex: 'cinnamon · vanilla · coconut', n: 97, c: 'var(--c1)' },
  { x: 990, name: 'Salad, sauce, beef, pork', ex: 'lettuce · mustard · beans', n: 57, c: 'var(--c2)' },
  { x: 1270, name: 'Ginger, soy, fish, lime', ex: 'ginger · shrimp · fish', n: 55, c: 'var(--c3)' },
  { x: 1560, name: 'Spices and legumes', ex: 'coriander · turmeric · clove', n: 41, c: 'var(--c4)' },
]
</script>
<template>
  <div class="slide s05">
    <div class="eyebrow fade" :class="{ on: active }">Louvain communities</div>
    <Kin class="h" text="Five groups of ingredients *used together*" :on="active" />
    <div class="hero fade" :class="{ on: active, gone: click >= 1 }" style="--d: .8s">
      <span class="big num">5</span>
      <div><b>communities</b><span>modularity <span class="num">0.40</span></span></div>
    </div>
    <div v-for="(g, i) in groups" :key="g.name" class="gname fade" :class="{ on: active && click >= 1 }"
      :style="{ left: g.x - 140 + 'px', '--d': .9 + i * .35 + 's' }">
      <em class="num"><i :style="{ background: g.c }" />{{ g.n }}</em><b>{{ g.name }}</b><span>{{ g.ex }}</span>
    </div>
    <div class="seeds fade" :class="{ on: active && click >= 2 }">
      <div class="tiles"><span v-for="s in seeds" :key="s.seed" :class="{ odd: s.n !== 5 }">{{ s.n }}</span></div>
      <p><b>5 communities in 28 of 30 seeds</b> · modularity 0.389 to 0.402 · groups used together, not cuisines</p>
    </div>
  </div>
</template>
<style scoped>
.s05 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s05 .h { position: absolute; left: 136px; top: 196px; width: 760px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s05 .hero { position: absolute; left: 140px; top: 470px; display: flex; align-items: center; gap: 28px; }
.s05 .hero .big { font-size: 260px; line-height: .8; }
.s05 .hero div { display: flex; flex-direction: column; gap: 8px; font-size: 34px; }
.s05 .hero b { font: 400 54px/1 var(--serif); } .s05 .hero span { color: var(--ink-2); }
.s05 .gname { position: absolute; top: 726px; width: 280px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; }
.s05 .gname i { display: inline-block; width: 26px; height: 4px; border-radius: 2px; margin-right: 10px; vertical-align: middle; }
.s05 .gname b { font: 400 31px/1.05 var(--serif); } .s05 .gname span { font-size: 21px; color: var(--ink-2); font-style: italic; }
.s05 .gname em { font-style: normal; font-size: 30px; color: var(--ink-2); margin-bottom: 6px; }
.s05 .seeds { position: absolute; left: 140px; right: 140px; top: 915px; display: flex; align-items: center; gap: 30px; }
.s05 .tiles { display: flex; gap: 5px; }
.s05 .tiles span { width: 25px; height: 34px; display: grid; place-items: center; font: 600 17px/1 var(--sans); background: rgba(42,32,25,.08); color: var(--ink); border-radius: 2px; }
.s05 .tiles span.odd { background: var(--pen); color: var(--paper); }
.s05 .seeds p { margin: 0; font-size: 23px; color: var(--ink-2); } .s05 .seeds b { color: var(--ink); font-weight: 650; }
</style>
