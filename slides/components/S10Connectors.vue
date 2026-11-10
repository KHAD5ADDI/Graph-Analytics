<script setup lang="ts">
import { useBeat } from './useBeat'
const { active } = useBeat()
</script>
<template>
  <div class="slide s10">
    <div class="eyebrow fade" :class="{ on: active }">Connecting countries</div>
    <Kin class="h" text="Fiji, Uganda and Mauritius *connect* communities" :on="active" />
    <div class="hero fade" :class="{ on: active }" style="--d: .9s">
      <span class="big num">3/4</span>
      <p>of <b>Uganda</b>'s neighbours sit in other communities <span class="num">(54 of 71)</span></p>
    </div>
    <div class="list fade" :class="{ on: active }" style="--d: 1.2s">
      <div><b>Fiji</b><i /><span class="num">62.5%</span></div>
      <div><b>Uganda</b><i /><span class="num">76.1%</span></div>
      <div><b>Mauritius</b><i /><span class="num">57.6%</span></div>
      <p>share of neighbours outside their own community</p>
    </div>
    <p class="tonga fade" :class="{ on: active }" style="--d: 1.5s"><b>Tonga</b> ranks high too, only because Samoa reaches the graph through Tonga alone.</p>
  </div>
</template>
<style scoped>
.s10 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s10 .h { position: absolute; left: 136px; top: 196px; width: 700px; margin: 0; font: 400 80px/1 var(--serif); letter-spacing: -.02em; }
.s10 .hero { position: absolute; left: 140px; top: 420px; width: 620px; }
.s10 .hero .big { display: block; font-size: 150px; line-height: 1; color: var(--pen); }
.s10 .hero p { margin: 22px 0 0; font-size: 28px; line-height: 1.3; color: var(--ink-2); } .s10 b { color: var(--ink); font-weight: 650; }
.s10 .list { position: absolute; left: 140px; top: 700px; width: 560px; }
.s10 .list div { display: flex; align-items: baseline; gap: 12px; font-size: 27px; padding: 6px 0; }
.s10 .list i { flex: 1; border-bottom: 2px dotted var(--rule); transform: translateY(-6px); }
.s10 .list .num { font-size: 36px; }
.s10 .list p { margin: 6px 0 0; font-size: 20px; color: var(--ink-2); }
.s10 .tonga { position: absolute; left: 860px; top: 925px; width: 940px; margin: 0; font-size: 23px; color: var(--ink-2); }
</style>
