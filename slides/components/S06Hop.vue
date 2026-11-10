<script setup lang="ts">
import { useBeat } from './useBeat'
const { active, click } = useBeat()
</script>
<template>
  <div class="slide s06">
    <div class="eyebrow fade" :class="{ on: active }">Brokers</div>
    <Kin class="h" :class="{ gone: click >= 1 }" text="A broker lies on *many* shortest paths" :on="active" />
    <Kin class="h" text="Equal steps make *popular* brokers" :on="active && click >= 1" :delay=".3" :stagger=".045" />
    <div class="defs fade" :class="{ on: active, gone: click >= 1 }" style="--d: .9s">
      <p><b>Broker</b> high betweenness: on many shortest paths between other ingredients</p>
      <p><b>Bridge</b> an edge whose removal disconnects the graph: <b>we have none</b></p>
    </div>
    <div class="hero fade" :class="{ on: active && click >= 1 }" style="--d: .9s">
      <div class="rho"><span class="num big">0.97</span><span>Spearman ρ between hop betweenness and frequency</span></div>
      <div class="bar">
        <div class="seg s1" style="width: 16.6%"><b class="num">16.6%</b><span>1 hop</span></div>
        <div class="seg s2" style="width: 81.5%"><b class="num">81.5%</b><span>2 hops</span></div>
        <div class="seg s3" style="width: 1.9%"><b class="num">1.9%</b><span>3</span></div>
      </div>
      <p class="cap">of all ingredient pairs: almost every pair is one or two steps apart</p>
    </div>
  </div>
</template>
<style scoped>
.s06 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s06 .h { position: absolute; left: 136px; top: 196px; width: 760px; margin: 0; font: 400 86px/1 var(--serif); letter-spacing: -.02em; }
.s06 .defs { position: absolute; left: 140px; top: 520px; width: 640px; display: flex; flex-direction: column; gap: 26px; }
.s06 .defs p { margin: 0; font-size: 30px; line-height: 1.3; color: var(--ink-2); } .s06 .defs b { color: var(--ink); font-weight: 650; }
.s06 .hero { position: absolute; left: 140px; top: 470px; width: 660px; }
.s06 .rho { display: flex; align-items: center; gap: 24px; }
.s06 .rho .big { font-size: 170px; line-height: .8; color: var(--pen); }
.s06 .rho span:last-child { font-size: 25px; color: var(--ink-2); max-width: 300px; }
.s06 .bar { display: flex; margin-top: 60px; height: 58px; gap: 3px; }
.s06 .seg { position: relative; background: rgba(42,32,25,.14); }
.s06 .seg.s2 { background: var(--ink); }
.s06 .seg b, .s06 .seg span { position: absolute; left: 0; white-space: nowrap; }
.s06 .seg b { top: -42px; font-size: 32px; } .s06 .seg span { top: 70px; font-size: 22px; color: var(--ink-2); }
.s06 .seg.s3 b { left: auto; right: 0; } .s06 .seg.s3 span { left: auto; right: 0; }
.s06 .cap { text-wrap: balance; margin: 112px 0 0; font-size: 23px; color: var(--ink-2); }
</style>
