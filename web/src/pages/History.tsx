import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { deleteGeneration, listGenerations, submitFeedback, toggleFavorite } from '../api/client'
import type { GenerationItem } from '../types'

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      className="mini-btn"
      onClick={async () => {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 1500)
      }}
    >
      {copied ? '✓ 已复制' : '复制'}
    </button>
  )
}

export default function History() {
  const qc = useQueryClient()
  const [onlyFav, setOnlyFav] = useState(false)
  const { data: items, isLoading } = useQuery({
    queryKey: ['generations', onlyFav],
    queryFn: () => listGenerations(onlyFav ? { favorite: true } : undefined),
  })

  const favMut = useMutation({
    mutationFn: ({ id, favorite }: { id: string; favorite: boolean }) => toggleFavorite(id, favorite),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['generations'] }),
  })
  const delMut = useMutation({
    mutationFn: (id: string) => deleteGeneration(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['generations'] }),
  })
  const fbMut = useMutation({
    mutationFn: ({ id, rating }: { id: string; rating: 1 | -1 }) => submitFeedback(id, rating),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['generations'] }),
  })

  const renderRating = (it: GenerationItem) =>
    it.rating === 1 ? <span className="rating-badge good">👍</span> : it.rating === -1 ? <span className="rating-badge bad">👎</span> : null

  if (isLoading) return <div className="page-loading">加载历史中…</div>

  return (
    <div className="history-page">
      <div className="presets">
        <button className={`preset-btn${onlyFav ? ' active-fav' : ''}`} onClick={() => setOnlyFav(!onlyFav)}>
          {onlyFav ? '★ 只看收藏' : '☆ 只看收藏'}
        </button>
      </div>
      {(items ?? []).length === 0 && <div className="page-loading">暂无生成记录，去工作台生成第一条吧</div>}
      {(items ?? []).map((it: GenerationItem) => (
        <div key={it.id} className="history-item">
          <div className="history-meta">
            <span>{new Date(it.created_at).toLocaleString('zh-CN')}</span>
            <span>·</span>
            <span>{it.model}</span>
            {it.theme && (
              <>
                <span>·</span>
                <span className="history-theme">{it.theme}</span>
              </>
            )}
            {it.mode === 'refine' && <span className="mode-badge">迭代</span>}
            {renderRating(it)}
            <span style={{ flex: 1 }} />
            <button className="mini-btn" onClick={() => fbMut.mutate({ id: it.id, rating: 1 })}>
              👍
            </button>
            <button className="mini-btn" onClick={() => fbMut.mutate({ id: it.id, rating: -1 })}>
              👎
            </button>
            <button className="mini-btn" onClick={() => favMut.mutate({ id: it.id, favorite: !it.favorite })}>
              {it.favorite ? '★ 已收藏' : '☆ 收藏'}
            </button>
            <CopyButton text={it.final_prompt} />
            <button className="mini-btn danger" onClick={() => delMut.mutate(it.id)}>
              删除
            </button>
          </div>
          <div className="result-text">{it.final_prompt}</div>
        </div>
      ))}
    </div>
  )
}
