// react, react-dom, vite: the same three Top-of-Mind already uses.
// JSX is compiled by vite's built-in esbuild; no React plugin needed.
import { defineConfig } from "vite";

export default defineConfig({
  esbuild: { jsx: "automatic" },
  server: { proxy: { "/api": "http://127.0.0.1:2828" } },
});
