import { COLORS } from '../utils/constants'

export default function PipelineStep({ step, status }) {
  const isActive = status === 'active'

  const bg =
    status === 'done'
      ? 'rgba(0,229,160,0.06)'
      : isActive
        ? 'rgba(0,180,255,0.06)'
        : 'rgba(255,255,255,0.015)'

  const borderColor =
    status === 'done'
      ? 'rgba(0,229,160,0.2)'
      : isActive
        ? 'rgba(0,180,255,0.25)'
        : COLORS.borderSubtle

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 16px',
        background: bg,
        border: `1px solid ${borderColor}`,
        borderRadius: 12,
        transition: 'all 0.4s',
        opacity: status === 'pending' ? 0.35 : 1,
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: isActive
            ? 'rgba(0,180,255,0.12)'
            : 'rgba(255,255,255,0.03)',
          fontSize: 18,
          flexShrink: 0,
          position: 'relative',
        }}
      >
        {step.icon}
        {isActive && (
          <div
            style={{
              position: 'absolute',
              inset: -3,
              borderRadius: 12,
              border: '2px solid rgba(0,180,255,0.35)',
              animation: 'pulse 1.5s ease-in-out infinite',
            }}
          />
        )}
      </div>

      {/* Text */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontWeight: 600,
            fontSize: 13,
            color: 'rgba(255,255,255,0.9)',
          }}
        >
          {step.label}
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10.5,
            color: COLORS.textDim,
            marginTop: 2,
          }}
        >
          {step.detail}
        </div>
      </div>

      {/* Status indicator */}
      <div style={{ fontSize: 14, flexShrink: 0 }}>
        {status === 'done' ? (
          '✅'
        ) : isActive ? (
          <div
            style={{
              width: 16,
              height: 16,
              border: '2px solid rgba(0,180,255,0.6)',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
            }}
          />
        ) : (
          ''
        )}
      </div>
    </div>
  )
}
