/**
 * Type declarations for CDN modules (resolved at runtime).
 */

declare module "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js" {
  export function parse(src: string): string;
  export const marked: { parse: typeof parse };
}

declare module "https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs" {
  interface RenderOptions {
    throwOnError?: boolean;
    displayMode?: boolean;
    output?: "html" | "mathml" | "htmlAndMathml";
    trust?: boolean;
  }
  export function renderToString(tex: string, options?: RenderOptions): string;
  const katex: { renderToString: typeof renderToString };
  export default katex;
}

declare module "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs" {
  interface MermaidConfig {
    startOnLoad?: boolean;
    theme?: string;
    securityLevel?: string;
    flowchart?: {
      useMaxWidth?: boolean;
      useMaxHeight?: boolean;
      htmlLabels?: boolean;
      curve?: string;
    };
  }
  export function initialize(config: MermaidConfig): void;
  export function render(
    id: string,
    definition: string
  ): Promise<{ svg: string; bindFunctions?: (el: Element) => void }>;
  const mermaid: { initialize: typeof initialize; render: typeof render };
  export default mermaid;
}
