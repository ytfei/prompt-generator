import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createTemplate, getOptions, streamGeneration, streamRefine, submitFeedback } from '../api/client'
import type { GenerateHandlers } from '../api/client'
import ChipGroup from '../components/ChipGroup'
import ResultCard from '../components/ResultCard'
import StepStream from '../components/StepStream'
import { useSelections } from '../stores/selections'
import type { ResultEvent, StepState } from '../types'

type Phase = 'idle' | 'generating' | 'refining' | 'done' | 'error'

export default function Studio() {
  const { selections, theme, setTheme, applySelections, reset } = useSelections()
  const [phase, setPhase] = useState<Phase>('idle')
  const [steps, setSteps] = useState<StepState[]>([])
  const [result, setResult] = useState<ResultEvent | null>(null)
  const [error, setError] = useState('')
  const [tplName, setTplName] = useState('')
  const queryClient = useQueryClient()

  const { data: options, isLoading } = useQuery({ queryKey: ['options'], queryFn: getOptions })

  const saveTpl = useMutation({
    mutationFn: () => createTemplate(tplName.trim(), selections),
    onSuccess: () => {
      setTplName('')
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  const feedbackMut = useMutation({
    mutationFn: ({ id, rating }: { id: string; rating: 1 | -1 }) => submitFeedback(id, rating),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['generations'] }),
  })

  const setRatio = (ratio: string) => applySelections({ ...selections, ratio })

  const makeHandlers = (): GenerateHandlers => ({
    onStep: (ev) =>
      setSteps((prev) => [
        ...prev.filter((s) => s.node !== ev.node),
        { node: ev.node, status: ev.status },
      ]),
    onWarn: () => {},
    onResult: (ev) => {
      setResult(ev)
      setPhase('done')
    },
    onError: (msg) => {
      setError(msg)
      setPhase('error')
    },
  })

  const generate = async () => {
    setPhase('generating')
    setSteps([])
    setResult(null)
    setError('')
    try {
      await streamGeneration({ selections, theme }, makeHandlers())
    } catch (e) {
      setError(String(e))
      setPhase('error')
    }
  }

  const handleRefine = async (instruction: string) => {
    if (!result) return
    setPhase('refining')
    setSteps([])
    setError('')
    const baseId = result.id
    try {
      await streamRefine(baseId, instruction, makeHandlers())
    } catch (e) {
      setError(String(e))
      setPhase('error')
    } finally {
      queryClient.invalidateQueries({ queryKey: ['generations'] })
    }
  }

  if (isLoading) return <div className="page-loading">加载维度配置中…</div>
  if (!options) return <div className="page-loading">配置加载失败，请确认后端已启动</div>

  const busy = phase === 'generating' || phase === 'refining'

  return (
    <div className="layout">
      <div>
        <div className="presets">
          <span className="label">预设模板</span>
          {options.presets.map((p) => (
            <button key={p.key} className="preset-btn" onClick={() => applySelections(p.selections)}>
              {p.label}
            </button>
          ))}
          <button id="resetBtn" className="preset-btn" style={{ marginLeft: 'auto' }} onClick={reset}>
            ↺ 重置全部
          </button>
        </div>
        <div className="groups">
          {Object.entries(options.groups).map(([gid, group]) => (
            <ChipGroup key={gid} groupId={gid} group={group} onUsageSelect={(_, ratio) => setRatio(ratio)} />
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="card">
          <h2>
            主题描述 <span style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 400 }}>（可留空）</span>
          </h2>
          <textarea
            id="theme"
            placeholder="例如：一个年轻人在深夜的书房里写公众号文章，屏幕光映在脸上……"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          />
          <div className="row">
            <button className="primary" disabled={busy} onClick={generate}>
              {phase === 'generating' ? '生成中…' : '✨ 生成提示词'}
            </button>
          </div>
          <StepStream steps={steps} mode={phase === 'refining' || result?.parent_id ? 'refine' : 'generate'} />
          {phase === 'error' && <div className="note-item note-warn" style={{ marginTop: 8 }}>⚠ {error}</div>}
        </div>

        {result && (
          <div className="save-tpl">
            <input
              placeholder="保存当前配置为模板…"
              value={tplName}
              onChange={(e) => setTplName(e.target.value)}
            />
            <button disabled={!tplName.trim() || saveTpl.isPending} onClick={() => saveTpl.mutate()}>
              保存
            </button>
          </div>
        )}

        {result && (
          <ResultCard
            result={result}
            refining={phase === 'refining'}
            onRefine={handleRefine}
            onFeedback={(rating) => feedbackMut.mutate({ id: result.id, rating })}
          />
        )}
      </div>
    </div>
  )
}
