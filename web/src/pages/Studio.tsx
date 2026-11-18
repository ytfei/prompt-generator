import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createTemplate, getOptions, inspireTheme, streamGeneration, streamRefine, submitFeedback } from '../api/client'
import type { GenerateHandlers } from '../api/client'
import ChipGroup from '../components/ChipGroup'
import ResultCard from '../components/ResultCard'
import StepStream from '../components/StepStream'
import { useSelections } from '../stores/selections'
import type { ResultEvent, StepState } from '../types'

type Phase = 'idle' | 'generating' | 'refining' | 'done' | 'error'

export default function Studio() {
  const { selections, theme, setTheme, applySelections, patchSelections, reset } = useSelections()
  const [phase, setPhase] = useState<Phase>('idle')
  const [steps, setSteps] = useState<StepState[]>([])
  const [result, setResult] = useState<ResultEvent | null>(null)
  const [error, setError] = useState('')
  const [tplName, setTplName] = useState('')
  const [themeOptions, setThemeOptions] = useState<string[] | null>(null)
  const [themesOpen, setThemesOpen] = useState(false)
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

  const inspireMut = useMutation({
    mutationFn: () => inspireTheme(selections),
    onSuccess: (d) => {
      setThemeOptions(d.themes)
      setThemesOpen(true)
    },
  })

  const toggleInspire = () => {
    if (!themeOptions) {
      inspireMut.mutate()
    } else {
      setThemesOpen(!themesOpen) // 已有候选：折叠/展开，不重新生成
    }
  }

  const setRatio = (ratio: string) => patchSelections({ ratio })

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

  // 预设按分类分组（保持后端返回顺序）
  const presetGroups: { name: string; presets: typeof options.presets }[] = []
  for (const p of options.presets) {
    const name = p.category || '通用'
    let g = presetGroups.find((x) => x.name === name)
    if (!g) {
      g = { name, presets: [] }
      presetGroups.push(g)
    }
    g.presets.push(p)
  }

  const applyPreset = (p: (typeof options.presets)[number]) => {
    applySelections(p.selections)
    if (p.theme_hint) setTheme(p.theme_hint)
  }

  return (
    <div className="layout">
      <aside className="tpl-sidebar">
        {presetGroups.map((g) => (
          <div key={g.name} className="tpl-cat">
            <div className="tpl-cat-name">{g.name}</div>
            {g.presets.map((p) => (
              <button key={p.key} className="tpl-item" onClick={() => applyPreset(p)} title={p.theme_hint || ''}>
                {p.label}
              </button>
            ))}
          </div>
        ))}
        <button className="tpl-item reset" onClick={reset}>↺ 重置全部</button>
      </aside>

      <div className="groups-col">
        <div className="groups">
          {Object.entries(options.groups).map(([gid, group]) => (
            <ChipGroup key={gid} groupId={gid} group={group} onUsageSelect={(_, ratio) => setRatio(ratio)} />
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="card">
          <div className="theme-head">
            <h2>
              主题描述 <span style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 400 }}>（可留空）</span>
            </h2>
            <button
              className="mini-btn inspire-btn"
              disabled={inspireMut.isPending || busy}
              onClick={toggleInspire}
              title={themeOptions ? '展开/收起灵感候选' : '基于已选配置生成创意主题'}
            >
              {inspireMut.isPending
                ? '灵感迸发中…'
                : themeOptions
                  ? themesOpen
                    ? '🎲 收起灵感'
                    : `🎲 展开灵感 (${themeOptions.length})`
                  : '🎲 随机灵感'}
            </button>
          </div>
          <textarea
            id="theme"
            placeholder="例如：一个年轻人在深夜的书房里写公众号文章，屏幕光映在脸上……"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          />
          {themeOptions && !themesOpen && (
            <div
              className="inspire-entry"
              onClick={() => setThemesOpen(true)}
            >
              有 {themeOptions.length} 条灵感候选，点击展开选择 →
            </div>
          )}
          {themeOptions && themesOpen && (
            <div className="inspire-list">
              <div className="inspire-tip">
                基于当前配置的灵感候选，点击选用：
                <span>
                  <button
                    className="mini-btn"
                    disabled={inspireMut.isPending}
                    onClick={() => inspireMut.mutate()}
                  >
                    {inspireMut.isPending ? '生成中…' : '换一批'}
                  </button>
                  <button className="mini-btn" onClick={() => setThemesOpen(false)}>收起</button>
                </span>
              </div>
              {themeOptions.map((t, i) => (
                <div
                  key={i}
                  className="inspire-item"
                  onClick={() => {
                    setTheme(t)
                    setThemesOpen(false) // 保留候选，可再次展开换选
                  }}
                >
                  {t}
                </div>
              ))}
            </div>
          )}
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
