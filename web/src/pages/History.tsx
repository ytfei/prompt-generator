import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { deleteGeneration, listGenerations, submitFeedback, toggleFavorite, updateGeneration } from '../api/client'
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

/** 行内标签/备注编辑器 */
function TagNoteEditor({
  item,
  onDone,
}: {
  item: GenerationItem
  onDone: () => void
}) {
  const qc = useQueryClient()
  const [tagsText, setTagsText] = useState(item.tags.join('、'))
  const [note, setNote] = useState(item.note)
  const saveMut = useMutation({
    mutationFn: () =>
      updateGeneration(item.id, {
        tags: tagsText.split(/[、,，\s]+/).map((t) => t.trim()).filter(Boolean),
        note,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['generations'] })
      onDone()
    },
  })

  return (
    <div className="tagnote-editor">
      <input
        placeholder="标签（用顿号/逗号分隔，如：牛市、首图、备选）"
        value={tagsText}
        onChange={(e) => setTagsText(e.target.value)}
      />
      <textarea
        placeholder="备注：出图效果如何、适合配什么文章…"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={2}
      />
      <div className="tagnote-actions">
        <button className="mini-btn" onClick={onDone}>取消</button>
        <button className="mini-btn good" disabled={saveMut.isPending} onClick={() => saveMut.mutate()}>
          {saveMut.isPending ? '保存中…' : '保存'}
        </button>
      </div>
    </div>
  )
}

export default function History() {
  const qc = useQueryClient()
  const [onlyFav, setOnlyFav] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
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
            {it.rating === 1 && <span className="rating-badge">👍</span>}
            {it.rating === -1 && <span className="rating-badge">👎</span>}
            <span style={{ flex: 1 }} />
            <button className="mini-btn" onClick={() => fbMut.mutate({ id: it.id, rating: 1 })}>👍</button>
            <button className="mini-btn" onClick={() => fbMut.mutate({ id: it.id, rating: -1 })}>👎</button>
            <button className={`mini-btn${it.favorite ? ' fav' : ''}`} onClick={() => favMut.mutate({ id: it.id, favorite: !it.favorite })}>
              {it.favorite ? '★ 已收藏' : '☆ 收藏'}
            </button>
            <button className="mini-btn" onClick={() => setEditingId(editingId === it.id ? null : it.id)}>
              ✎ 标签备注{it.tags.length ? `(${it.tags.length})` : ''}
            </button>
            <CopyButton text={it.final_prompt} />
            <button className="mini-btn danger" onClick={() => delMut.mutate(it.id)}>
              删除
            </button>
          </div>
          <div className="result-text">{it.final_prompt}</div>
          {(it.tags.length > 0 || it.note) && (
            <div className="tagnote-display">
              {it.tags.map((t) => (
                <span key={t} className="tag-chip">#{t}</span>
              ))}
              {it.note && <span className="note-text">📝 {it.note}</span>}
            </div>
          )}
          {editingId === it.id && <TagNoteEditor item={it} onDone={() => setEditingId(null)} />}
        </div>
      ))}
    </div>
  )
}
