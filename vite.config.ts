import { defineConfig, Plugin } from 'vite'
import { copyFileSync, mkdirSync } from 'fs'

function copyDebuggerCss(): Plugin {
  return {
    name: 'copy-debugger-css',
    closeBundle() {
      mkdirSync('./src/starhtml/static/js/debugger', { recursive: true });
      copyFileSync('./typescript/debugger/debugger.css', './src/starhtml/static/js/debugger/debugger.css');
    }
  };
}

export default defineConfig({
  build: {
    lib: {
      entry: {
        // Plugins
        'plugins/persist': './typescript/plugins/persist.ts',
        'plugins/scroll': './typescript/plugins/scroll.ts',
        'plugins/resize': './typescript/plugins/resize.ts',
        'plugins/drag': './typescript/plugins/drag.ts',
        'plugins/canvas': './typescript/plugins/canvas.ts',
        'plugins/position': './typescript/plugins/position.ts',
        'plugins/throttle': './typescript/plugins/throttle.ts',
        'plugins/smooth-scroll': './typescript/plugins/smooth-scroll.ts',
        'plugins/split': './typescript/plugins/split.ts',
        'plugins/markdown': './typescript/plugins/markdown.ts',
        'plugins/katex': './typescript/plugins/katex.ts',
        'plugins/mermaid': './typescript/plugins/mermaid.ts',
        'plugins/motion': './typescript/plugins/motion.ts',
        'plugins/motion-svg': './typescript/plugins/motion-svg.ts',
        // Debugger
        'debugger/dom-observer': './typescript/debugger/dom-observer.ts',
        'debugger/capture': './typescript/debugger/capture.ts',
        'debugger/signals': './typescript/debugger/signals.ts',
        'debugger/timeline': './typescript/debugger/timeline.ts',
        'debugger/setup': './typescript/debugger/setup.ts',
      },
      formats: ['es'],
      fileName: (_format, entryName) => `${entryName}.js`
    },
    outDir: './src/starhtml/static/js',
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false,
        drop_debugger: false,
        pure_funcs: [],
        passes: 2,
        unsafe: true,
        unsafe_comps: true,
        unsafe_math: true,
        unsafe_methods: true,
        reduce_vars: true,
        collapse_vars: true,
        hoist_funs: true,
        hoist_vars: true
      },
      format: {
        comments: false,
        ascii_only: true,
        semicolons: false,
        beautify: false
      },
      mangle: {
        safari10: true,
        toplevel: true,
        eval: true,
        keep_fnames: false,
        reserved: []
      }
    },
    rollupOptions: {
      external: [
        'datastar',
        'https://cdn.jsdelivr.net/npm/@floating-ui/dom@1/+esm',
        'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js',
        'https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs',
        'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs',
        'https://cdn.jsdelivr.net/npm/motion@11/+esm',
        'https://cdn.jsdelivr.net/npm/flubber@0.4.2/+esm',
      ],
      output: {
        preserveModules: false,
        compact: true,
        generatedCode: {
          constBindings: true,
          arrowFunctions: true
        }
      }
    },
    sourcemap: false,
    emptyOutDir: true,
    reportCompressedSize: true
  },
  plugins: [copyDebuggerCss()],
  esbuild: {
    target: 'es2020',
    format: 'esm',
    legalComments: 'none',
    treeShaking: true
  }
})