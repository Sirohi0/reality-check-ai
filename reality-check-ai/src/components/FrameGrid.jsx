import { COLORS } from '../utils/constants'

export default function FrameGrid({ frameCount, analyzedCount, isFake }) {
  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(10, 1fr)',
          gap: 3,
        }}
      >
        {Array.from({ length: frameCount }).map((_, i) => {
          const analyzed = i < analyzedCount
          const suspicious =
            analyzed && isFake && (i % 4 === 1 || i % 7 === 2)

          return (
            <div
              key={i}
              style={{
                aspectRatio: '16/9',
                borderRadius: 3,
                background: suspicious
                  ? COLORS.dangerDim
                  : analyzed
                    ? 'rgba(0,229,160,0.12)'
                    : 'rgba(255,255,255,0.03)',
                border: `1px solid ${
                  suspicious
                    ? 'rgba(255,77,106,0.35)'
                    : analyzed
                      ? 'rgba(0,229,160,0.18)'
                      : COLORS.borderSubtle
                }`,
                transition: 'all 0.3s',
              }}
            />
          )
        })}
      </div>

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          gap: 20,
          marginTop: 12,
          justifyContent: 'center',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: COLORS.textDim,
        }}
      >
        <span style={{ color: 'rgba(0,229,160,0.6)' }}>■ Clean</span>
        {isFake && (
          <span style={{ color: 'rgba(255,77,106,0.6)' }}>■ Anomaly</span>
        )}
        {analyzedCount < frameCount && <span>□ Pending</span>}
      </div>
    </div>
  )
}
