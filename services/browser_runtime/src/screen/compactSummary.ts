import type { DomSummary } from "./domExtractor.js";
import type { InternalElement } from "./elementExtractor.js";

export function buildCompactSummary(input: {
  title: string;
  domSummary: DomSummary;
  elements: InternalElement[];
}): string {
  const counts = input.domSummary.counts;
  const navLabels = input.elements
    .filter((element) => element.role === "navigation" || element.role === "link")
    .map((element) => element.label)
    .filter(Boolean)
    .slice(0, 5);
  const headings = input.domSummary.headings.map((heading) => heading.text).slice(0, 5);
  const parts = [
    `Page titled '${input.title || "Untitled"}'.`,
    `Visible UI includes ${String(counts.buttons ?? 0)} buttons, ${String(counts.links ?? 0)} links, ${String(counts.inputs ?? 0)} inputs, ${String(counts.forms ?? 0)} forms.`,
  ];
  if (navLabels.length > 0) {
    parts.push(`Navigation includes ${navLabels.join(", ")}.`);
  }
  if (headings.length > 0) {
    parts.push(`Main headings: ${headings.join(", ")}.`);
  }
  return parts.join(" ").slice(0, 1000);
}

