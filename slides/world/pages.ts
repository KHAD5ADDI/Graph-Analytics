// Page order: the world state and the speaker for each slide (1-based page numbers).
export const PAGES: { world: string, speaker: 'Khadidja' | 'Ewan' | 'Both', timeline?: Record<number, number[]> }[] = [
  { world: 'cover', speaker: 'Both' },
  { world: 'question', speaker: 'Khadidja' },
  { world: 'projection', speaker: 'Khadidja', timeline: { 1: [3.4] } },
  { world: 'two-graphs', speaker: 'Khadidja' },
  { world: 'communities', speaker: 'Khadidja' },
  { world: 'hop-brokers', speaker: 'Ewan' },
  { world: 'weighted', speaker: 'Ewan' },
  { world: 'geography', speaker: 'Ewan' },
  { world: 'shuffle', speaker: 'Ewan', timeline: { 1: [0.5, 1.4, 2.3, 3.2, 4.0, 4.8, 5.6, 6.4, 8.0] } },
  { world: 'connectors', speaker: 'Ewan' },
  { world: 'limits', speaker: 'Ewan' },
  { world: 'answer', speaker: 'Both' },
  { world: 'none', speaker: 'Both' }, // B1
  { world: 'none', speaker: 'Both' }, // B2
  { world: 'none', speaker: 'Both' }, // B3
]
export const MAIN_PAGES = 12

export function pageInfo(page: number) {
  return PAGES[page - 1] ?? { world: 'none', speaker: 'Both' }
}
