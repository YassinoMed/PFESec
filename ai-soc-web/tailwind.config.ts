import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Fond cyber — hérité de l'UI existante (#050810)
        base: {
          900: "#050810",
          800: "#090d1a",
          700: "#0f1424",
          600: "#161d33",
        },
        // Bleu électrique — primaire (hsl 220 95% 62%)
        primary: {
          DEFAULT: "hsl(220 95% 62%)",
          dim: "hsl(220 60% 40%)",
          glow: "hsl(220 95% 62% / 0.5)",
        },
        // Sémantique verdict
        accept: "hsl(142 72% 46%)",
        block: "hsl(0 82% 58%)",
        warn: "hsl(38 92% 55%)",
        info: "hsl(195 90% 50%)",
        // Types de modèles
        bert: "#38bdf8",
        lora: "#c084fc",
        llm: "#f472b6",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-outfit)", "system-ui", "sans-serif"],
        mono: ["var(--font-fira)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.37)",
        glow: "0 0 20px hsl(220 95% 62% / 0.4)",
        "glow-block": "0 0 20px hsl(0 82% 58% / 0.4)",
        "glow-accept": "0 0 20px hsl(142 72% 46% / 0.4)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-up": "fadeUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) both",
        "slide-in": "slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) both",
        spin: "spin 1s linear infinite",
        "draw-outline": "drawOutline 2s ease forwards",
        draw: "draw 2s ease forwards",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        drawOutline: {
          from: { strokeDasharray: "160", strokeDashoffset: "160" },
          to: { strokeDasharray: "160", strokeDashoffset: "0" },
        },
        draw: {
          from: { strokeDasharray: "100", strokeDashoffset: "100" },
          to: { strokeDasharray: "100", strokeDashoffset: "0" },
        },
      },
      backgroundImage: {
        "glow-radial":
          "radial-gradient(circle at 20% 0%, hsl(220 95% 62% / 0.08), transparent 50%), radial-gradient(circle at 80% 100%, hsl(142 72% 46% / 0.06), transparent 50%), radial-gradient(circle at 50% 50%, hsl(0 82% 58% / 0.04), transparent 60%)",
      },
    },
  },
  plugins: [],
};

export default config;
