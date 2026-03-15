import { useState, useEffect } from 'react'
import { COLORS } from '../utils/constants'

export default function ConfidenceGauge({ score, isFake }) {
  const radius = 90
  const circumference = 2 * Math.PI * radius
  const [val, setVal] = useState(0)

  useEffect(() => {
    const duration = 1600
    const start = Date.now()
    const tick = () => {
      const p = Math.min((Date.now() - start) / duration, 1)
      setVal((1 - Math.pow(1 - p, 3)) * score)
      if (p < 1) requestAnimationFrame(tick)
    }
    tick()
  }, [score])

  const offset = circumference - (val / 100) * circumference * 0.75
  const color = isFake ? COLORS.danger : COLORS.accent

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
      }}
    >
      <svg width="220" height="180" viewBox="0 0 220 200">
        <defs>
          <linearGradient
            id="resultGrad"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="100%"
          >
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} />
          </linearGradient>
          <filter id="resultGlow">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <circle
          cx="110"
          cy="110"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.04)"
          strokeWidth="14"
          strokeDasharray={
            circumference * 0.75 + ' ' + circumference * 0.25
          }
          strokeLinecap="round"
          transform="rotate(135 110 110)"
        />

        {/* Active arc */}
        <circle
          cx="110"
          cy="110"
          r={radius}
          fill="none"
          stroke="url(#resultGrad)"
          strokeWidth="14"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(135 110 110)"
          filter="url(#resultGlow)"
        />

        {/* Score text */}
        <text
          x="110"
          y="100"
          textAnchor="middle"
          fill="white"
          style={{
            fontSize: 44,
            fontFamily: "'Playfair Display', serif",
            fontWeight: 800,
            fontStyle: 'italic',
          }}
        >
          {val.toFixed(1)}%
        </text>
        <text
          x="110"
          y="128"
          textAnchor="middle"
          fill={COLORS.textDim}
          style={{
            fontSize: 11,
            fontFamily: "'Outfit', sans-serif",
            letterSpacing: 3,
            textTransform: 'uppercase',
          }}
        >
          confidence
        </text>
      </svg>

      {/* Verdict badge */}
      <div
        style={{
          padding: '10px 30px',
          borderRadius: 40,
          background: isFake ? COLORS.dangerDim : COLORS.accentDim,
          border: `1px solid ${
            isFake ? 'rgba(255,77,106,0.3)' : 'rgba(0,229,160,0.3)'
          }`,
          color: color,
          fontFamily: "'Outfit', sans-serif",
          fontWeight: 700,
          fontSize: 14,
          letterSpacing: 2,
          textTransform: 'uppercase',
        }}
      >
        {isFake ? '⚠ Deepfake Detected' : '✓ Authentic Video'}
      </div>
    </div>
  )
}
