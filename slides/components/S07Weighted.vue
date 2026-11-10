<script setup lang="ts">
import { useBeat } from './useBeat'
import { SCATTER as S } from '../world/states'
const { active, click } = useBeat()
</script>
<template>
  <div class="slide s07">
    <div class="eyebrow fade" :class="{ on: active }">Brokers, weighted</div>
    <Kin class="h" text="Let strong association mean a *short* step" :on="active" />
    <div class="hero fade" :class="{ on: active }" style="--d: .9s">
      <span class="big num">175 → 1</span>
      <p><b>Couscous</b>, in only 245 recipes, links vegetables and broth with fruit like apricot and currant</p>
      <p class="rho">ρ with frequency <span class="num">0.32</span></p>
    </div>
    <div class="robust fade" :class="{ on: active && click >= 1 }">
      <p class="t">Second distance, 1/(1+PMI)</p>
      <p>Shallot <b>1</b> · Couscous <b>2</b> · Coconut <b>3</b> · Saffron <b>6</b> · <s>Lasagna 2 → 26</s></p>
      <p class="muted">partly robust, and the report says so</p>
    </div>
    <svg class="diag fade" :class="{ on: active }" viewBox="0 0 1920 1080"><line :x1="S.x" :y1="S.y" :x2="S.x + S.w" :y2="S.y + S.h" /><text :transform="`translate(${S.x + S.w * 0.55} ${S.y + S.h * 0.55 - 16}) rotate(${Math.atan2(S.h, S.w) * 180 / Math.PI})`" text-anchor="middle">same rank under both</text></svg>
    <div class="axis fade" :class="{ on: active }" style="--d: .5s">
      <span class="x" :style="{ left: S.x + 'px', top: S.y + S.h + 26 + 'px', width: S.w + 'px' }"><b>rank with hops</b>, 1 → 362</span>
      <span class="y" :style="{ left: S.x - 48 + 'px', top: S.y - 4 + 'px' }">1</span>
      <span class="y2" :style="{ left: S.x - 48 + 'px', top: S.y - 52 + 'px' }"><b>{{ click >= 1 ? 'rank with 1/(1+PMI)' : 'rank with 1/PMI' }}</b> ↓</span>
    </div>
  </div>
</template>
<style scoped>
.s07 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s07 .h { position: absolute; left: 136px; top: 196px; width: 640px; margin: 0; font: 400 80px/1 var(--serif); letter-spacing: -.02em; }
.s07 .hero { position: absolute; left: 140px; top: 470px; width: 600px; }
.s07 .hero .big { font-size: 130px; line-height: .9; color: var(--pen); letter-spacing: -.02em; }
.s07 .hero p { margin: 16px 0 0; font-size: 27px; line-height: 1.32; color: var(--ink-2); } .s07 .hero b { color: var(--ink); font-weight: 650; }
.s07 .hero .rho { font-size: 26px; } .s07 .hero .rho .num { font-size: 44px; color: var(--ink); }
.s07 .robust { position: absolute; left: 140px; top: 830px; width: 640px; }
.s07 .robust p { margin: 0 0 6px; font-size: 25px; } .s07 .robust .t { font: 600 19px/1 var(--sans); letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); margin-bottom: 12px; }
.s07 .robust s { text-decoration-color: var(--pen); text-decoration-thickness: 2px; }
.s07 .diag { position: absolute; inset: 0; width: 1920px; height: 1080px; z-index: -1; pointer-events: none; }
.s07 .diag line { stroke: rgba(42,32,25,.28); stroke-width: 1.5; stroke-dasharray: 6 8; }
.s07 .diag text { font: italic 400 26px var(--serif); fill: var(--ink-2); }
.s07 .axis span { position: absolute; font-size: 21px; color: var(--ink-2); }
.s07 .axis b { color: var(--ink); font-weight: 600; }
.s07 .axis .x { text-align: right; }
</style>
