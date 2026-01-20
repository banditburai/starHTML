import katex from "https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs";
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
import type { AttributeContext, AttributePlugin } from "./types.js";

const renderMath = (tex: string, displayMode: boolean): string =>
  katex.renderToString(tex, { throwOnError: false, displayMode, output: "html", trust: true });

const processContent = (el: Element): void => {
  if (el.querySelector(".katex")) return;

  let content = el.textContent || "";

  // Display math: \[...\] or $$...$$
  content = content.replace(/\\\[([\s\S]+?)\\\]/gm, (_, tex) => renderMath(tex.trim(), true));
  content = content.replace(/\$\$([\s\S]+?)\$\$/gm, (_, tex) => renderMath(tex.trim(), true));

  // Inline math: \(...\) or $...$
  content = content.replace(/\\\(([\s\S]+?)\\\)/g, (_, tex) => renderMath(tex.trim(), false));
  content = content.replace(/(?<!\w)\$([^\$\s](?:[^\$]*[^\$\s])?)\$(?!\w)/g, (_, tex) =>
    renderMath(tex.trim(), false)
  );

  el.innerHTML = marked.parse(content);
};

const katexPlugin: AttributePlugin = {
  name: "katex",
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

export default katexPlugin;
