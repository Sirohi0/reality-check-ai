import { Link, useLocation } from 'react-router-dom'
import { COLORS } from '../utils/constants'

export default function Navbar() {
  const location = useLocation()

  const linkStyle = {
    fontFamily: "'Outfit', sans-serif",
    fontSize: 14,
    fontWeight: 500,
    color: COLORS.textMuted,
    textDecoration: 'none',
    transition: 'color 0.2s',
  }

  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 48px',
        height: 64,
        background: COLORS.bgDark,
        borderBottom: `1px solid ${COLORS.borderSubtle}`,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Logo */}
      <Link to="/" style={{ textDecoration: 'none' }}>
        <span
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: 6,
            color: COLORS.text,
            textTransform: 'uppercase',
          }}
        >
          RE<span style={{ color: COLORS.accent }}>∧</span>LITY CHECK AI
        </span>
      </Link>

      {/* Nav Links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
        {[
          { label: 'Home', to: '/' },
          { label: 'FAQ', to: '/faq' },
          { label: 'About', to: '/about' },
          { label: 'Sign In', to: '/signin' },
        ].map(({ label, to }) => (
          <Link
            key={label}
            to={to}
            style={{
              ...linkStyle,
              color: location.pathname === to ? COLORS.text : COLORS.textMuted,
            }}
            onMouseEnter={(e) => (e.target.style.color = COLORS.text)}
            onMouseLeave={(e) =>
              (e.target.style.color =
                location.pathname === to ? COLORS.text : COLORS.textMuted)
            }
          >
            {label}
          </Link>
        ))}

        <Link
          to="/upload"
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 14,
            fontWeight: 600,
            color: COLORS.bgDark,
            background: COLORS.accent,
            border: 'none',
            borderRadius: 6,
            padding: '8px 20px',
            textDecoration: 'none',
            transition: 'transform 0.15s, box-shadow 0.15s',
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-1px)'
            e.target.style.boxShadow = `0 4px 16px ${COLORS.accentDim}`
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = 'none'
          }}
        >
          Get Started
        </Link>
      </div>
    </nav>
  )
}
