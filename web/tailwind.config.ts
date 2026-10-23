import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f4efe6",
        ink: "#1c1916",
        muted: "#6b635b",
        line: "#e3d8c8",
        card: "#fffdfb",
        teal: {
          DEFAULT: "#0d6b56",
          dark: "#084838",
          soft: "#e7f3ee",
        },
        clay: "#9a4e28",
      },
      fontFamily: {
        serif: ["Iowan Old Style", "Palatino Linotype", "Palatino", "Georgia", "serif"],
        sans: [
          "ui-sans-serif",
          "system-ui",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(28, 25, 22, 0.04), 0 16px 40px rgba(28, 25, 22, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
