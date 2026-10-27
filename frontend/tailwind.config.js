/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#0B0F14",          // Deep charcoal background
          surface: "#121820",     // Elevated surface/panel
          border: "#1E293B",      // Subtle card border
          borderLight: "#334155", // Interactive border
          textPrimary: "#F1F5F9", // Accessible high contrast white/slate
          textMuted: "#94A3B8",   // Secondary typography
          teal: {
            DEFAULT: "#0D9488",
            light: "#14B8A6",
            dark: "#0F766E",
            dim: "#134E4A",
          },
          cyan: {
            DEFAULT: "#0891B2",
            light: "#06B6D4",
          },
          status: {
            healthy: "#10B981",    // Controlled emerald
            degraded: "#F59E0B",   // Amber
            critical: "#EF4444",   // Red
            info: "#0284C7",       // Blue
          }
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
