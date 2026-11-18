import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/** 图生图页状态（PRD v0.2），独立于文生图的 selections 持久化。 */
interface I2IState {
  scene: 'creative' | 'modify' | 'style'
  desc: string
  direction: string
  style: string
  modify: string
  template: string
  ratio: string
  setScene: (scene: I2IState['scene']) => void
  patch: (partial: Partial<Omit<I2IState, 'setScene' | 'patch'>>) => void
  reset: () => void
}

export const useI2I = create<I2IState>()(
  persist(
    (set) => ({
      scene: 'modify',
      desc: '',
      direction: '',
      style: '',
      modify: '',
      template: '',
      ratio: '',
      setScene: (scene) => set({ scene }), // 切场景时保留描述与意向
      patch: (partial) => set(partial),
      reset: () =>
        set({ scene: 'modify', desc: '', direction: '', style: '', modify: '', template: '', ratio: '' }),
    }),
    { name: 'prompt-studio-i2i-v1' },
  ),
)
