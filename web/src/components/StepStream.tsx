import {
  GENERATE_NODE_ORDER,
  I2I_NODE_ORDER,
  NODE_LABELS,
  REFINE_NODE_ORDER,
  type StepState,
} from '../types'

export type { StepState }

export default function StepStream({
  steps,
  mode = 'generate',
}: {
  steps: StepState[]
  mode?: 'generate' | 'refine' | 'i2i'
}) {
  if (steps.length === 0) return null
  const order =
    mode === 'refine' ? REFINE_NODE_ORDER : mode === 'i2i' ? I2I_NODE_ORDER : GENERATE_NODE_ORDER
  const doneCount = steps.filter((s) => s.status === 'done').length

  return (
    <ul className="steps">
      {order.map((node, i) => {
        const state = steps.find((s) => s.node === node)
        const cls = !state
          ? i <= doneCount
            ? 'active'
            : ''
          : state.status === 'done'
            ? 'done'
            : 'active'
        return (
          <li key={node} className={cls}>
            <span className="dot" /> {NODE_LABELS[node]}
          </li>
        )
      })}
    </ul>
  )
}
