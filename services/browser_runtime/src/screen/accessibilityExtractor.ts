import type { Page } from "playwright";

export type AccessibilityNode = {
  role: string;
  name: string;
  depth: number;
};

export async function extractAccessibilitySignature(
  page: Page,
  maxNodes: number,
  maxDepth: number,
): Promise<AccessibilityNode[]> {
  return page.evaluate(
    ({ maxNodes: nodeCap, maxDepth: depthCap }) => {
      const nodes: AccessibilityNode[] = [];
      const roleOf = (element: Element): string =>
        element.getAttribute("role") ?? element.tagName.toLowerCase();
      const nameOf = (element: Element): string =>
        (
          element.getAttribute("aria-label") ??
          element.getAttribute("title") ??
          element.textContent
        )
          .replace(/\s+/g, " ")
          .trim()
          .slice(0, 80);
      const visit = (element: Element, depth: number): void => {
        if (nodes.length >= nodeCap || depth > depthCap) {
          return;
        }
        const style = window.getComputedStyle(element);
        if (style.display === "none" || style.visibility === "hidden") {
          return;
        }
        const role = roleOf(element);
        const name = nameOf(element);
        if (name || ["button", "a", "input", "nav"].includes(element.tagName.toLowerCase())) {
          nodes.push({ role, name, depth });
        }
        for (const child of Array.from(element.children)) {
          visit(child, depth + 1);
        }
      };
      visit(document.body, 0);
      return nodes;
    },
    { maxNodes, maxDepth },
  );
}
