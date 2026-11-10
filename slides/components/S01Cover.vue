<script setup lang="ts">
import { useBeat } from './useBeat'
const { active, click } = useBeat()
</script>

<template>
  <div class="slide s01">
    <div class="eyebrow fade" :class="{ on: active }">Graph Analytics · Albert School 2026</div>
    <Kin class="title" tag="h1" text="Communities" :on="active" :delay="0.2" />
    <Kin class="title two" tag="h1" text="&amp; *brokers*" :on="active" :delay="0.38" />
    <Kin class="sub" tag="p" text="in ingredient networks of world cuisines" :on="active" :delay="0.6" :stagger="0.035" />
    <div class="names fade" :class="{ on: active }" style="--d: 1.1s">
      <span>Khadidja Addi</span><span>Mathew Kristoffer Ewan Kapoor</span>
    </div>
    <div class="plan">
      <div class="part fade" :class="{ on: active && click >= 1 }">
        <b class="num">01</b><div><span class="who">Khadidja</span><span>the data, the two graphs, the communities</span></div>
      </div>
      <div class="part fade" :class="{ on: active && click >= 1 }" style="--d: .12s">
        <b class="num">02</b><div><span class="who">Ewan</span><span>the brokers, the countries, our answer</span></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.s01 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s01 .title { position: absolute; left: 128px; margin: 0; font: 400 196px/.86 var(--serif); letter-spacing: -.035em; }
.s01 .title:not(.two) { top: 222px; }
.s01 .title.two { top: 392px; }
.s01 .title.two :deep(em) { color: var(--pen); }
.s01 .sub { position: absolute; left: 140px; top: 600px; margin: 0; max-width: 800px;
  font: italic 400 52px/1.08 var(--serif); color: var(--ink-2); }
.s01 .names { position: absolute; left: 140px; top: 742px; display: flex; flex-direction: column; gap: 6px;
  font: 500 28px/1.3 var(--sans); }
.s01 .plan { position: absolute; left: 140px; top: 862px; display: flex; gap: 72px; }
.s01 .part { display: flex; gap: 18px; align-items: baseline; }
.s01 .part b { font-size: 46px; color: var(--pen); font-weight: 400; }
.s01 .part div { display: flex; flex-direction: column; gap: 4px; font-size: 25px; color: var(--ink-2); }
.s01 .part .who { font-weight: 650; color: var(--ink); letter-spacing: .02em; }
</style>
