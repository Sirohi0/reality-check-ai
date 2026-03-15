import { useState, useEffect, useRef } from 'react'

/**
 * Animates a number from 0 to target when element enters viewport
 * @param {number} target - final number
 * @param {number} duration - animation duration in ms
 * @returns {{ ref, value }}
 */
export default function useAnimatedCounter(target, duration = 1400) {
  const [value, setValue] = useState(0)
  const ref = useRef(null)
  const hasAnimated = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          const startTime = Date.now()

          const tick = () => {
            const elapsed = Date.now() - startTime
            const progress = Math.min(elapsed / duration, 1)
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3)
            setValue(eased * target)
            if (progress < 1) requestAnimationFrame(tick)
          }
          tick()
          observer.disconnect()
        }
      },
      { threshold: 0.5 }
    )

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [target, duration])

  return { ref, value }
}
