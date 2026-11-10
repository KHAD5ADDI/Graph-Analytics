<script setup lang="ts">
import { useBeat } from './useBeat'
const { active, click } = useBeat()
</script>

<template>
  <div class="slide s02">
    <div :class="{ gone: click >= 1 }" class="beat0">
      <div class="eyebrow fade" :class="{ on: active }">Counting first</div>
      <Kin class="h" text="Counting tells us what is *common*" :on="active" />
      <p class="axis fade" :class="{ on: active }" style="--d: 1.2s">362 ingredients, ranked by the number of recipes that use them</p>
    </div>
    <div class="beat1" :class="{ hidden: click < 1 }">
      <div class="eyebrow fade" :class="{ on: active && click >= 1 }">Our question</div>
      <Kin class="q" text="Which *communities* and which connecting ingredients emerge from recipe data?" :on="active && click >= 1" :delay="0.5" :stagger="0.045" />
      <p class="q2 fade" :class="{ on: active && click >= 1 }" style="--d: 1.3s">And do cuisines that use similar ingredients sit close on the map?</p>
    </div>
  </div>
</template>

<style scoped>
.s02 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s02 .h { position: absolute; left: 136px; top: 200px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s02 .axis { position: absolute; left: 140px; top: 950px; margin: 0; font-size: 22px; color: var(--ink-2); letter-spacing: .02em; }
.s02 .beat1.hidden { pointer-events: none; }
.s02 .q { position: absolute; left: 136px; top: 200px; width: 700px; margin: 0; font: 400 86px/1.0 var(--serif); letter-spacing: -.02em; }
.s02 .q2 { position: absolute; left: 140px; top: 760px; width: 640px; margin: 0; font: italic 400 44px/1.15 var(--serif); color: var(--ink-2); }
</style>
