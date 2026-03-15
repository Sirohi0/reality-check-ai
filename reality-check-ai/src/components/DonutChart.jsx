import { useState, useEffect } from 'react'
import { COLORS } from '../utils/constants'

export default function DonutChart({ realPercent = 83, size = 300 }) {
  const [animated, setAnimated] = useState(0)
  const suspiciousPercent = 100 - realPercent
  const radius = 110
  const circumference = 2 * Math.PI * radius
  const cx = size / 2
  const cy = size / 2

  useEffect(() => {
    const duration = 1800
    const startTime = Date.now()
    const tick = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimated(eased * realPercent)
      if (progress < 1) requestAnimationFrame(tick)
    }
    tick()
  }, [realPercent])

  const realArc = (animated / 100) * circumference
  const suspArc = (suspiciousPercent / 100) * circumference
  const gap = circumference * 0.02

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      {/* Outer glow */}
      <div
        style={{
          position: 'absolute',
          inset: -20,
          background:
            'radial-gradient(circle, rgba(0,229,160,0.06) 0%, transparent 70%)',
          borderRadius: '50%',
        }}
      />

      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id="tealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00c98a" />
            <stop offset="100%" stopColor="#00e5a0" />
          </linearGradient>
          <linearGradient id="coralGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ff4d6a" />
            <stop offset="100%" stopColor="#ff6b82" />
          </linearGradient>
          <filter id="chartGlow">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background track */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="28"
        />

        {/* Real (teal) arc */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none" stroke="url(#tealGrad)" strokeWidth="28"
          strokeLinecap="round"
          strokeDasharray={`${realArc - gap} ${circumference - realArc + gap}`}
          transform={`rotate(-90 ${cx} ${cy})`}
          filter="url(#chartGlow)"
        />

        {/* Suspicious (coral) arc */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none" stroke="url(#coralGrad)" strokeWidth="28"
          strokeLinecap="round"
          strokeDasharray={`${suspArc - gap} ${circumference - suspArc + gap}`}
          transform={`rotate(${-90 + (realPercent / 100) * 360 + 3} ${cx} ${cy})`}
          filter="url(#chartGlow)"
        />

        {/* Center text */}
        <text
          x={cx} y={cy - 8}
          textAnchor="middle" dominantBaseline="central"
          fill="white"
          style={{
            fontSize: 56,
            fontFamily: "'Playfair Display', serif",
            fontWeight: 800,
            fontStyle: 'italic',
          }}
        >
          {Math.round(animated)}%
        </text>
        <text
          x={cx} y={cy + 30}
          textAnchor="middle"
          fill={COLORS.textMuted}
          style={{
            fontSize: 14,
            fontFamily: "'Outfit', sans-serif",
            fontWeight: 500,
            letterSpacing: 2,
          }}
        >
          Authentic
        </text>
      </svg>

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 32,
          marginTop: 12,
        }}
      >
        {[
          { color: COLORS.accent, label: 'Real' },
          { color: COLORS.danger, label: 'Suspicious' },
        ].map(({ color, label }) => (
          <div
            key={label}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <div
              style={{
                width: 14, height: 14, borderRadius: 3, background: color,
              }}
            />
            <span
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: 14, fontWeight: 600, color: COLORS.text,
              }}
            >
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
