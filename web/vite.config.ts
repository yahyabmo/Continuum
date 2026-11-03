import { appendFileSync, mkdirSync } from "node:fs";
import { defineConfig, type Plugin } from "vite";

const JOURNAL = new URL("../data/journal/web.jsonl", import.meta.url);

/** In development, the page writes its measures and errors to a file that can be read back. */
function journal(): Plugin {
  return {
    name: "continuum-journal",
    configureServer(server) {
      server.middlewares.use("/__journal", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end();
          return;
        }
        let body = "";
        req.on("data", (chunk) => {
          body += chunk;
        });
        req.on("end", () => {
          try {
            const entry = { time: new Date().toISOString(), ...JSON.parse(body) };
            mkdirSync(new URL(".", JOURNAL), { recursive: true });
            appendFileSync(JOURNAL, `${JSON.stringify(entry)}\n`);
            res.statusCode = 204;
          } catch {
            res.statusCode = 400;
          }
          res.end();
        });
      });
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [journal()],
  // 5173 is taken by another project on this machine: a fixed port avoids opening the wrong page.
  server: { port: 5180, strictPort: true, fs: { allow: [".."] } },
});
