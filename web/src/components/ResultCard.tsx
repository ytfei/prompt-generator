import { useState } from 'react'
import type { ResultEvent } from '../types'

interface Props {
  result: ResultEvent
  refining: boolean
  onRefine: (instruction: string) => void
  onFeedback: (rating: 1 | -1) => void
}

export default function ResultCard({ result, refining, onRefine, onFeedback }: Props) {
  const [copied, setCopied] = useState(false)
  const [instruction, setInstruction] = useState('')
  const [rating, setRating] = useState<1 | -1 | null>(null)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(result.prompt)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = result.prompt
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className="card">
      <h2>
        最终提示词
        {result.parent_id && (
          <span className="mode-badge">基于上一条迭代</span>
        )}
      </h2>
      <div className="result-text">{result.prompt}</div>
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
      <div className="copy-row">
        <button className={`copy-btn${copied ? ' ok' : ''}`} onClick={copy}>
          {copied ? '✓ 已复制' : '复制'}
        </button>
        {result.suggested_ratio && (
          <span className="ratio-badge">建议画幅：{result.suggested_ratio}</span>
        )}
        <span className="ratio-badge">模型：{result.model}</span>
      </div>

      <div className="refine-row">
        <input
          placeholder="基于这条继续改，如：更亮一点 / 换成居中构图…"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && instruction.trim() && !refining) onRefine(instruction.trim())
          }}
        />
        <button
          disabled={!instruction.trim() || refining}
          onClick={() => onRefine(instruction.trim())}
        >
          {refining ? '修改中…' : '继续修改'}
        </button>
      </div>

      <div className="feedback-row">
        <span>出图效果（在即梦生图后回来标记）：</span>
        <button
          className={`mini-btn${rating === 1 ? ' good' : ''}`}
          onClick={() => {
            setRating(1)
            onFeedback(1)
          }}
        >
          👍 好
        </button>
        <button
          className={`mini-btn${rating === -1 ? ' bad' : ''}`}
          onClick={() => {
            setRating(-1)
            onFeedback(-1)
          }}
        >
          👎 差
        </button>
      </div>
    </div>
  )
}
