import { COLORS, PIPELINE_STEPS } from '../utils/constants'
import PipelineStep from './PipelineStep'

export default function PipelineTracker({ stepStatuses }) {
  return (
    <div
      style={{
        background: COLORS.surface,
        border: `1px solid ${COLORS.borderSubtle}`,
        borderRadius: 16,
        padding: 24,
      }}
    >
      <div
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: COLORS.textDim,
          letterSpacing: 3,
          textTransform: 'uppercase',
          marginBottom: 20,
        }}
      >
        Analysis Pipeline
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {PIPELINE_STEPS.map((step, i) => (
          <PipelineStep key={step.id} step={step} status={stepStatuses[i]} />
        ))}
      </div>
    </div>
  )
}
