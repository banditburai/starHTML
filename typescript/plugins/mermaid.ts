import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
import type { AttributeContext, AttributePlugin } from "./types.js";

let initialized = false;
let diagramCounter = 0;

const renderDiagram = (el: Element): void => {
  mermaid
    .render(`mermaid-diagram-${diagramCounter++}`, el.textContent || "")
    .then(({ svg, bindFunctions }) => {
      el.innerHTML = svg;
      bindFunctions?.(el);
    })
    .catch((error: Error) => {
      console.error("Error rendering Mermaid diagram:", error);
      el.setAttribute("data-mermaid-error", "true");
      el.innerHTML = `<p style="color:#666;font-style:italic;">Error rendering diagram</p>`;
    });
};

const processContent = (el: Element): void => {
  // Skip if already processed (has svg or error marker)
  if (el.querySelector("svg") || el.hasAttribute("data-mermaid-error")) return;

  if (!initialized) {
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      securityLevel: "loose",
      flowchart: { useMaxWidth: true, htmlLabels: true, curve: "basis" },
    });
    initialized = true;
  }

  // Defer render until element has dimensions (helps with iframes/hidden containers)
  if (el.clientWidth === 0) {
    requestAnimationFrame(() => processContent(el));
    return;
  }

  renderDiagram(el);
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
