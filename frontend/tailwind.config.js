/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        archive: {
          alabaster: "#F7F5F0",
          ivory: "#FDFBF7",
          hairline: "#E2DDD5",
          borderDark: "#C5BDB2",
          charcoal: "#18181B",
          ink: "#27272A",
          muted: "#71717A",
          stone: "#52525B",
          terracotta: "#9E3B24",
          terracottaDark: "#7E2A16",
          terracottaLight: "#F8ECE9",
          parchment: "#F1ECE1",
          gold: "#B4833E",
          emerald: "#2D6A4F",
        },
      },
      fontFamily: {
        serif: ["'Cormorant Garamond'", "Georgia", "serif"],
        sans: ["'Plus Jakarta Sans'", "system-ui", "-apple-system", "sans-serif"],
        mono: ["'JetBrains Mono'", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        'curator': '0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03)',
        'plate': '0 2px 8px rgba(0, 0, 0, 0.06), 0 12px 24px -8px rgba(0, 0, 0, 0.08)',
        'stamp': 'inset 0 0 0 1px rgba(158, 59, 36, 0.2), 0 1px 2px rgba(158, 59, 36, 0.1)',
      },
      letterSpacing: {
        'archival': '0.12em',
        'stamp': '0.2em',
      },
    },
  },
  plugins: [],
};

