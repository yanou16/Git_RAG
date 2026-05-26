/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    /* ── Cohere radius scale (overrides defaults) ── */
    borderRadius: {
      DEFAULT: "4px",
      sm:   "8px",
      md:   "16px",
      lg:   "22px",
      xl:   "30px",
      pill: "32px",
      full: "9999px",
    },
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "Inter", "ui-sans-serif", "system-ui"],
        sans:    ["Inter", "Arial", "ui-sans-serif", "system-ui"],
        mono:    ["JetBrains Mono", "Arial", "ui-monospace"],
      },
      colors: {
        /* Cohere palette */
        "c-primary":    "#17171c",
        "c-black":      "#000000",
        "c-ink":        "#212121",
        "c-green":      "#003c33",
        "c-navy":       "#071829",
        "c-canvas":     "#ffffff",
        "c-stone":      "#eeece7",
        "c-pale-green": "#edfce9",
        "c-pale-blue":  "#f1f5ff",
        "c-hairline":   "#d9d9dd",
        "c-border":     "#e5e7eb",
        "c-card":       "#f2f2f2",
        "c-muted":      "#93939f",
        "c-slate":      "#75758a",
        "c-body-muted": "#616161",
        "c-action":     "#1863dc",
        "c-focus":      "#4c6ee6",
        "c-coral":      "#ff7759",
        "c-coral-soft": "#ffad9b",
        "c-error":      "#b30000",
      },
      letterSpacing: {
        "hero":    "-0.02em",
        "display": "-0.015em",
        "tight":   "-0.01em",
        "mono":    "0.02em",
      },
      lineHeight: {
        "none": "1",
        "snug": "1.2",
      },
    },
  },
  plugins: [],
};
