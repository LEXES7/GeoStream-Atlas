import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Project site is served at https://lexes7.github.io/GeoStream-Atlas/
export default defineConfig({
  plugins: [react()],
  base: "/GeoStream-Atlas/",
});
