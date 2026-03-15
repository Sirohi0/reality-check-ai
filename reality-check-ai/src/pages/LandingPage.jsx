import { Link } from 'react-router-dom'
import { COLORS } from '../utils/constants'
import DonutChart from '../components/DonutChart'
import TrustBadges from '../components/TrustBadges'
import AnimatedStat from '../components/AnimatedStat'

export default function LandingPage() {
  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Gradient accent line under nav */}
      <div
        style={{
          height: 2,
          background: `linear-gradient(90deg, transparent, ${COLORS.accent}, transparent)`,
        }}
      />

      {/* Hero */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '60px 80px 40px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Subtle grid bg */}
        <svg
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            opacity: 0.03,
            pointerEvents: 'none',
          }}
        >
          <defs>
            <pattern
              id="heroGrid"
              width="80"
              height="80"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 80 0 L 0 0 0 80"
                fill="none"
                stroke={COLORS.accent}
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#heroGrid)" />
        </svg>

        {/* Main headline */}
        <h1
          className="animate-fade-in-up"
          style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 52,
            fontWeight: 800,
            fontStyle: 'italic',
            color: COLORS.text,
            lineHeight: 1.2,
            marginBottom: 40,
          }}
        >
          See Through{' '}
          <span style={{ color: COLORS.accent }}>The Lie</span>
        </h1>

        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: 80,
          }}
        >
          {/* Left column */}
          <div
            className="animate-fade-in-up-delay-1"
            style={{ flex: 1, maxWidth: 520 }}
          >
            {/* AI badge */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 16px',
                borderRadius: 20,
                border: `1px solid ${COLORS.border}`,
                marginBottom: 28,
              }}
            >
              <div
                className="animate-pulse-glow"
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: COLORS.accent,
                  boxShadow: `0 0 8px ${COLORS.accent}`,
                }}
              />
              <span
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontSize: 13,
                  fontWeight: 600,
                  color: COLORS.accent,
                }}
              >
                AI-Powered Detection
              </span>
            </div>

            {/* Sub-headlines */}
            <h2
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: 32,
                fontWeight: 800,
                color: COLORS.text,
                lineHeight: 1.4,
                marginBottom: 20,
              }}
            >
              Verify Media.
              <br />
              Expose{' '}
              <span style={{ color: COLORS.danger }}>Deepfakes.</span>
              <br />
              Trust What's Real.
            </h2>

            <p
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: 15,
                color: COLORS.textMuted,
                lineHeight: 1.7,
                marginBottom: 32,
                maxWidth: 420,
              }}
            >
              Upload any image or video and our AI will analyze it for signs of
              digital manipulation in seconds.
            </p>

            {/* CTA Buttons */}
            <div style={{ display: 'flex', gap: 16, marginBottom: 48 }}>
              <Link
                to="/upload"
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontSize: 15,
                  fontWeight: 700,
                  color: COLORS.bgDark,
                  background: COLORS.accent,
                  border: 'none',
                  borderRadius: 8,
                  padding: '14px 28px',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: '0 4px 20px rgba(0,229,160,0.25)',
                  transition: 'transform 0.2s',
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.transform = 'translateY(-2px)')
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.transform = 'translateY(0)')
                }
              >
                ▲ Start Detection
              </Link>
              <button
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontSize: 15,
                  fontWeight: 600,
                  color: COLORS.text,
                  background: 'transparent',
                  border: `1px solid ${COLORS.borderSubtle}`,
                  borderRadius: 8,
                  padding: '14px 28px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'border-color 0.2s',
                }}
                onMouseEnter={(e) =>
                  (e.target.style.borderColor = 'rgba(255,255,255,0.15)')
                }
                onMouseLeave={(e) =>
                  (e.target.style.borderColor = COLORS.borderSubtle)
                }
              >
                How It Works →
              </button>
            </div>

            {/* Stats */}
            <div style={{ display: 'flex', gap: 48 }}>
              <AnimatedStat value="2.4M+" label="Files Analyzed" />
              <AnimatedStat value="85%+" label="Detection Accuracy" />
              <AnimatedStat value="<8s" label="Avg. Analysis Time" />
            </div>
          </div>

          {/* Right column — Donut Chart */}
          <div
            className="animate-fade-in-up-delay-2"
            style={{
              background: COLORS.surface,
              borderRadius: 24,
              padding: '32px 36px',
              border: `1px solid ${COLORS.borderSubtle}`,
            }}
          >
            <DonutChart realPercent={83} size={300} />
          </div>
        </div>
      </div>

      <TrustBadges />
    </div>
  )
}
