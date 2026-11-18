/** 与后端 schema 对齐的类型定义 */

export interface OptionItem {
  label: string
  prompt: string
  ratio: string
}

export interface OptionGroup {
  name: string
  hint: string
  multi: boolean
  options: OptionItem[]
}

export interface Preset {
  key: string
  label: string
  selections: Record<string, string | string[]>
}

export interface OptionsResponse {
  groups: Record<string, OptionGroup>
  presets: Preset[]
}

export interface Note {
  rule: string
  message: string
  suggest_tone_prompt?: string
}

export interface GenerationItem {
  id: string
  created_at: string
  selections: Record<string, string | string[]>
  theme: string
  final_prompt: string
  notes: Note[]
  warnings: Note[]
  model: string
  mode: string
  favorite: boolean
}

export type Selections = Record<string, string | string[]>

/** SSE 事件 */
export interface StepEvent {
  node: string
  status: 'running' | 'done'
  index: number
}

export interface ResultEvent {
  id: string
  prompt: string
  notes: Note[]
  warnings: Note[]
  suggested_ratio: string
  model: string
}

export const NODE_LABELS: Record<string, string> = {
  parse_intent: '解析主题意图',
  enrich_details: '补全画面细节',
  conflict_check: '检查并修正维度冲突',
  assemble: '汇总组装提示词',
  refine: '润色输出最终结果',
}
