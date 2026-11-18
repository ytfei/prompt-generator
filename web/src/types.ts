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
  category?: string
  /** 场景类预设自带的主题提示语，应用模板时填入主题描述 */
  theme_hint?: string
  selections: Record<string, string | string[]>
}

export interface ModelTier {
  id: 'default' | 'nano' | 'mid' | 'pro'
  label: string
  configured: boolean
}

export interface OptionsResponse {
  groups: Record<string, OptionGroup>
  presets: Preset[]
  models: { llm_enabled: boolean; tiers: ModelTier[] }
  i2i: I2IOptions
}

/** 图生图配置（PRD v0.2 M8/M9），由 /api/options 下发 */
export interface I2IOptions {
  scenes: I2IScene[]
  dirs: I2IDir[]
  templates: I2ITemplate[]
}

export interface I2IScene {
  id: 'creative' | 'modify' | 'style'
  label: string
  desc: string
  output: 'multi' | 'single'
}

export interface I2IDir {
  label: string
  tip: string
}

export interface I2ITemplate {
  id: string
  name: string
  use: string
  text: string
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
  tags: string[]
  note: string
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

/** 图生图 SSE result 事件：creative 场景 prompts 为 3 条，其余 1 条 */
export interface I2IResultEvent {
  id: string
  prompts: I2IPromptCard[]
  prompt: string
  notes: Note[]
  warnings: Note[]
  suggested_ratio: string
  model: string
}

export interface I2IPromptCard {
  direction: string
  note: string
  prompt: string
}

export const NODE_LABELS: Record<string, string> = {
  parse_intent: '解析主题意图',
  enrich_details: '补全画面细节',
  conflict_check: '检查并修正维度冲突',
  assemble: '汇总组装提示词',
  refine: '润色输出最终结果',
  apply_instruction: '应用修改要求',
  conflict_scan: '冲突扫描',
  understand_image: '理解原图内容',
  align_intent: '对齐修改/创意意图',
  fusion_check: '检查冲突与融合质量',
  compose: '输出提示词',
}

export const GENERATE_NODE_ORDER = [
  'parse_intent',
  'enrich_details',
  'conflict_check',
  'assemble',
  'refine',
]

export const REFINE_NODE_ORDER = ['apply_instruction', 'conflict_scan']

export const I2I_NODE_ORDER = ['understand_image', 'align_intent', 'fusion_check', 'compose']
