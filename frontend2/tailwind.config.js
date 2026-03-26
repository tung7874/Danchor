/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0D0D0D",
        surface: "#1A1A1A",
        border: "#2A2A2A",
        primary: "#00D4FF",
        positive: "#00C851",
        negative: "#FF4444",
        warning: "#FFB800",
        muted: "#666666",
      },
    },
  },
  plugins: [],
};
