import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  // 5173 is taken by another project on this machine: a fixed port avoids opening the wrong page.
  server: { port: 5180, strictPort: true, fs: { allow: [".."] } },
});
