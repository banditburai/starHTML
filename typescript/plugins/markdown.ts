import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
import type { AttributeContext, AttributePlugin } from "./types.js";

const processContent = (el: Element): void => {
  if (el.querySelector("p, h1, h2, h3, ul, ol, blockquote")) return;
  el.innerHTML = marked.parse(el.textContent || "");
};

const markdownPlugin: AttributePlugin = {
  name: "markdown",
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

export default markdownPlugin;
