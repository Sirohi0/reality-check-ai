import { useNavigate } from 'react-router-dom'
import { COLORS, FRAME_COUNT } from '../utils/constants'
import ConfidenceGauge from '../components/ConfidenceGauge'
import FrameGrid from '../components/FrameGrid'

export default function ResultPage({ result, onReset }) {
  const navigate = useNavigate()

  if (!result) {
    navigate('/')
    return null
  }

  const handleAnalyzeAnother = () => {
    onReset()
    navigate('/upload')
  }

  const stats = [
    { label: 'Frames Analyzed', value: String(result.frames), sub: 'uniform sampling' },
    { label: 'Faces Detected', value: String(result.facesDetected || 28), sub: 'RetinaFace' },
    { label: 'Model', value: 'EN-B4', sub: '+ Attn-LSTM' },
  ]

  return (
    <div
      className="animate-fade-in-up"
      style={{
        minHeight: 'calc(100vh - 64px)',
        padding: 48,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* Main result card */}
      <div
        style={{
          width: '100%',
          maxWidth: 720,
          background: COLORS.surface,
          border: `1px solid ${
            result.isFake
              ? 'rgba(255,77,106,0.15)'
              : 'rgba(0,229,160,0.15)'
          }`,
          borderRadius: 20,
          padding: '44px 36px',
          textAlign: 'center',
        }}
      >
        <ConfidenceGauge score={result.confidence} isFake={result.isFake} />

        {/* Stats grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 14,
            marginTop: 36,
          }}
        >
          {stats.map((item) => (
            <div
              key={item.label}
              style={{
                padding: '18px 14px',
                borderRadius: 12,
                background: 'rgba(255,255,255,0.02)',
                border: `1px solid ${COLORS.borderSubtle}`,
              }}
            >
              <div
                style={{
                  fontFamily: "'Playfair Display', serif",
                  fontSize: 24,
                  fontWeight: 800,
                  fontStyle: 'italic',
                  color: COLORS.text,
                }}
              >
                {item.value}
              </div>
              <div
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontSize: 11,
                  color: COLORS.textMuted,
                  marginTop: 4,
                  fontWeight: 600,
                }}
              >
                {item.label}
              </div>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 9,
                  color: COLORS.textDim,
                  marginTop: 2,
                }}
              >
                {item.sub}
              </div>
            </div>
          ))}
        </div>

        {/* Frame-level results */}
        <div style={{ marginTop: 28 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: COLORS.textDim,
              letterSpacing: 3,
              textTransform: 'uppercase',
              marginBottom: 14,
            }}
          >
            Frame-Level Results
          </div>
          <FrameGrid
            frameCount={FRAME_COUNT}
            analyzedCount={FRAME_COUNT}
            isFake={result.isFake}
          />
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 14, marginTop: 28 }}>
        <button
          onClick={handleAnalyzeAnother}
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 14,
            fontWeight: 600,
            color: COLORS.accent,
            background: COLORS.accentDim,
            border: `1px solid ${COLORS.border}`,
            borderRadius: 10,
            padding: '12px 28px',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) =>
            (e.target.style.background = 'rgba(0,229,160,0.18)')
          }
          onMouseLeave={(e) =>
            (e.target.style.background = COLORS.accentDim)
          }
        >
          Analyze Another
        </button>
        <button
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 14,
            fontWeight: 600,
            color: COLORS.textMuted,
            background: 'rgba(255,255,255,0.03)',
            border: `1px solid ${COLORS.borderSubtle}`,
            borderRadius: 10,
            padding: '12px 28px',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) =>
            (e.target.style.background = 'rgba(255,255,255,0.05)')
          }
          onMouseLeave={(e) =>
            (e.target.style.background = 'rgba(255,255,255,0.03)')
          }
        >
          Download Report
        </button>
      </div>
    </div>
  )
}
