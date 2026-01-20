import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    lib: {
      entry: {
        'persist': './typescript/plugins/persist.ts',
        'scroll': './typescript/plugins/scroll.ts',
        'resize': './typescript/plugins/resize.ts',
        'drag': './typescript/plugins/drag.ts',
        'canvas': './typescript/plugins/canvas.ts',
        'position': './typescript/plugins/position.ts',
        'throttle': './typescript/plugins/throttle.ts',
        'smooth-scroll': './typescript/plugins/smooth-scroll.ts',
        'split': './typescript/plugins/split.ts',
        'markdown': './typescript/plugins/markdown.ts',
        'katex': './typescript/plugins/katex.ts',
        'mermaid': './typescript/plugins/mermaid.ts',        
      },
      formats: ['es'],
      fileName: (format, entryName) => `${entryName}.js`
    },
    outDir: './src/starhtml/static/js/plugins',
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
        'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js',
        'https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs',
        'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs',
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
  esbuild: {
    target: 'es2020',
    format: 'esm',
    legalComments: 'none',
    treeShaking: true
  }
})