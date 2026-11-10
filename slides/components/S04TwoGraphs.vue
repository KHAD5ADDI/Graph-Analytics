<script setup lang="ts">
import { useBeat } from './useBeat'
const { active, click } = useBeat()
</script>
<template>
  <div class="slide s04">
    <div class="eyebrow fade" :class="{ on: active }">Two graphs</div>
    <Kin class="h" text="One recipe dataset, *two* graphs" :on="active" />
    <div class="block a fade" :class="{ on: active, dim: click >= 1 }" style="--d: .7s">
      <div class="row"><span class="big num">362</span><span class="lab">ingredients</span></div>
      <div class="row"><span class="mid num">10,853</span><span class="lab">weighted edges</span></div>
      <p>connected · any two ingredients at most <b>3 steps</b> apart</p>
    </div>
    <div class="block b fade" :class="{ on: active && click >= 1 }">
      <div class="row"><span class="big num">171</span><span class="lab">countries</span></div>
      <div class="row"><span class="mid num">2,066</span><span class="lab">edges · Jaccard ≥ 0.30</span></div>
      <p><b>5 components</b> · 166 countries in the largest</p>
    </div>
    <p class="kind fade" :class="{ on: active }" style="--d: 1.1s">undirected · simple · weighted</p>
  </div>
</template>
<style scoped>
.s04 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s04 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s04 .block { position: absolute; left: 140px; width: 740px; }
.s04 .block.a { top: 360px; } .s04 .block.b { top: 640px; }
.s04 .block.dim { opacity: .38; transition: opacity .6s; }
.s04 .row { display: flex; align-items: baseline; gap: 22px; }
.s04 .big { font-size: 150px; line-height: .9; letter-spacing: -.03em; }
.s04 .mid { font-size: 76px; line-height: 1.05; }
.s04 .lab { font-size: 30px; color: var(--ink-2); }
.s04 p { margin: 10px 0 0; font-size: 27px; color: var(--ink-2); } .s04 p b { color: var(--ink); font-weight: 650; }
.s04 .kind { position: absolute; left: 140px; top: 945px; margin: 0; font-size: 22px; letter-spacing: .1em; text-transform: uppercase; }
</style>
