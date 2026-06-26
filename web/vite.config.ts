import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Project site is served at https://lexes7.github.io/GeoStream-Atlas/
export default defineConfig({
  plugins: [react()],
  base: "/GeoStream-Atlas/",
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom"],
          leaflet: ["leaflet", "react-leaflet"],
          charts: ["chart.js", "react-chartjs-2", "chartjs-plugin-annotation", "chartjs-adapter-date-fns", "date-fns"],
          motion: ["framer-motion"],
        },
      },
    },
  },
});
