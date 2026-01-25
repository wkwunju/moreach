import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0e1116",
        glow: "#f7f0e8",
        tide: "#c9d8ff",
        moss: "#0f4c5c",
        clay: "#f6b47b",
        ember: "#eb6a4a"
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        serif: ["'Fraunces'", "serif"]
      },
      keyframes: {
        floatUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" }
        }
      },
      animation: {
        floatUp: "floatUp 0.8s ease-out",
        pulseSoft: "pulseSoft 2.4s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

export default config;
