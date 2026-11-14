/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Dark HYPHEN-inspired palette
        'hypnen-navy': '#0a0e17',
        'hypnen-dark': '#0f1419',
        'hypnen-card': '#161b22',
        'hypnen-border': '#2a323c',
        'hypnen-cyan': '#00d4ff',
        'hypnen-cyan-dim': '#00a8cc',
        'hypnen-blue': '#1e90ff',
        'hypnen-teal': '#00b894',
        'hypnen-text': '#e6edf3',
        'hypnen-text-dim': '#8b949e',
        'hypnen-accent': '#ff6b35',
        'hypnen-green': '#2ecc71',
        'hypnen-red': '#e74c3c',
        'hypnen-yellow': '#f39c12',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}