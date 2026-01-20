import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
import type { AttributeContext, AttributePlugin } from "./types.js";

let initialized = false;
let diagramCounter = 0;

const processContent = (el: Element): void => {
  if (el.querySelector("svg")) return;

  if (!initialized) {
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      securityLevel: "loose",
      flowchart: { useMaxWidth: false, useMaxHeight: false },
    });
    initialized = true;
  }

  mermaid
    .render(`mermaid-diagram-${diagramCounter++}`, el.textContent || "")
    .then(({ svg, bindFunctions }) => {
      el.innerHTML = svg;
      bindFunctions?.(el);
    })
    .catch((error: Error) => {
      console.error("Error rendering Mermaid diagram:", error);
      el.innerHTML = `<p>Error rendering diagram: ${error.message}</p>`;
    });
};

const mermaidPlugin: AttributePlugin = {
  name: "mermaid",
  apply({ el }: AttributeContext) {
    processContent(el);

    // Re-process on DOM changes (morphing replaces content)
    const observer = new MutationObserver(() => {
      observer.disconnect();
      processContent(el);
      observer.observe(el, { childList: true, characterData: true, subtree: true });
    });
    observer.observe(el, { childList: true, characterData: true, subtree: true });
  },
};

export default mermaidPlugin;
