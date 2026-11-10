// Data model for the world: 362 ingredients + 171 countries, positions in 1920x1080 canvas px.
import ingData from '../data/ingredients_world.json'
import ctyData from '../data/countries_world.json'

export type RGB = [number, number, number]
export interface WNode {
  id: string
  kind: 'ing' | 'cty' | 'rec'
  gx: number // repo layout, 0..1
  gy: number
  community: number
  recipes: number
  strength: number
  rankHop: number
  rankInv: number
  rankInv1p: number
  region?: string
  lon?: number
  lat?: number
  degree: number
}

export interface Target {
  x: number
  y: number
  r: number
  c: RGB
  a: number
  stemY?: number // draw a stem from (x, stemY) to (x, y)
  stemA?: number
  ring?: number // ring alpha
  label?: string
  labelA?: number
  labelSize?: number
  labelSide?: 'r' | 'l' | 't' | 'b'
  labelWeight?: number
  labelDX?: number // label offset with a leader line
  labelDY?: number
  labelAt?: [number, number] // absolute label anchor, with a leader line
  hollow?: boolean
  square?: boolean
  enterFrom?: [number, number] // where an appearing node starts
}

export const hex = (h: string): RGB => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]

export const PAPER = hex('#F5EFE3')
export const INK = hex('#2A2019')
export const INK2 = hex('#75655A')
export const PEN = hex('#C2412D')
export const COMM = ['#2F5A2A', '#9B3F6B', '#E2704A', '#3B7F8C', '#D99A1A'].map(hex)

const ing = (ingData as any).nodes.map((n: any): WNode => ({
  id: n.id, kind: 'ing', gx: n.x, gy: n.y, community: n.community, recipes: n.n_recipes,
  strength: n.strength, rankHop: n.rank_hop, rankInv: n.rank_inv, rankInv1p: n.rank_inv1p, degree: n.degree,
}))
const cty = (ctyData as any).nodes.map((n: any): WNode => ({
  id: n.id, kind: 'cty', gx: n.x, gy: n.y, community: n.community, recipes: n.n_ingredients,
  strength: n.degree, rankHop: 0, rankInv: 0, rankInv1p: 0, region: n.region,
  lon: n.lonlat?.[0], lat: n.lonlat?.[1], degree: n.degree,
}))

import manimData from '../data/manim.json'
export const RECIPES = (manimData as any).projection.recipes as { title: string, cuisine: string, ingredients: string[] }[]
const rec = RECIPES.map((r): WNode => ({ id: r.title, kind: 'rec', gx: 0, gy: 0, community: 0, recipes: 0, strength: 0, rankHop: 0, rankInv: 0, rankInv1p: 0, degree: 0 }))
export const NODES: WNode[] = [...ing, ...cty, ...rec]
export const INDEX = new Map(NODES.map((n, i) => [n.kind + ':' + n.id, i]))
export const ING = NODES.map((n, i) => (n.kind === 'ing' ? i : -1)).filter(i => i >= 0)
export const CTY = NODES.map((n, i) => (n.kind === 'cty' ? i : -1)).filter(i => i >= 0)
export const ing_ = (id: string) => INDEX.get('ing:' + id)!
export const cty_ = (id: string) => INDEX.get('cty:' + id)!
export const rec_ = (id: string) => INDEX.get('rec:' + id)!

export const ING_EDGES: [number, number, number][] = (ingData as any).edges.map((e: any) => [ing_(e.u), ing_(e.v), e.pmi])
export const CTY_EDGES: [number, number, number][] = (ctyData as any).edges.map((e: any) => [cty_(e.u), cty_(e.v), e.jaccard])

// Equal Earth projection, to place countries geographically
export function equalEarth(lon: number, lat: number): [number, number] {
  const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2
  const l = ((((lon - 10) % 360) + 540) % 360 - 180) * Math.PI / 180 // centred at 10°E
  const p = lat * Math.PI / 180
  const t = Math.asin(M * Math.sin(p)); const t2 = t * t; const t6 = t2 * t2 * t2
  const x = l * Math.cos(t) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
  const y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
  return [x, y]
}
