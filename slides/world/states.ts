// One target per node for each (slide, click). Slides call the world by name, not by number.
import { COMM, CTY, CTY_EDGES, ING, ING_EDGES, INK, INK2, NODES, PEN, type RGB, type Target, ing_ } from './model'

export interface WorldState {
  targets: (Target | null)[] // null = keep position, fade out
  ingEdges: number // alpha of the ingredient backbone
  ctyEdges: number
  land?: number // alpha of the map outlines
  landRect?: Rect // where the map outlines sit (default: MAP)
  edgeColor?: RGB
  drift?: number // idle motion amplitude in px
  special?: { from: number, to: number, a: number, w: number, c: RGB }[]
  duration?: number
}

export interface Rect { x: number, y: number, w: number, h: number }

const radius = (strength: number, k = 1) => (2.2 + Math.sqrt(strength) * 0.62) * k

function graphAt(rect: Rect, opts: { color?: (i: number) => RGB, alpha?: (i: number) => number, k?: number } = {}): (Target | null)[] {
  const t: (Target | null)[] = NODES.map(() => null)
  for (const i of ING) {
    const n = NODES[i]
    t[i] = {
      x: rect.x + n.gx * rect.w, y: rect.y + n.gy * rect.h, r: radius(n.strength, opts.k ?? 1),
      c: opts.color ? opts.color(i) : INK, a: opts.alpha ? opts.alpha(i) : 0.8,
    }
  }
  return t
}

// ---------------------------------------------------------------- slide states
const COVER_RECT: Rect = { x: 900, y: 150, w: 900, h: 760 }
export const HOME: Rect = { x: 920, y: 220, w: 880, h: 700 } // the graph's place on every graph slide
const GRAPH_RIGHT = HOME

function cover(): WorldState {
  return { targets: graphAt(COVER_RECT, { alpha: () => 0.42, k: 0.9 }), ingEdges: 0.08, ctyEdges: 0, drift: 2.2 }
}

// Frequency skyline: the 362 ingredients sorted by recipe count, as lollipops (square-root scale).
const FREQ_BASE = 920
const FREQ_LEFT = 150
const FREQ_W = 1620
const FREQ_H = 560
const SPOKEN = new Set(['Salt', 'Onion', 'Butter']) // the three named in the script
const NAMED = 7 // label the top seven, so Pepper and Garlic are not unexplained tall bars
function frequency(): WorldState {
  const t: (Target | null)[] = NODES.map(() => null)
  const sorted = [...ING].sort((a, b) => NODES[b].recipes - NODES[a].recipes)
  const max = NODES[sorted[0]].recipes
  sorted.forEach((i, rank) => {
    const n = NODES[i]
    const lit = SPOKEN.has(n.id)
    const named = rank < NAMED
    const x = FREQ_LEFT + Math.pow(rank / (sorted.length - 1), 0.82) * FREQ_W
    const y = FREQ_BASE - Math.sqrt(n.recipes / max) * FREQ_H
    const r = lit ? 7.5 : 3.4
    t[i] = {
      x, y, r, c: lit ? PEN : INK, a: lit ? 1 : 0.62, stemY: FREQ_BASE, stemA: lit ? 0.95 : 0.3,
      label: named ? `${n.id}  ${n.recipes.toLocaleString('en-US')}` : undefined, labelA: lit ? 1 : named ? 0.5 : 0,
      labelSize: lit ? 30 : 25, labelSide: 'r', labelWeight: lit ? 600 : 500,
      labelDX: named ? 330 - (r + 12) - x : 0, labelDY: named ? 340 + rank * 40 - y : 0,
    }
  })
  return { targets: t, ingEdges: 0, ctyEdges: 0 }
}

function questionGraph(): WorldState {
  return { targets: graphAt(GRAPH_RIGHT, { alpha: () => 0.78, k: 0.88 }), ingEdges: 0.13, ctyEdges: 0, drift: 1.5 }
}


// ---------------------------------------------------------------- slides 4 to 12
import extra from '../data/extra.json'
import { cty_, equalEarth } from './model'

function countryGraph(rect: Rect, color: (i: number) => RGB, alpha = 0.8): (Target | null)[] {
  const t: (Target | null)[] = NODES.map(() => null)
  for (const i of CTY) {
    const n = NODES[i]
    t[i] = { x: rect.x + n.gx * rect.w, y: rect.y + n.gy * rect.h, r: 2.6 + Math.sqrt(n.degree) * 0.75, c: color(i), a: alpha }
  }
  return t
}
const CTY_COLOR = (i: number): RGB => {
  const k = NODES[i].community
  return k <= 4 ? COMM[k] : k === 5 ? INK : INK2
}

function twoGraphs(click: number): WorldState {
  if (click < 1) return { targets: graphAt(HOME, { alpha: () => 0.85, k: 0.9 }), ingEdges: 0.16, ctyEdges: 0, drift: 1.2 }
  return { targets: countryGraph(HOME, () => INK, 0.85), ingEdges: 0, ctyEdges: 0.16, drift: 1.2 }
}

const CLUSTER_X = [300, 660, 990, 1270, 1560]
const CLUSTER_Y = 575
function communities(click: number): WorldState {
  if (click < 1) return { targets: graphAt(HOME, { alpha: () => 0.92, k: 0.9, color: i => COMM[NODES[i].community] }), ingEdges: 0.12, ctyEdges: 0, drift: 1.4 }
  const t: (Target | null)[] = NODES.map(() => null)
  for (let k = 0; k < 5; k++) {
    const members = ING.filter(i => NODES[i].community === k).sort((a, b) => NODES[b].strength - NODES[a].strength)
    const R = 12.5 * Math.sqrt(members.length)
    members.forEach((i, j) => {
      const rr = R * Math.sqrt((j + 0.5) / members.length)
      const th = j * 2.399963
      t[i] = { x: CLUSTER_X[k] + rr * Math.cos(th), y: CLUSTER_Y + rr * Math.sin(th), r: 2.4 + Math.sqrt(NODES[i].strength) * 0.5, c: COMM[k], a: 0.95 }
    })
  }
  return { targets: t, ingEdges: 0, ctyEdges: 0, drift: 0.8 }
}

const HOP5 = ['Water', 'Salt', 'Butter', 'Lemon', 'Cream']
function hopBrokers(click: number): WorldState {
  const t = graphAt(HOME, { alpha: () => (click >= 1 ? 0.3 : 0.75), k: 0.88, color: i => COMM[NODES[i].community] })
  if (click >= 1) {
    const at: Record<string, [[number, number], 'l' | 'r']> = {
      Water: [[1270, 637], 'l'], Lemon: [[1270, 531], 'l'], Butter: [[1470, 605], 'r'], Salt: [[1558, 676], 'r'], Cream: [[1499, 784], 'r'],
    }
    HOP5.forEach((id) => {
      const i = ing_(id); const g = t[i]!
      t[i] = { ...g, a: 1, r: g.r * 1.35 + 2, ring: 0.95, label: id, labelA: 1, labelSize: 30, labelWeight: 650, labelAt: at[id][0], labelSide: at[id][1] }
    })
  }
  return { targets: t, ingEdges: click >= 1 ? 0.07 : 0.12, ctyEdges: 0, drift: 1.2 }
}

const INV5 = ['Couscous', 'Lasagna', 'Shallot', 'Coconut', 'Saffron']
export const SCATTER = { x: 830, y: 205, w: 950, h: 690 }
function weighted(click: number): WorldState {
  const t: (Target | null)[] = NODES.map(() => null)
  const S = SCATTER
  for (const i of ING) {
    const n = NODES[i]
    const yr = click >= 1 ? n.rankInv1p : n.rankInv
    t[i] = { x: S.x + ((n.rankHop - 1) / 361) * S.w, y: S.y + ((yr - 1) / 361) * S.h, r: 4.2, c: COMM[n.community], a: 0.42 }
  }
  const at: Record<string, [number, number]> = {
    Shallot: [885, 268], Coconut: [965, 306], Saffron: [1065, 268], Couscous: [1235, 268], Lasagna: [1445, click >= 1 ? 340 : 306],
  }
  for (const id of [...INV5, 'Water', 'Salt']) {
    const i = ing_(id); const n = NODES[i]; const g = t[i]!
    let lab = id
    if (INV5.includes(id)) lab = click >= 1 ? (id === 'Lasagna' ? 'Lasagna  2 → 26' : `${id}  ${n.rankInv1p}`) : (id === 'Couscous' ? 'Couscous  175 → 1' : id)
    t[i] = { ...g, a: 1, r: 8, ring: id === 'Couscous' || (click >= 1 && id === 'Lasagna') ? 0.95 : 0,
      label: lab, labelA: 1, labelSize: 28, labelWeight: 650, labelSide: 'r', labelAt: at[id] }
  }
  return { targets: t, ingEdges: 0, ctyEdges: 0 }
}

export const MAP = (extra as any).map_rect as Rect
function mapXY(lon: number, lat: number, R: Rect = MAP): [number, number] {
  const xmax = equalEarth(170, 0)[0]; const ymax = equalEarth(10, 90)[1]
  const [x, y] = equalEarth(lon, lat)
  return [R.x + (x / xmax + 1) / 2 * R.w, R.y + (1 - (y / ymax + 1) / 2) * R.h]
}
function geography(): WorldState {
  const t: (Target | null)[] = NODES.map(() => null)
  for (const i of CTY) {
    const n = NODES[i]
    const [x, y] = mapXY(n.lon!, n.lat!)
    t[i] = { x, y, r: 7.5, c: CTY_COLOR(i), a: 0.95 }
  }
  return { targets: t, ingEdges: 0, ctyEdges: 0, land: 1 }
}

const LIT = ['Fiji', 'Uganda', 'Mauritius']
function connectors(): WorldState {
  const rect = { x: 840, y: 170, w: 960, h: 700 }
  const t = countryGraph(rect, CTY_COLOR, 0.42)
  for (const id of LIT) {
    const i = cty_(id); const g = t[i]!
    t[i] = { ...g, a: 1, r: g.r + 3, ring: 0.95, label: id, labelA: 1, labelSize: 30, labelWeight: 650, labelSide: id === 'Fiji' ? 'l' : 'r' }
  }
  for (const id of ['Tonga', 'Samoa']) {
    const i = cty_(id); const g = t[i]!
    t[i] = { ...g, a: 1, r: g.r + 1.5, label: id, labelA: 1, labelSize: 24, labelWeight: 600, labelSide: id === 'Samoa' ? 'b' : 't' }
  }
  const uganda = cty_('Uganda')
  const special = CTY_EDGES.filter(([u, v]) => u === uganda || v === uganda).map(([u, v]) => {
    const other = u === uganda ? v : u
    const outside = NODES[other].community !== NODES[uganda].community
    return { from: u, to: v, a: outside ? 0.75 : 0.35, w: 1.6, c: outside ? PEN : INK2 }
  })
  special.push({ from: cty_('Tonga'), to: cty_('Samoa'), a: 1, w: 3, c: INK })
  return { targets: t, ingEdges: 0, ctyEdges: 0.07, special }
}

function faint(): WorldState {
  return { targets: graphAt(HOME, { alpha: () => 0.22, k: 0.85, color: i => COMM[NODES[i].community] }), ingEdges: 0.05, ctyEdges: 0, drift: 2 }
}
const RECAP_MAP: Rect = { x: 1010, y: 360, w: 790, h: 790 * 711.8235765040789 / 1300 }
function answer(click: number): WorldState {
  if (click < 1) return faint()
  if (click === 1) { // the five communities, again
    const t: (Target | null)[] = NODES.map(() => null)
    const centres = [[1150, 400], [1440, 400], [1700, 420], [1290, 700], [1580, 710]]
    for (let k = 0; k < 5; k++) {
      const members = ING.filter(i => NODES[i].community === k).sort((a, b) => NODES[b].strength - NODES[a].strength)
      const R = 9.6 * Math.sqrt(members.length)
      members.forEach((i, j) => {
        const rr = R * Math.sqrt((j + 0.5) / members.length); const th = j * 2.399963
        t[i] = { x: centres[k][0] + rr * Math.cos(th), y: centres[k][1] + rr * Math.sin(th), r: 2 + Math.sqrt(NODES[i].strength) * 0.42, c: COMM[k], a: 0.95 }
      })
    }
    return { targets: t, ingEdges: 0, ctyEdges: 0, drift: 0.8 }
  }
  if (click === 2) { // two meanings of a step: Water and Couscous
    const t = graphAt(HOME, { alpha: () => 0.28, k: 0.88, color: i => COMM[NODES[i].community] })
    for (const [id, lab] of [['Water', 'Water · every step one hop'], ['Couscous', 'Couscous · step = 1/PMI']] as const) {
      const i = ing_(id); const g = t[i]!
      t[i] = { ...g, a: 1, r: 9, ring: 0.95, label: lab, labelA: 1, labelSize: 28, labelWeight: 650, labelSide: 'r' }
    }
    return { targets: t, ingEdges: 0.06, ctyEdges: 0, drift: 1 }
  }
  const t: (Target | null)[] = NODES.map(() => null) // the countries on the map
  for (const i of CTY) {
    const n = NODES[i]; const [x, y] = mapXY(n.lon!, n.lat!, RECAP_MAP)
    t[i] = { x, y, r: 5.5, c: CTY_COLOR(i), a: 0.95 }
  }
  return { targets: t, ingEdges: 0, ctyEdges: 0, land: 1, landRect: RECAP_MAP }
}

// ---------------------------------------------------------------- slide 3: recipes become a graph
import manimJson from '../data/manim.json'
import { RECIPES, rec_ } from './model'
const PROJ = (manimJson as any).projection
export const SHORT: Record<string, string> = { 'Soybean Sauce': 'Soy sauce', 'Pine': 'Pine nuts', 'Cooking Oil': 'Cooking oil' }
const COLUMN = ['Onion', 'Pepper', 'Vinegar', 'Ginger', 'Soybean Sauce', 'Sesame', 'Garlic', 'Beef', 'Sugar', 'Water', 'Cooking Oil', 'Lemon', 'Salt', 'Basil', 'Olive', 'Pine']
const WHEEL = ['Onion', 'Pepper', 'Vinegar', 'Ginger', 'Soybean Sauce', 'Sesame', 'Beef', 'Sugar', 'Water', 'Cooking Oil', 'Lemon', 'Salt', 'Basil', 'Olive', 'Pine']
export const FOCUS = ['Garlic-Salt', 'Ginger-Soybean Sauce']
function wheelPos(cx: number, cy: number, rx: number, ry: number): Record<string, [number, number, 'l' | 'r' | 't' | 'b']> {
  const out: Record<string, [number, number, 'l' | 'r' | 't' | 'b']> = { Garlic: [cx, cy, 'b'] }
  WHEEL.forEach((id, k) => {
    const th = -Math.PI / 2 + (2 * Math.PI * k) / WHEEL.length
    const x = cx + Math.cos(th) * rx, y = cy + Math.sin(th) * ry
    const side = Math.abs(Math.cos(th)) < 0.35 ? (Math.sin(th) < 0 ? 't' : 'b') : (Math.cos(th) < 0 ? 'l' : 'r')
    out[id] = [x, y, side]
  })
  return out
}
function projection(click: number, step: number): WorldState {
  const t: (Target | null)[] = NODES.map(() => null)
  const special: NonNullable<WorldState['special']> = []
  if (click < 1) return { targets: t, ingEdges: 0, ctyEdges: 0 }
  if (click === 1 && step < 1) { // bipartite: recipes on the left, their ingredients in a column
    RECIPES.forEach((r, k) => { t[rec_(r.title)] = { x: 470, y: 400 + k * 160, r: 11, c: INK, a: 1, square: true, label: r.title, labelA: 1, labelSize: 30, labelWeight: 600, labelSide: 'l', enterFrom: [140 + k * 416 + 110, 438] } })
    const from: Record<string, [number, number]> = {}
    RECIPES.forEach((r, k) => r.ingredients.forEach((id, j) => { from[id] ??= [140 + k * 416 + 34, 492.5 + 34.5 * j + 17] }))
    COLUMN.forEach((id, k) => { t[ing_(id)] = { x: 930, y: 365 + k * 37.5, r: 7, c: INK, a: 1, label: SHORT[id] ?? id, labelA: 1, labelSize: 25, labelWeight: 500, labelSide: 'r', enterFrom: from[id] } })
    RECIPES.forEach(r => r.ingredients.forEach(id => special.push({ from: rec_(r.title), to: ing_(id), a: 0.55, w: 1.4, c: INK2 })))
    return { targets: t, ingEdges: 0, ctyEdges: 0, special }
  }
  const W = click === 1 ? wheelPos(1280, 610, 300, 265) : wheelPos(560, 640, 270, 240)
  for (const id of COLUMN) {
    const [x, y, side] = W[id]
    t[ing_(id)] = { x, y, r: 8, c: INK, a: 1, label: SHORT[id] ?? id, labelA: 1, labelSize: 25, labelWeight: 500, labelSide: side }
  }
  for (const p of PROJ.pairs) {
    const key = [p.a, p.b].sort().join('-')
    const focus = FOCUS.includes(key)
    let w = 1.4 + 1.6 * (p.local - 1), a = 0.6, c = INK2
    if (click === 2) { w = 0.8 + 11 * p.cooc / 7571; a = focus ? 1 : 0.28; c = focus ? INK : INK2 }
    if (click >= 3) { if (!p.in_graph) a = 0; else { w = 0.8 + 3.4 * p.pmi; a = focus ? 1 : 0.32; c = focus ? PEN : INK2 } }
    special.push({ from: ing_(p.a), to: ing_(p.b), a, w, c })
  }
  return { targets: t, ingEdges: 0, ctyEdges: 0, special }
}

// ---------------------------------------------------------------- slide 9: the shuffle test
const SHUF = (manimJson as any).shuffle
export const TRAY = { left: 140, base: 600, step: 23, cols: 5, gap: 44 }
export const TRAYS = (() => {
  let x = TRAY.left
  return SHUF.real.groups.map((g: any) => {
    const w = Math.min(TRAY.cols, g.members.length) * TRAY.step
    const out = { x, w, majority: g.majority as string, size: g.members.length as number }
    x += w + TRAY.gap
    return out
  })
})() as { x: number, w: number, majority: string, size: number }[]
export function shuffleFrame(step: number) {
  if (step === 0 || step >= 10) return SHUF.real
  return SHUF.first_shuffles[Math.min(step, 8) - 1]
}
function shuffle(step: number): WorldState {
  const t: (Target | null)[] = NODES.map(() => null)
  const frame = shuffleFrame(step)
  frame.groups.forEach((g: any, k: number) => {
    const tray = TRAYS[k]
    g.members.forEach((m: any, j: number) => {
      const x = tray.x + (j % TRAY.cols) * TRAY.step + TRAY.step / 2
      const y = TRAY.base - Math.floor(j / TRAY.cols) * TRAY.step
      t[cty_(m.country)] = m.match ? { x, y, r: 8, c: INK, a: 0.95 } : { x, y, r: 8, c: INK2, a: 0.9, hollow: true }
    })
  })
  return { targets: t, ingEdges: 0, ctyEdges: 0, duration: step === 0 ? 1.6 : 0.7 }
}

const none = (): WorldState => ({ targets: NODES.map(() => null), ingEdges: 0, ctyEdges: 0 })

export function worldState(name: string, click: number, step = 0): WorldState {
  switch (name) {
    case 'cover': return cover()
    case 'question': return click >= 1 ? questionGraph() : frequency()
    case 'projection': return projection(click, step)
    case 'shuffle': return shuffle(click >= 2 ? 10 : click >= 1 ? step : 0)
    case 'two-graphs': return twoGraphs(click)
    case 'communities': return communities(click)
    case 'hop-brokers': return hopBrokers(click)
    case 'weighted': return weighted(click)
    case 'geography': return geography()
    case 'connectors': return connectors()
    case 'limits': return faint()
    case 'answer': return answer(click)
    default: return none()
  }
}

export { COMM, CTY, CTY_EDGES, ING_EDGES, INK2, ing_ }
