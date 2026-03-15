import { COLORS, TRUST_BADGES } from '../utils/constants'

export default function TrustBadges() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        gap: 48,
        padding: '20px 48px',
        background: COLORS.bgDark,
        borderTop: `1px solid ${COLORS.borderSubtle}`,
      }}
    >
      {TRUST_BADGES.map((b) => (
        <div
          key={b.text}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <span style={{ fontSize: 16 }}>{b.icon}</span>
          <span
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontSize: 12,
              color: COLORS.textMuted,
              fontWeight: 500,
            }}
          >
            {b.text}
          </span>
        </div>
      ))}
    </div>
  )
}
