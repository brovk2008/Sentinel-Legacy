/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        sentinel: {
          950: "#090D14", // Deep canvas base
          900: "#0F1420", // Card & sidebar background
          850: "#141A29", // Elevated surface
          800: "#1E2638", // Subtle borders & dividers
          700: "#2B364D", // Interactive border & hover
          600: "#475569", // Muted text
          blue: {
            50: "#EFF6FF",
            100: "#DBEAFE",
            500: "#3B82F6",
            600: "#2563EB",
            700: "#1D4ED8",
          },
          emerald: {
            500: "#10B981",
            600: "#059669",
          },
          amber: {
            500: "#F59E0B",
            600: "#D97706",
          },
          rose: {
            500: "#EF4444",
            600: "#DC2626",
          },
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ['"Inter"', "-apple-system", "BlinkMacSystemFont", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(0, 0, 0, 0.25)",
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px -1px rgba(0, 0, 0, 0.3)",
        elevated: "0 4px 6px -1px rgba(0, 0, 0, 0.35), 0 2px 4px -2px rgba(0, 0, 0, 0.35)",
        modal: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
      },
    },
  },
  plugins: [],
};
