import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { getOptions, streamI2I, streamRefine, submitFeedback, toggleFavorite } from '../api/client'
import type { GenerateHandlers } from '../api/client'
import ResultCard from '../components/ResultCard'
import StepStream from '../components/StepStream'
import { useI2I } from '../stores/i2i'
import type { I2IResultEvent, ResultEvent, StepState } from '../types'

type Phase = 'idle' | 'generating' | 'refining' | 'done' | 'error'

/** 单条提示词结果 → 复用文生图结果卡（复制/继续修改/收藏/出图反馈） */
function toResultEvent(r: I2IResultEvent): ResultEvent {
  return {
    id: r.id,
    prompt: r.prompt,
    notes: r.notes,
    warnings: r.warnings,
    suggested_ratio: r.suggested_ratio,
    model: r.model,
  }
}

export default function Img2Img() {
  const { data: options, isLoading } = useQuery({ queryKey: ['options'], queryFn: getOptions })
  const { scene, desc, direction, style, modify, template, ratio, setScene, patch } = useI2I()
  const [phase, setPhase] = useState<Phase>('idle')
  const [steps, setSteps] = useState<StepState[]>([])
  const [result, setResult] = useState<I2IResultEvent | null>(null)
  const [error, setError] = useState('')
  const [descErr, setDescErr] = useState(false)
  const [resultFavorite, setResultFavorite] = useState(false)
  const [modelTier, setModelTier] = useState('default')
  const queryClient = useQueryClient()

  const feedbackMut = useMutation({
    mutationFn: ({ id, rating }: { id: string; rating: 1 | -1 }) => submitFeedback(id, rating),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['generations'] }),
  })

  const resultFavMut = useMutation({
    mutationFn: () => toggleFavorite(result!.id, !resultFavorite),
    onSuccess: (d) => setResultFavorite(d.favorite),
  })

  const makeHandlers = (): GenerateHandlers => ({
    onStep: (ev) =>
      setSteps((prev) => [
        ...prev.filter((s) => s.node !== ev.node),
        { node: ev.node, status: ev.status },
      ]),
    onWarn: () => {},
    onResult: (ev) => {
      // 图生图 result 事件多带 prompts 数组，兼容文生图事件结构
      setResult(ev as unknown as I2IResultEvent)
      setResultFavorite(false)
      setPhase('done')
    },
    onError: (msg) => {
      setError(msg)
      setPhase('error')
    },
  })

  const generate = async () => {
    if (!desc.trim()) {
      setDescErr(true)
      return
    }
    setPhase('generating')
    setSteps([])
    setResult(null)
    setError('')
    try {
      await streamI2I(
        { desc: desc.trim(), scene, direction, style, modify, ratio, template, model_tier: modelTier },
        makeHandlers(),
      )
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
    try {
      await streamRefine(result.id, instruction, makeHandlers())
    } catch (e) {
      setError(String(e))
      setPhase('error')
    } finally {
      queryClient.invalidateQueries({ queryKey: ['generations'] })
    }
  }

  if (isLoading) return <div className="page-loading">加载配置中…</div>
  if (!options) return <div className="page-loading">配置加载失败，请确认后端已启动</div>

  const busy = phase === 'generating' || phase === 'refining'
  const multi = (result?.prompts.length ?? 0) > 1

  const pickTemplate = (id: string, text: string) => {
    if (template === id) {
      patch({ template: '' }) // 再点取消：保留已填文字，仅解除模板态
    } else {
      patch({ template: id, modify: text })
    }
  }

  return (
    <div className="layout i2i-layout">
      {/* 左列：场景 + 图片描述 + 场景动态区 */}
      <div style={{ gridArea: 'groups' }}>
        <div className="group" style={{ marginBottom: 14 }}>
          <h3>
            🧭 选择场景
            <span className="state on">{options.i2i.scenes.find((s) => s.id === scene)?.label}</span>
          </h3>
          <div className="hint">场景决定要填什么、Agent 怎么生成</div>
          <div className="chips">
            {options.i2i.scenes.map((s) => (
              <span
                key={s.id}
                className={`chip${scene === s.id ? ' on' : ''}`}
                title={s.desc}
                onClick={() => {
                  setScene(s.id)
                  // 模板与扩图画幅是精准修改专属，切走时清掉，避免残留状态影响其他场景
                  if (s.id !== 'modify' && (template || ratio)) patch({ template: '', ratio: '' })
                }}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>

        <div className="group" style={{ marginBottom: 14 }}>
          <h3>
            📷 图片内容描述
            <span className={`state${desc.trim() ? ' on' : ''}`}>
              {desc.trim() ? `已填 ${desc.trim().length} 字` : '未填写'}
            </span>
          </h3>
          <div className="hint">
            必填。说清"图片中有什么"即可，不必精确到构图细节。无需上传图片。
          </div>
          <textarea
            className={`i2i-ta${descErr ? ' err' : ''}`}
            style={{ minHeight: 80 }}
            placeholder="例如：一只橘猫趴在窗台上晒太阳，窗外是城市街景"
            value={desc}
            onChange={(e) => {
              patch({ desc: e.target.value })
              setDescErr(false)
            }}
          />
          {descErr && <div className="ta-err">请先描述图片内容，图生图需要参照原图信息</div>}
        </div>

        {scene === 'creative' && (
          <div className="group" style={{ marginBottom: 14 }}>
            <h3>
              🧩 创意方向
              <span className={`state${direction ? ' on' : ''}`}>{direction || '自由脑洞'}</span>
            </h3>
            <div className="hint">可不选，默认「自由脑洞」混合发散</div>
            <div className="chips">
              {options.i2i.dirs.map((d) => (
                <span
                  key={d.label}
                  className={`chip${direction === d.label ? ' on' : ''}`}
                  title={d.tip}
                  onClick={() => patch({ direction: direction === d.label ? '' : d.label })}
                >
                  {d.label}
                </span>
              ))}
            </div>
          </div>
        )}

        {scene === 'style' && (
          <div className="group" style={{ marginBottom: 14 }}>
            <h3>
              🎨 目标风格
              <span className={`state${style ? ' on' : ''}`}>{style || 'Agent 自判'}</span>
            </h3>
            <div className="hint">与文生图共用风格库；不选则由 Agent 依原图判断最合适的风格</div>
            <div className="chips">
              {options.groups.style.options.map((s) => (
                <span
                  key={s.label}
                  className={`chip${style === s.label ? ' on' : ''}`}
                  title={s.prompt}
                  onClick={() => patch({ style: style === s.label ? '' : s.label })}
                >
                  {s.label}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 通用：修改意向（三个场景均可填，留空自由发挥）；模板仅精准修改场景 */}
        <div className="group">
          {scene === 'modify' && (
            <>
              <h3>
                🛠 常用修改模板
                <span className={`state${template ? ' on' : ''}`}>
                  {options.i2i.templates.find((t) => t.id === template)?.name ?? '未使用'}
                </span>
              </h3>
              <div className="hint">点模板一键填充修改意向，可再手动编辑；再点一次解除模板态</div>
              <div className="tpl-grid">
                {options.i2i.templates.map((t) => (
                  <button
                    key={t.id}
                    className={`tpl-btn${template === t.id ? ' on' : ''}`}
                    onClick={() => pickTemplate(t.id, t.text)}
                  >
                    {t.name}
                    <span className="t-use">{t.use}</span>
                  </button>
                ))}
              </div>
            </>
          )}
          <h3 style={{ marginTop: scene === 'modify' ? 4 : 0 }}>
            ✍️ 修改意向
            <span className={`state${modify.trim() ? ' on' : ''}`}>
              {modify.trim() ? '已填' : '自由发挥'}
            </span>
          </h3>
          <div className="hint">
            选填，三个场景通用。填写后生成时参考；留空则由 Agent 自由发挥
            {scene === 'modify' && '（精准修改场景留空会生成通用画质增强）'}
          </div>
          <textarea
            className="i2i-ta"
            style={{ minHeight: 72 }}
            placeholder={
              scene === 'modify'
                ? '例如：把背景换成黄昏的海边，主体保持不变'
                : '例如：整体色调偏暖一些，画面里加一点绿植（留空则自由发挥）'
            }
            value={modify}
            onChange={(e) => patch({ modify: e.target.value })}
          />
          {template === 'outpaint' && (
            <div style={{ marginTop: 12 }}>
              <div className="hint" style={{ marginBottom: 6 }}>
                目标画幅（扩图需指定，默认按公众号首图 2.35:1）
              </div>
              <div className="chips">
                {options.groups.ratio.options.map((r) => (
                  <span
                    key={r.label}
                    className={`chip${ratio === r.label ? ' on' : ''}`}
                    onClick={() => patch({ ratio: ratio === r.label ? '' : r.label })}
                  >
                    {r.label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 右列：生成 + 结果 */}
      <div className="panel" style={{ gridArea: 'panel' }}>
        <div className="card">
          <h2>图生图提示词</h2>
          <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 4 }}>
            生成后到即梦：<b>上传原图 → 粘贴提示词</b>
          </div>
          <div className="row">
            {options.models.llm_enabled && options.models.tiers.length > 1 && (
              <select
                className="tier-select"
                value={modelTier}
                onChange={(e) => setModelTier(e.target.value)}
                title="选择生成所用模型档位"
              >
                {options.models.tiers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
            )}
            <button className="primary" disabled={busy} onClick={generate}>
              {phase === 'generating' ? '生成中…' : '✨ 生成提示词'}
            </button>
          </div>
          <StepStream steps={steps} mode="i2i" />
          {phase === 'error' && (
            <div className="note-item note-warn" style={{ marginTop: 8 }}>
              ⚠ {error}
            </div>
          )}
        </div>

        {result && multi && (
          <div className="card">
            <div className="result-head">
              <h2>创意提示词（{result.prompts.length} 条）</h2>
            </div>
            {result.prompts.map((p, i) => (
              <MultiPromptCard key={i} label={`方向${'一二三'[i] ?? i + 1}`} sub={p.note} text={p.prompt} />
            ))}
            {result.warnings.length > 0 && (
              <div className="notes">
                {result.warnings.map((w, i) => (
                  <div key={i} className="note-item note-warn">
                    ⚠ {w.message}
                  </div>
                ))}
              </div>
            )}
            {result.notes.length > 0 && (
              <div className="notes">
                {result.notes.map((n, i) => (
                  <div key={i} className="note-item">
                    {n.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {result && !multi && (
          <ResultCard
            result={toResultEvent(result)}
            refining={phase === 'refining'}
            favorited={resultFavorite}
            onRefine={handleRefine}
            onFeedback={(rating) => feedbackMut.mutate({ id: result.id, rating })}
            onFavorite={() => resultFavMut.mutate()}
          />
        )}
      </div>
    </div>
  )
}

/** 创意灵感场景的多条结果卡：每条可独立复制 */
function MultiPromptCard({ label, sub, text }: { label: string; sub: string; text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }
  return (
    <div className="result-card">
      <div className="card-label">
        {label}
        <span>{sub}</span>
      </div>
      <div className="result-text">{text}</div>
      <div className="copy-row">
        <button className={`copy-btn${copied ? ' ok' : ''}`} onClick={copy}>
          {copied ? '✓ 已复制' : '复制'}
        </button>
      </div>
    </div>
  )
}
