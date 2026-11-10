<script setup lang="ts">
import { useBeat } from './useBeat'
const { active } = useBeat()
</script>
<template>
  <div class="slide s08">
    <div class="eyebrow fade" :class="{ on: active }">Countries and geography</div>
    <Kin class="h" text="Eleven communities, some *regional*, some mixed" :on="active" />
    <div class="calls">
      <div class="call fade" :class="{ on: active }" style="--d: 1.2s"><i style="background: var(--c4)" /><span class="num">9 of 9</span><p>countries in Asia</p></div>
      <div class="call fade" :class="{ on: active }" style="--d: 1.45s"><i style="background: var(--ink)" /><span class="num">5 of 6</span><p>in Oceania</p></div>
      <div class="call fade" :class="{ on: active }" style="--d: 1.7s"><i style="background: var(--c0)" /><span class="num">31 + 9</span><p>Europe with the Americas, in the largest one</p></div>
    </div>
    <p class="cap fade" :class="{ on: active }" style="--d: 1.9s">each dot is a country, coloured by its Louvain community</p>
  </div>
</template>
<style scoped>
.s08 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s08 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s08 .calls { position: absolute; left: 1470px; top: 400px; width: 330px; display: flex; flex-direction: column; gap: 34px; }
.s08 .call i { display: block; width: 16px; height: 16px; border-radius: 50%; margin-bottom: 10px; }
.s08 .call .num { font-size: 92px; line-height: .9; }
.s08 .call p { margin: 6px 0 0; font-size: 25px; color: var(--ink-2); line-height: 1.25; }
.s08 .cap { position: absolute; left: 1470px; top: 318px; width: 330px; margin: 0; font-size: 21px; color: var(--ink-2); }
</style>
