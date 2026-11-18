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
  parent_id: string | null
  rating: number | null
}

export interface TemplateInfo {
  id: string
  name: string
  selections: Selections
  created_at: string
}

export type Selections = Record<string, string | string[]>

export interface StepState {
  node: string
  status: 'running' | 'done'
}

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
  parent_id?: string
}

export const NODE_LABELS: Record<string, string> = {
  parse_intent: '解析主题意图',
  enrich_details: '补全画面细节',
  conflict_check: '检查并修正维度冲突',
  assemble: '汇总组装提示词',
  refine: '润色输出最终结果',
  apply_instruction: '应用修改要求',
  conflict_scan: '冲突扫描',
}

export const GENERATE_NODE_ORDER = [
  'parse_intent',
  'enrich_details',
  'conflict_check',
  'assemble',
  'refine',
]

export const REFINE_NODE_ORDER = ['apply_instruction', 'conflict_scan']
