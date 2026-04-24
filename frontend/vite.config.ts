import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": new URL("./src", import.meta.url).pathname,
    },
  },

  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to Django backend in dev
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: "dist",
    sourcemap: false,
    rollupOptions: {
      output: {
        // Split vendor chunks for better caching
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          query: ["@tanstack/react-query"],
          charts: ["recharts"],
          ui: ["lucide-react", "clsx", "react-hot-toast"],
        },
      },
    },
    // Warn if chunk > 500KB
    chunkSizeWarningLimit: 500,
  },

  preview: {
    port: 3000,
  },
});
