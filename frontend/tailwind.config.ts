import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        saffron: { DEFAULT: "#FF9933", dark: "#E8881F" },
        green: { DEFAULT: "#138808", dark: "#0F6A06" },
        navy: { DEFAULT: "#1A237E", light: "#283593" },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
