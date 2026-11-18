import type { OptionGroup } from '../types'
import { useSelections } from '../stores/selections'

interface Props {
  groupId: string
  group: OptionGroup
  /** 用途组联动：选中带 ratio 的选项时同步画幅组 */
  onUsageSelect?: (label: string, ratio: string) => void
}

export default function ChipGroup({ groupId, group, onUsageSelect }: Props) {
  const { selections, setOption } = useSelections()
  const cur = selections[groupId]
  const selectedCount = Array.isArray(cur) ? cur.length : cur ? 1 : 0

  const handleClick = (label: string, ratio: string) => {
    setOption(groupId, label, group.multi)
    if (groupId === 'usage' && ratio && cur !== label) onUsageSelect?.(label, ratio)
  }

  return (
    <div className="group">
      <h3>
        {group.name}{' '}
        <span className={`state${selectedCount ? ' on' : ''}`}>
          {group.multi
            ? selectedCount
              ? `已选 ${selectedCount}`
              : '不限定'
            : (cur as string) || '不限定'}
        </span>
      </h3>
      {group.hint && <div className="hint">{group.hint}</div>}
      <div className="chips">
        {group.options.map((opt) => {
          const on = group.multi
            ? Array.isArray(cur) && cur.includes(opt.label)
            : cur === opt.label
          return (
            <span
              key={opt.label}
              className={`chip${on ? ' on' : ''}`}
              onClick={() => handleClick(opt.label, opt.ratio)}
            >
              {opt.label}
            </span>
          )
        })}
      </div>
    </div>
  )
}
