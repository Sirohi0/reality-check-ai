import { COLORS } from '../utils/constants'

export default function InfoCard({ icon, title, titleColor, children }) {
  return (
    <div
      style={{
        padding: '24px 28px',
        borderRadius: 14,
        background: COLORS.surface,
        border: `1px solid ${COLORS.border}`,
      }}
    >
      <div
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: 16,
          fontWeight: 700,
          color: titleColor || COLORS.accent,
          marginBottom: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        {icon} {title}
      </div>
      <p
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: 13,
          color: COLORS.textMuted,
          lineHeight: 1.7,
          margin: 0,
        }}
      >
        {children}
      </p>
    </div>
  )
}
