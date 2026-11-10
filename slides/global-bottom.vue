<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useNav } from '@slidev/client'
import gsap from 'gsap'
import { CTY_EDGES, ING_EDGES, INK2, NODES, PAPER, type RGB, type Target } from './world/model'
import { MAP, worldState, type WorldState } from './world/states'
import { pageInfo } from './world/pages'
import { sub } from './world/clock'
import extra from './data/extra.json'
const landPath = (extra as any).land as string
const land = ref(0)
const landTf = ref('none')

const nav = useNav()
const canvas = ref<HTMLCanvasElement | null>(null)
const N = NODES.length

interface Cur { x: number, y: number, r: number, c: RGB, a: number, stemY: number, stemA: number, ring: number,
  label: string, labelA: number, labelSize: number, labelSide: string, labelWeight: number, ldx: number, ldy: number, lat: [number, number] | null,
  hollow: boolean, square: boolean }
const cur: Cur[] = NODES.map(() => ({ x: 960, y: 540, r: 3, c: [42, 32, 25], a: 0, stemY: 930, stemA: 0, ring: 0,
  label: '', labelA: 0, labelSize: 24, labelSide: 'r', labelWeight: 500, ldx: 0, ldy: 0, lat: null, hollow: false, square: false }))
let from: Cur[] = cur.map(c => ({ ...c }))
let to: Cur[] = cur.map(c => ({ ...c }))
let delays = new Float32Array(N)
const edges = { ing: 0, cty: 0, fromIng: 0, fromCty: 0, toIng: 0, toCty: 0 }
interface Spec { from: number, to: number, a: number, w: number, c: RGB }
let specCur = new Map<string, Spec>()
let specFrom = new Map<string, Spec>()
let specTo = new Map<string, Spec>()
let state: WorldState | undefined
const phase = NODES.map((_, i) => (i * 2.399963) % (Math.PI * 2))
const prog = { p: 1 }
let tween: gsap.core.Tween | undefined
let raf = 0
let ctx: CanvasRenderingContext2D | null = null
let scale = 1
const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

function toCur(t: Target | null, prev: Cur): Cur {
  if (!t) return { ...prev, a: 0, stemA: 0, ring: 0, labelA: 0 }
  return {
    x: t.x, y: t.y, r: t.r, c: t.c, a: t.a, stemY: t.stemY ?? prev.stemY, stemA: t.stemA ?? 0, ring: t.ring ?? 0,
    label: t.label ?? prev.label, labelA: t.labelA ?? 0, labelSize: t.labelSize ?? 24,
    labelSide: t.labelSide ?? 'r', labelWeight: t.labelWeight ?? 500, ldx: t.labelDX ?? 0, ldy: t.labelDY ?? 0, lat: t.labelAt ?? null,
    hollow: !!t.hollow, square: !!t.square,
  }
}

function apply(page: number, click: number, instant = false) {
  const info = pageInfo(page)
  state = worldState(info.world, click, sub.value)
  from = cur.map(c => ({ ...c, c: [...c.c] as RGB }))
  to = state.targets.map((t, i) => {
    const next = toCur(t, cur[i])
    // invisible nodes jump to their target so they appear in place
    if (cur[i].a < 0.02 && t) {
      from[i] = { ...next, a: 0, stemA: 0, ring: 0, labelA: 0, stemY: next.stemY }
      if (t.enterFrom) { from[i].x = t.enterFrom[0]; from[i].y = t.enterFrom[1] }
    }
    return next
  })
  delays = new Float32Array(N)
  for (let i = 0; i < N; i++) delays[i] = Math.min(1, Math.max(0, to[i].x / 1920)) * 0.32 + ((i * 7919) % 97) / 97 * 0.08
  edges.fromIng = edges.ing; edges.fromCty = edges.cty
  edges.toIng = state.ingEdges; edges.toCty = state.ctyEdges
  specFrom = new Map([...specCur].map(([k, v]) => [k, { ...v }]))
  specTo = new Map((state.special ?? []).map(e => [`${e.from}-${e.to}`, { ...e }]))
  for (const [k, v] of specTo) if (!specFrom.has(k)) specFrom.set(k, { ...v, a: 0 })
  for (const [k, v] of specFrom) if (!specTo.has(k)) specTo.set(k, { ...v, a: 0 })
  land.value = state.land ?? 0
  if (state.landRect) { const k = state.landRect.w / MAP.w; landTf.value = `translate(${state.landRect.x - MAP.x * k}px, ${state.landRect.y - MAP.y * k}px) scale(${k})` }
  else if (state.land) landTf.value = 'none'
  tween?.kill()
  if (instant || reduced) { prog.p = 1; step(1); return }
  prog.p = 0
  tween = gsap.to(prog, { p: 1, duration: state.duration ?? 1.5, ease: 'none', onUpdate: () => step(prog.p) })
}

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)
const mix = (a: number, b: number, t: number) => a + (b - a) * t

function step(p: number) {
  for (let i = 0; i < N; i++) {
    const d = delays[i]
    const t = ease(Math.min(1, Math.max(0, (p - d) / (1 - 0.4))))
    const f = from[i], g = to[i], c = cur[i]
    c.x = mix(f.x, g.x, t); c.y = mix(f.y, g.y, t); c.r = mix(f.r, g.r, t)
    c.c = [mix(f.c[0], g.c[0], t), mix(f.c[1], g.c[1], t), mix(f.c[2], g.c[2], t)]
    const fast = Math.min(1, p * 3.2) // exits: no delay, quick
    const late = Math.max(0, (t - 0.72) / 0.28) // stems and rings: once the dot has arrived
    c.a = g.a < 0.01 ? mix(f.a, 0, fast) : mix(f.a, g.a, t)
    c.stemY = mix(f.stemY, g.stemY, t)
    c.stemA = g.stemA < f.stemA ? mix(f.stemA, g.stemA, fast) : mix(f.stemA, g.stemA, late)
    c.ring = g.ring < f.ring ? mix(f.ring, g.ring, fast) : mix(f.ring, g.ring, late)
    // labels: the old one leaves at once, the new one arrives with the dot
    const lt = Math.max(0, (t - 0.55) / 0.45)
    if (f.label === g.label && f.labelA > 0.01 && g.labelA > 0.01) { c.label = g.label; c.labelA = mix(f.labelA, g.labelA, t) }
    else {
      c.label = fast < 1 && f.labelA > 0.01 && lt === 0 ? f.label : g.label
      c.labelA = fast < 1 && f.labelA > 0.01 && lt === 0 ? f.labelA * (1 - fast) : g.labelA * lt
    }
    c.labelSize = g.labelSize; c.labelSide = g.labelSide; c.labelWeight = g.labelWeight; c.ldx = g.ldx; c.ldy = g.ldy; c.lat = t < 0.5 ? f.lat : g.lat
    c.hollow = t < 0.5 ? f.hollow : g.hollow; c.square = t < 0.5 ? f.square : g.square
  }
  const e = ease(Math.min(1, p * 1.2))
  const eIn = ease(Math.max(0, (p - 0.62) / 0.38)) // edges arrive once the dots have landed
  const eOut = Math.min(1, p * 3.2) // and leave at once
  edges.ing = mix(edges.fromIng, edges.toIng, edges.toIng > edges.fromIng ? eIn : eOut)
  edges.cty = mix(edges.fromCty, edges.toCty, edges.toCty > edges.fromCty ? eIn : eOut)
  const next = new Map<string, Spec>()
  for (const [k, g] of specTo) {
    const f = specFrom.get(k)!
    const a = mix(f.a, g.a, g.a < f.a ? eOut : g.a > f.a && f.a < 0.01 ? eIn : e)
    if (a > 0.003 || g.a > 0) next.set(k, { from: g.from, to: g.to, a, w: mix(f.w, g.w, e), c: [mix(f.c[0], g.c[0], e), mix(f.c[1], g.c[1], e), mix(f.c[2], g.c[2], e)] })
  }
  specCur = next
}

const rgba = (c: RGB, a: number) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`

function resize() {
  const el = canvas.value; if (!el) return
  const w = el.getBoundingClientRect().width || 1920
  const dpr = window.devicePixelRatio || 1
  const backing = Math.round(1920 * (w / 1920) * dpr)
  if (el.width !== backing) { el.width = backing; el.height = Math.round(backing * 1080 / 1920) }
  scale = el.width / 1920
  ctx = el.getContext('2d')
}

function draw(time: number) {
  raf = requestAnimationFrame(draw)
  if (!ctx || !canvas.value) return
  const el = canvas.value
  if (Math.abs(el.getBoundingClientRect().width * (window.devicePixelRatio || 1) - el.width) > 2) resize()
  ctx.setTransform(scale, 0, 0, scale, 0, 0)
  ctx.clearRect(0, 0, 1920, 1080)
  const drift = reduced ? 0 : (state?.drift ?? 0)
  const s = time / 1000
  const X = (i: number) => cur[i].x + drift * Math.sin(s * 0.55 + phase[i])
  const Y = (i: number) => cur[i].y + drift * Math.cos(s * 0.43 + phase[i] * 1.3)

  for (const [set, alpha] of [[ING_EDGES, edges.ing], [CTY_EDGES, edges.cty]] as const) {
    if (alpha < 0.005) continue
    ctx.beginPath()
    for (const [u, v] of set) {
      if (cur[u].a < 0.05 || cur[v].a < 0.05) continue
      ctx.moveTo(X(u), Y(u)); ctx.lineTo(X(v), Y(v))
    }
    ctx.strokeStyle = rgba(INK2, alpha); ctx.lineWidth = 1; ctx.stroke()
  }
  ctx.lineCap = 'round'
  for (const e of specCur.values()) {
    if (e.a < 0.005 || cur[e.from].a < 0.05 || cur[e.to].a < 0.05) continue
    ctx.beginPath(); ctx.moveTo(X(e.from), Y(e.from)); ctx.lineTo(X(e.to), Y(e.to))
    ctx.strokeStyle = rgba(e.c, e.a); ctx.lineWidth = e.w; ctx.stroke()
  }
  ctx.lineCap = 'butt'
  for (let i = 0; i < N; i++) {
    const c = cur[i]
    if (c.stemA < 0.01) continue
    ctx.beginPath(); ctx.moveTo(X(i), c.stemY); ctx.lineTo(X(i), Y(i))
    ctx.strokeStyle = rgba(c.c, c.stemA * 0.8); ctx.lineWidth = 1.4; ctx.stroke()
  }
  for (let i = 0; i < N; i++) {
    const c = cur[i]
    if (c.a < 0.01) continue
    ctx.beginPath()
    if (c.square) ctx.rect(X(i) - c.r, Y(i) - c.r, c.r * 2, c.r * 2)
    else ctx.arc(X(i), Y(i), Math.max(0.5, c.hollow ? c.r - 0.8 : c.r), 0, Math.PI * 2)
    if (c.hollow) { ctx.strokeStyle = rgba(c.c, c.a); ctx.lineWidth = 1.8; ctx.stroke() }
    else { ctx.fillStyle = rgba(c.c, c.a); ctx.fill() }
    if (c.ring > 0.01) {
      ctx.beginPath(); ctx.arc(X(i), Y(i), c.r + 7, 0, Math.PI * 2)
      ctx.strokeStyle = rgba([42, 32, 25], c.ring); ctx.lineWidth = 2.2; ctx.stroke()
    }
  }
  ctx.textBaseline = 'middle'
  for (let i = 0; i < N; i++) {
    const c = cur[i]
    if (c.labelA < 0.01 || !c.label) continue
    ctx.font = `${c.labelWeight} ${c.labelSize}px "Inter Variable", Inter, sans-serif`
    const off = c.r + 12
    let x = X(i) + c.ldx, y = Y(i) + c.ldy
    if (c.lat) { x = c.lat[0]; y = c.lat[1] }
    if (c.ldx || c.ldy || c.lat) { // leader line from the node to the label
      ctx.beginPath(); ctx.moveTo(X(i) + c.r + 3, Y(i)); ctx.lineTo(x + 2, y)
      ctx.strokeStyle = rgba([194, 65, 45], c.labelA * 0.7); ctx.lineWidth = 1.3; ctx.stroke()
    }
    ctx.textAlign = 'left'
    if (c.lat) { ctx.textAlign = c.labelSide === 'l' ? 'right' : 'left' }
    else if (c.labelSide === 'r') x += off
    else if (c.labelSide === 'l') { x -= off; ctx.textAlign = 'right' }
    else if (c.labelSide === 't') { y -= off + 4; ctx.textAlign = 'center' }
    else { y += off + 4; ctx.textAlign = 'center' }
    ctx.lineJoin = 'round'; ctx.lineWidth = 7; ctx.strokeStyle = rgba(PAPER, c.labelA)
    ctx.strokeText(c.label, x, y)
    ctx.fillStyle = rgba([42, 32, 25], c.labelA); ctx.fillText(c.label, x, y)
  }
}

onMounted(() => {
  resize()
  sub.value = 0
  apply(nav.currentPage.value, nav.clicks.value, true)
  schedule(nav.currentPage.value, nav.clicks.value)
  raf = requestAnimationFrame(draw)
  window.addEventListener('resize', resize)
  document.fonts?.ready.then(() => resize())
})
onBeforeUnmount(() => { cancelAnimationFrame(raf); tween?.kill(); window.removeEventListener('resize', resize) })
let timers: number[] = []
function schedule(page: number, click: number) {
  timers.forEach(t => clearTimeout(t)); timers = []
  const steps = pageInfo(page).timeline?.[click] ?? []
  const printing = nav.isPrintMode.value
  sub.value = printing ? steps.length : 0
  apply(page, click)
  if (printing) return
  steps.forEach((at, k) => timers.push(window.setTimeout(() => { sub.value = k + 1; apply(page, click) }, at * 1000)))
}
watch(() => [nav.currentPage.value, nav.clicks.value] as const, ([page, click]) => schedule(page, click))
</script>

<template>
  <svg class="world-land" viewBox="0 0 1920 1080" aria-hidden="true" :style="{ opacity: land, transform: landTf }"><path :d="landPath" /></svg>
  <canvas ref="canvas" class="world-canvas" aria-hidden="true" />
</template>

<style>
.world-canvas { position: absolute; inset: 0; width: 1920px; height: 1080px; pointer-events: none; z-index: 0; }
.world-land { position: absolute; inset: 0; width: 1920px; height: 1080px; pointer-events: none; z-index: 0;
  transition: opacity 1s ease, transform 1.2s cubic-bezier(.6,0,.2,1); transform-origin: 0 0; }
.world-land path { fill: #E7DDC9; stroke: #D3C5AC; stroke-width: .8; }
</style>
