import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { deleteTemplate, listTemplates } from '../api/client'
import { useSelections } from '../stores/selections'
import type { TemplateInfo } from '../types'

function selectionSummary(t: TemplateInfo): string {
  return Object.values(t.selections)
    .map((v) => (Array.isArray(v) ? v.join('、') : v))
    .filter(Boolean)
    .join(' · ')
}

export default function Templates() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const { applySelections } = useSelections()
  const { data: templates, isLoading } = useQuery({ queryKey: ['templates'], queryFn: listTemplates })

  const delMut = useMutation({
    mutationFn: (id: string) => deleteTemplate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['templates'] }),
  })

  if (isLoading) return <div className="page-loading">加载模板中…</div>

  return (
    <div className="history-page">
      <div className="presets">
        <span className="label">我的模板（在工作台生成结果下方可保存）</span>
      </div>
      {(templates ?? []).length === 0 && (
        <div className="page-loading">暂无模板：在工作台选好配置后，结果下方可保存为模板</div>
      )}
      {(templates ?? []).map((t) => (
        <div key={t.id} className="history-item">
          <div className="history-meta">
            <strong className="tpl-name">{t.name}</strong>
            <span>·</span>
            <span>{new Date(t.created_at).toLocaleString('zh-CN')}</span>
            <span style={{ flex: 1 }} />
            <button
              className="mini-btn"
              onClick={() => {
                applySelections(t.selections)
                navigate('/')
              }}
            >
              ✓ 使用
            </button>
            <button className="mini-btn danger" onClick={() => delMut.mutate(t.id)}>
              删除
            </button>
          </div>
          <div className="tpl-summary">{selectionSummary(t)}</div>
        </div>
      ))}
    </div>
  )
}
