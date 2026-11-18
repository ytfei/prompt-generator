import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Selections } from '../types'

interface SelectionsState {
  selections: Selections
  theme: string
  setOption: (groupId: string, label: string, multi: boolean) => void
  setTheme: (theme: string) => void
  applySelections: (s: Selections) => void
  reset: () => void
}

export const useSelections = create<SelectionsState>()(
  persist(
    (set, get) => ({
      selections: {},
      theme: '',
      setOption: (groupId, label, multi) => {
        const cur = get().selections
        if (multi) {
          const arr = Array.isArray(cur[groupId]) ? [...(cur[groupId] as string[])] : []
          const i = arr.indexOf(label)
          i >= 0 ? arr.splice(i, 1) : arr.push(label)
          set({ selections: { ...cur, [groupId]: arr } })
        } else if (cur[groupId] === label) {
          const next = { ...cur }
          delete next[groupId]
          set({ selections: next })
        } else {
          set({ selections: { ...cur, [groupId]: label } })
        }
      },
      setTheme: (theme) => set({ theme }),
      applySelections: (s) => set({ selections: s }),
      reset: () => set({ selections: {}, theme: '' }),
    }),
    { name: 'prompt-studio-v1' },
  ),
)
