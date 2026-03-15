/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0d1520',
          dark: '#0a1018',
          surface: '#111d2e',
          light: '#162236',
        },
        accent: {
          DEFAULT: '#00e5a0',
          dim: 'rgba(0,229,160,0.12)',
        },
        danger: {
          DEFAULT: '#ff4d6a',
          dim: 'rgba(255,77,106,0.12)',
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body: ['"Outfit"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
