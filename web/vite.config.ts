import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// 개발 중에는 Flask 개발 서버(5000)로 API 와 Socket.IO 를 넘긴다.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/socket.io": { target: "http://127.0.0.1:5000", ws: true },
    },
  },
  test: {
    environment: "jsdom",
  },
});
