import { useState, useEffect, useRef } from 'react'
import { COLORS } from '../utils/constants'

export default function AnimatedStat({ value, label }) {
  const [display, setDisplay] = useState('')
  const ref = useRef(null)
  const hasAnimated = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          let i = 0
          const interval = setInterval(() => {
            i++
            if (i <= value.length) {
              setDisplay(value.slice(0, i))
            } else {
              clearInterval(interval)
            }
          }, 80)
          observer.disconnect()
        }
      },
      { threshold: 0.5 }
    )

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [value])

  return (
    <div ref={ref} style={{ textAlign: 'left' }}>
      <div
        style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 38,
          fontWeight: 800,
          fontStyle: 'italic',
          color: COLORS.accent,
          lineHeight: 1.1,
          minHeight: '1.1em',
        }}
      >
        {display || '\u00A0'}
      </div>
      <div
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: 12,
          color: COLORS.textDim,
          marginTop: 6,
          fontWeight: 500,
        }}
      >
        {label}
      </div>
    </div>
  )
}
