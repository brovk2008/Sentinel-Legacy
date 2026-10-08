/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        sentinel: {
          950: "#06090F",
          900: "#0B111D",
          850: "#0F172A",
          800: "#1E293B",
          700: "#334155",
          cyan: "#06B6D4",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#EF4444",
          violet: "#8B5CF6",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(6, 182, 212, 0.25)",
        "glow-red": "0 0 25px -5px rgba(239, 68, 68, 0.4)",
        "glow-emerald": "0 0 25px -5px rgba(16, 185, 129, 0.3)",
      },
    },
  },
  plugins: [],
};
