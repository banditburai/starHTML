import { cpSync, rmSync } from "fs";

rmSync("src/starhtml/static/js", { recursive: true, force: true });

const result = await Bun.build({
  entrypoints: [
    // Plugins (14)
    "typescript/plugins/persist.ts",
    "typescript/plugins/scroll.ts",
    "typescript/plugins/resize.ts",
    "typescript/plugins/drag.ts",
    "typescript/plugins/canvas.ts",
    "typescript/plugins/position.ts",
    "typescript/plugins/throttle.ts",
    "typescript/plugins/smooth-scroll.ts",
    "typescript/plugins/split.ts",
    "typescript/plugins/markdown.ts",
    "typescript/plugins/katex.ts",
    "typescript/plugins/mermaid.ts",
    "typescript/plugins/motion.ts",
    "typescript/plugins/motion-svg.ts",
    // Debugger (5)
    "typescript/debugger/dom-observer.ts",
    "typescript/debugger/capture.ts",
    "typescript/debugger/signals.ts",
    "typescript/debugger/timeline.ts",
    "typescript/debugger/setup.ts",
  ],
  outdir: "src/starhtml/static/js",
  root: "typescript",
  minify: true,
  splitting: true,
  format: "esm",
  target: "browser",
  external: [
    "datastar",
    "https://cdn.jsdelivr.net/npm/@floating-ui/dom@1/+esm",
    "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js",
    "https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs",
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs",
    "https://cdn.jsdelivr.net/npm/motion@11/+esm",
    "https://cdn.jsdelivr.net/npm/flubber@0.4.2/+esm",
  ],
});

if (!result.success) {
  console.error("Build failed:");
  for (const msg of result.logs) console.error(msg);
  process.exit(1);
}

// Copy debugger CSS (not a JS module, just needs to be alongside the debugger JS)
cpSync(
  "typescript/debugger/debugger.css",
  "src/starhtml/static/js/debugger/debugger.css",
);

console.log(`Built ${result.outputs.length} files`);
