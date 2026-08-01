import type { Config } from "tailwindcss";

// Barbie-land palette — see docs/PRD.md §8.1 and the wireframes artifact. Values
// live as CSS custom properties in app/globals.css (light/dark aware); Tailwind
// just aliases them so components can use `bg-accent`, `text-ink-soft`, etc.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        "bg-elevated": "var(--bg-elevated)",
        ink: "var(--ink)",
        "ink-soft": "var(--ink-soft)",
        "ink-faint": "var(--ink-faint)",
        line: "var(--line)",
        accent: "var(--accent)",
        "accent-soft": "var(--accent-soft)",
        "accent-ink": "var(--accent-ink)",
        secondary: "var(--secondary)",
        "secondary-soft": "var(--secondary-soft)",
        tertiary: "var(--tertiary)",
      },
      borderRadius: {
        lg: "20px",
        xl: "28px",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
  plugins: [],
};

export default config;
