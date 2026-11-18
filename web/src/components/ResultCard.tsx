import { useState } from 'react'
import type { ResultEvent } from '../types'

export default function ResultCard({ result }: { result: ResultEvent }) {
  const [copied, setCopied] = useState(false)

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
      <h2>最终提示词</h2>
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
    </div>
  )
}
