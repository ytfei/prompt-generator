import { NODE_LABELS } from '../types'

const NODE_ORDER = ['parse_intent', 'enrich_details', 'conflict_check', 'assemble', 'refine']

export interface StepState {
  node: string
  status: 'running' | 'done'
}

export default function StepStream({ steps }: { steps: StepState[] }) {
  if (steps.length === 0) return null
  const doneCount = steps.filter((s) => s.status === 'done').length

  return (
    <ul className="steps">
      {NODE_ORDER.map((node, i) => {
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
