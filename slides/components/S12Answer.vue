<script setup lang="ts">
import { useBeat } from './useBeat'
const { active, click } = useBeat()
</script>
<template>
  <div class="slide s12">
    <div class="eyebrow fade" :class="{ on: active }">Conclusion</div>
    <Kin class="h" text="So, our *answer*" :on="active" />
    <div class="lines">
      <p class="fade" :class="{ on: active && click >= 1 }">Ingredients form <em>five stable</em> communities.</p>
      <p class="fade" :class="{ on: active && click >= 2 }">Which ingredients connect them depends on <em>what a step means</em>.</p>
      <p class="fade" :class="{ on: active && click >= 3 }">Countries that cook alike tend to <em>share a region</em>, far more than chance, but not completely.</p>
    </div>
    <div class="thanks fade" :class="{ on: active && click >= 3 }" style="--d: 2.2s">
      <b>Thank you</b><span>Khadidja Addi · Mathew Kristoffer Ewan Kapoor</span><span class="gh">github.com/KHAD5ADDI/Graph-Analytics</span>
    </div>
  </div>
</template>
<style scoped>
.s12 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s12 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s12 .lines { position: absolute; left: 140px; top: 370px; width: 800px; display: flex; flex-direction: column; gap: 30px; }
.s12 .lines p { margin: 0; font: 400 52px/1.06 var(--serif); letter-spacing: -.01em; }
.s12 .lines em { color: var(--pen); }
.s12 .thanks { position: absolute; left: 140px; top: 905px; display: flex; align-items: baseline; gap: 30px; font-size: 24px; color: var(--ink-2); }
.s12 .thanks b { font: italic 400 64px/1 var(--serif); color: var(--ink); }
.s12 .thanks .gh { color: var(--ink); font-weight: 550; }
</style>
