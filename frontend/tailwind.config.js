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
          bg: '#F1F5F9',
          surface: '#FFFFFF',
          secondary: '#E8EEF5',
          navy: '#172B4D',
          navyBorder: '#2A4365',
          text: '#1E293B',
          muted: '#64748B',
          teal: '#0D9488',
          tealLight: '#CCFBF1',
          ice: '#38BDF8',
          violet: '#8B7CF6',
          amber: '#F59E0B',
          critical: '#EF6461',
          normal: '#15803D',
          border: '#DCE4ED',
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
