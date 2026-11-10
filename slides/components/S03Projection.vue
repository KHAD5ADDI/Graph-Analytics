<script setup lang="ts">
import { useBeat } from './useBeat'
import { sub } from '../world/clock'
import { RECIPES } from '../world/model'
import { SHORT } from '../world/states'
const { active, click } = useBeat()
const rows = [
  { pair: 'Salt + Garlic', together: 7571, expected: 6553.7, ratio: '1.16', pmi: '0.21' },
  { pair: 'Ginger + Soy sauce', together: 1010, expected: 226.3, ratio: '4.46', pmi: '2.16' },
]
const W = 420 / 7571
</script>
<template>
  <div class="slide s03">
    <div class="eyebrow fade" :class="{ on: active }">From recipes to a graph</div>
    <Kin class="h" text="Shared recipes become *edges*" :on="active" />
    <!-- 0: real recipes -->
    <div class="cards" :class="{ gone: click >= 1 }">
      <div v-for="(r, k) in RECIPES" :key="r.title" class="card fade" :class="{ on: active }" :style="{ '--d': .5 + k * .12 + 's' }">
        <span class="cu">{{ r.cuisine }}</span><b>{{ r.title }}</b>
        <ul><li v-for="i in r.ingredients" :key="i">{{ SHORT[i] ?? i }}</li></ul>
      </div>
    </div>
    <div class="total fade" :class="{ on: active, gone: click >= 1 }" style="--d: 1.1s">
      <span class="num">45,749</span><p>recipes in CulinaryDB, each a list of ingredients</p>
    </div>
    <!-- 1: bipartite, then projection -->
    <div class="heads fade" :class="{ on: active && click === 1 && sub < 1 }"><span class="r">recipes</span><span class="i">ingredients</span></div>
    <div class="rules fade" :class="{ on: active && click === 1 && sub >= 1 }" style="--d: .9s">
      <div><b class="num">362</b><span>ingredients in at least 50 recipes</span></div>
      <div><b>an edge</b><span>when a pair shares at least 10 recipes</span></div>
    </div>
    <!-- 2: counts against chance, 3: PMI -->
    <div class="compare" :class="{ shown: active && click >= 2 }">
      <div v-for="(r, k) in rows" :key="r.pair" class="row" :style="{ top: (k === 0 ? 0 : click >= 3 ? 110 : 250) + 'px' }">
        <div class="t"><b>{{ r.pair }}</b><span class="x num">×{{ r.ratio }}</span><span class="pmi num" :class="{ on: click >= 3 }">PMI {{ r.pmi }}</span></div>
        <div class="bars" :class="{ off: click >= 3 }">
          <div class="bar tog" :style="{ width: (click >= 2 ? r.together * W : 0) + 'px' }" /><span>{{ r.together.toLocaleString('en-US') }} together</span>
          <div class="bar exp" :style="{ width: (click >= 2 ? r.expected * W : 0) + 'px' }" /><span class="m">{{ Math.round(r.expected).toLocaleString('en-US') }} expected by chance</span>
        </div>
      </div>
      <div class="formula fade" :class="{ on: click >= 3 }" style="--d: .5s">
        <span class="lhs">PMI = log<sub>2</sub></span>
        <span class="frac"><span>recipes with both × N</span><span>recipes with a × recipes with b</span></span>
        <p>how much more often a pair occurs than if the two were independent · N = 45,749</p>
      </div>
    </div>
  </div>
</template>
<style scoped>
.s03 .eyebrow { position: absolute; left: 140px; top: 150px; }
.s03 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 92px/1 var(--serif); letter-spacing: -.02em; }
.s03 .cards { position: absolute; left: 140px; top: 360px; display: flex; gap: 36px; }
.s03 .card { width: 380px; height: 444px; padding: 26px 30px; background: rgba(236, 227, 208, .7); border: 1px solid var(--rule); }
.s03 .card .cu { display: block; font: 600 17px/1 var(--sans); letter-spacing: .16em; text-transform: uppercase; color: var(--ink-2); }
.s03 .card b { display: block; margin: 10px 0 14px; padding-bottom: 14px; border-bottom: 1.5px solid var(--ink); font: italic 400 50px/1 var(--serif); }
.s03 .card ul { margin: 0; padding: 0; list-style: none; font-size: 25px; line-height: 1.38; }
.s03 .total { position: absolute; left: 140px; top: 846px; display: flex; align-items: baseline; gap: 22px; }
.s03 .total .num { font-size: 100px; line-height: 1; }
.s03 .total p { margin: 0; font-size: 30px; color: var(--ink-2); }
.s03 .heads span { position: absolute; top: 318px; font: 600 19px/1 var(--sans); letter-spacing: .16em; text-transform: uppercase; color: var(--ink-2); }
.s03 .heads .r { left: 340px; } .s03 .heads .i { left: 920px; }
.s03 .rules { position: absolute; left: 140px; top: 440px; width: 640px; display: flex; flex-direction: column; gap: 44px; }
.s03 .rules div { display: flex; flex-direction: column; gap: 6px; }
.s03 .rules b { font: 400 76px/1 var(--serif); } .s03 .rules span { font-size: 28px; color: var(--ink-2); }
.s03 .compare { position: absolute; left: 1010px; top: 360px; width: 780px; height: 600px; opacity: 0; transition: opacity .6s .4s; }
.s03 .compare.shown { opacity: 1; }
.s03 .row { position: absolute; left: 0; right: 0; transition: top .8s cubic-bezier(.6,0,.2,1); }
.s03 .row .t { display: flex; align-items: baseline; gap: 24px; }
.s03 .row .t b { font: 400 54px/1 var(--serif); flex: 1; }
.s03 .row .x { font-size: 74px; line-height: 1; }
.s03 .row .pmi { width: 0; overflow: hidden; white-space: nowrap; font-size: 44px; color: var(--pen); opacity: 0; transition: width .7s, opacity .7s; }
.s03 .row .pmi.on { width: 180px; opacity: 1; }
.s03 .bars { display: grid; grid-template-columns: max-content 1fr; align-items: center; column-gap: 16px; row-gap: 12px; margin-top: 26px; transition: opacity .5s; }
.s03 .bars.off { opacity: 0; }
.s03 .bar { height: 28px; transition: width 1.1s cubic-bezier(.3,.8,.2,1) .5s; }
.s03 .bar.tog { background: var(--ink); } .s03 .bar.exp { border: 2px solid var(--ink); background: transparent; height: 26px; min-width: 2px; }
.s03 .bars span { font-size: 25px; } .s03 .bars .m { color: var(--ink-2); }
.s03 .formula { position: absolute; left: 0; top: 300px; display: flex; flex-wrap: wrap; align-items: center; gap: 18px; }
.s03 .formula .lhs { font: 400 66px/1 var(--serif); } .s03 .formula sub { font-size: .5em; }
.s03 .frac { display: inline-flex; flex-direction: column; align-items: center; font-size: 28px; }
.s03 .frac span:first-child { padding: 0 14px 8px; border-bottom: 2px solid var(--ink); } .s03 .frac span:last-child { padding-top: 8px; }
.s03 .formula p { flex-basis: 100%; text-wrap: balance; margin: 18px 0 0; font-size: 23px; color: var(--ink-2); }
</style>
