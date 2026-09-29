/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        polar: {
          bg: '#F4F7FA',
          card: '#FFFFFF',
          panel: '#F8FAFC',
          border: '#E2E8F0',
          subtle: '#CBD5E1',
          teal: '#0D9488',
          tealBg: '#E6FFFB',
          text: '#183153',
          muted: '#64748B',
          normal: '#15803D',
          warning: '#D97706',
          critical: '#DC2626',
          offline: '#64748B',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
