/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#090d16",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155"
        },
        brand: {
          green: "#2ecc71",
          blue: "#3498db",
          yellow: "#f1c40f",
          orange: "#e67e22",
          purple: "#9b59b6"
        }
      }
    },
  },
  plugins: [],
}
