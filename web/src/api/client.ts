import type {
  GenerationItem,
  OptionsResponse,
  ResultEvent,
  Selections,
  StepEvent,
  TemplateInfo,
} from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!resp.ok) throw new Error(`${init?.method ?? 'GET'} ${path} → ${resp.status}`)
  return resp.json()
}

export const getOptions = () => request<OptionsResponse>('/api/options')

export const listGenerations = (params?: { favorite?: boolean }) => {
  const qs = params?.favorite !== undefined ? `?favorite=${params.favorite}` : ''
  return request<GenerationItem[]>(`/api/generations${qs}`)
}

export const toggleFavorite = (id: string, favorite: boolean) =>
  request<GenerationItem>(`/api/generations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ favorite }),
  })

export const deleteGeneration = (id: string) =>
  request<{ ok: boolean }>(`/api/generations/${id}`, { method: 'DELETE' })

export const submitFeedback = (id: string, rating: 1 | -1) =>
  request<{ ok: boolean; rating: number }>(`/api/generations/${id}/feedback`, {
    method: 'POST',
    body: JSON.stringify({ rating }),
  })

export const inspireTheme = (selections: Selections, modelTier: string = 'default') =>
  request<{ themes: string[] }>('/api/inspire-theme', {
    method: 'POST',
    body: JSON.stringify({ selections, model_tier: modelTier }),
  })

export const listTemplates = () => request<TemplateInfo[]>('/api/templates')

export const createTemplate = (name: string, selections: Selections) =>
  request<{ id: string }>('/api/templates', {
    method: 'POST',
    body: JSON.stringify({ name, selections }),
  })

export const deleteTemplate = (id: string) =>
  request<{ ok: boolean }>(`/api/templates/${id}`, { method: 'DELETE' })

export interface GenerateHandlers {
  onStep: (ev: StepEvent) => void
  onWarn: (ev: { rule: string; message: string }) => void
  onResult: (ev: ResultEvent) => void
  onError: (message: string) => void
}

/** 手动解析 SSE 流（EventSource 不支持 POST），生成与迭代共用。 */
async function consumeSSE(resp: Response, handlers: GenerateHandlers): Promise<void> {
  if (!resp.ok || !resp.body) throw new Error(`请求失败：${resp.status}`)
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''
    for (const block of blocks) {
      let event = ''
      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7)
        else if (line.startsWith('data: ')) data = line.slice(6)
      }
      if (!event || !data) continue
      const parsed = JSON.parse(data)
      if (event === 'step') handlers.onStep(parsed)
      else if (event === 'warn') handlers.onWarn(parsed)
      else if (event === 'result') handlers.onResult(parsed)
      else if (event === 'error') handlers.onError(parsed.message)
    }
  }
}

/** 生成：POST /api/generations */
export async function streamGeneration(
  payload: { selections: Selections; theme: string; mode?: string; model_tier?: string },
  handlers: GenerateHandlers,
): Promise<void> {
  const resp = await fetch('/api/generations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      mode: payload.mode ?? 'standard',
      model_tier: payload.model_tier ?? 'default',
    }),
  })
  await consumeSSE(resp, handlers)
}

/** 多轮迭代：基于某条结果按指令继续修改 */
export async function streamRefine(
  id: string,
  instruction: string,
  handlers: GenerateHandlers,
  modelTier: string = 'default',
): Promise<void> {
  const resp = await fetch(`/api/generations/${id}/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruction, model_tier: modelTier }),
  })
  await consumeSSE(resp, handlers)
}
