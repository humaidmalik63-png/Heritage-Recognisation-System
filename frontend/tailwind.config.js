/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        heritage: {
          bg: "#F5F3ED",
          primary: "#171816",
          secondary: "#6E7069",
          terracotta: "#A9472D",
          gold: "#B99A5B",
          sage: "#AAB9A4",
          blue: "#A9C8D4",
          card: "#FFFEFA",
          hairline: "#E3DFD5",
          borderDark: "#C5BDB2",
          darkCard: "#151514",
        },
        archive: {
          alabaster: "#F5F3ED",
          ivory: "#FFFEFA",
          hairline: "#E3DFD5",
          borderDark: "#C5BDB2",
          charcoal: "#171816",
          ink: "#27272A",
          muted: "#6E7069",
          stone: "#52525B",
          terracotta: "#A9472D",
          terracottaDark: "#87321C",
          terracottaLight: "#F8ECE9",
          parchment: "#EFECE4",
          gold: "#B99A5B",
          emerald: "#2D6A4F",
          sage: "#AAB9A4",
          blue: "#A9C8D4",
        },
      },
      fontFamily: {
        display: ["'Archivo'", "'Plus Jakarta Sans'", "sans-serif"],
        serif: ["'Cormorant Garamond'", "Georgia", "serif"],
        sans: ["'Inter'", "'Plus Jakarta Sans'", "system-ui", "-apple-system", "sans-serif"],
        mono: ["'JetBrains Mono'", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        'curator': '0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03)',
        'plate': '0 2px 8px rgba(0, 0, 0, 0.05), 0 12px 24px -8px rgba(0, 0, 0, 0.06)',
        'float': '0 4px 20px -4px rgba(23, 24, 22, 0.08), 0 16px 36px -12px rgba(23, 24, 22, 0.12)',
        'stamp': 'inset 0 0 0 1px rgba(169, 71, 45, 0.2), 0 1px 2px rgba(169, 71, 45, 0.1)',
      },
      letterSpacing: {
        'archival': '0.12em',
        'stamp': '0.2em',
      },
    },
  },
  plugins: [],
};
