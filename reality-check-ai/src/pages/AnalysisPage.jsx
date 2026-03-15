import { useNavigate } from 'react-router-dom'
import { useCallback } from 'react'
import { COLORS, FRAME_COUNT } from '../utils/constants'
import useAnalysis from '../hooks/useAnalysis'
import PipelineTracker from '../components/PipelineTracker'
import FrameGrid from '../components/FrameGrid'

export default function AnalysisPage({ file, onResult }) {
  const navigate = useNavigate()

  const handleComplete = useCallback(
    (result) => {
      onResult(result)
      navigate('/result')
    },
    [onResult, navigate]
  )

  const { stepStatuses, analyzedFrames } = useAnalysis(file, handleComplete)

  return (
    <div
      className="animate-fade-in-up"
      style={{
        minHeight: 'calc(100vh - 64px)',
        padding: 48,
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 24,
          maxWidth: 900,
          margin: '0 auto',
        }}
      >
        {/* Pipeline tracker */}
        <PipelineTracker stepStatuses={stepStatuses} />

        {/* Right side */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* File info */}
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
                marginBottom: 14,
              }}
            >
              Input File
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '12px 16px',
                borderRadius: 10,
                background: 'rgba(255,255,255,0.02)',
                border: `1px solid ${COLORS.borderSubtle}`,
              }}
            >
              <span style={{ fontSize: 24 }}>📹</span>
              <div>
                <div
                  style={{
                    fontFamily: "'Outfit', sans-serif",
                    fontSize: 14,
                    fontWeight: 600,
                    color: COLORS.text,
                  }}
                >
                  {file?.name || 'video_sample.mp4'}
                </div>
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 11,
                    color: COLORS.accent,
                    marginTop: 2,
                  }}
                >
                  Processing...
                </div>
              </div>
            </div>
          </div>

          {/* Frame analysis */}
          <div
            style={{
              background: COLORS.surface,
              border: `1px solid ${COLORS.borderSubtle}`,
              borderRadius: 16,
              padding: 24,
              flex: 1,
            }}
          >
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                color: COLORS.textDim,
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: 4,
              }}
            >
              Frame Analysis
            </div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: COLORS.accent,
                marginBottom: 14,
              }}
            >
              {analyzedFrames}/{FRAME_COUNT} frames processed
            </div>
            <FrameGrid
              frameCount={FRAME_COUNT}
              analyzedCount={analyzedFrames}
              isFake={false}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
