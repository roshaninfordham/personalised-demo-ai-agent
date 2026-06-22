import type { Page } from "playwright";
import type { BoundingBox, ElementRole, UIElement } from "@live-demo-agent/contracts";

export type InternalElement = UIElement & {
  tagName: string;
  inputType: string | undefined;
  href: string | undefined;
  placeholder: string | undefined;
  ariaLabel: string | undefined;
  text: string | undefined;
  surroundingText: string;
  selectorHint: string;
  elementFingerprint: string;
};

type RawElement = Omit<InternalElement, "element_id" | "risk_level" | "confidence" | "elementFingerprint">;

const selectors = [
  "button",
  "a[href]",
  "input",
  "textarea",
  "select",
  "[role]",
  "[tabindex]",
  "summary",
  "details",
  "label",
  "form",
  "nav",
  "[contenteditable='true']",
].join(",");

export async function extractRawElements(page: Page, maxElements: number): Promise<RawElement[]> {
  const raw = await page.evaluate(
    ({ candidateSelector, max }) => {
      const normalize = (value: string | null | undefined): string =>
        (value ?? "").replace(/\s+/g, " ").trim();
      const roleOf = (element: Element): ElementRole => {
        const explicit = element.getAttribute("role");
        const tag = element.tagName.toLowerCase();
        const inputType = (element.getAttribute("type") ?? "").toLowerCase();
        if (explicit === "button" || tag === "button" || inputType === "button" || inputType === "submit") {
          return "button";
        }
        if (tag === "a") return "link";
        if (tag === "textarea") return "textarea";
        if (tag === "select") return "select";
        if (inputType === "checkbox") return "checkbox";
        if (inputType === "radio") return "radio";
        if (tag === "input" || element.getAttribute("contenteditable") === "true") return "input";
        if (tag === "nav" || explicit === "navigation") return "navigation";
        if (explicit === "tab") return "tab";
        if (explicit === "dialog" || tag === "dialog") return "modal";
        return "unknown";
      };
      const labelOf = (element: Element): string => {
        const aria = element.getAttribute("aria-label");
        const labelledBy = element.getAttribute("aria-labelledby");
        const labelledText = labelledBy
          ? labelledBy
              .split(/\s+/)
              .map((id) => document.getElementById(id)?.textContent ?? "")
              .join(" ")
          : "";
        const ariaReferenceText = labelledText.length > 0 ? labelledText : null;
        const inputLabels =
          "labels" in element
            ? Array.from((element as HTMLInputElement).labels ?? [])
                .map((label) => label.textContent ?? "")
                .join(" ")
            : "";
        const wrappedLabel =
          element.closest("label") !== null ? element.closest("label")?.textContent ?? "" : "";
        const placeholder = element.getAttribute("placeholder");
        const value = element.getAttribute("value");
        const candidates = [
          aria,
          ariaReferenceText,
          inputLabels,
          wrappedLabel,
          placeholder,
          value,
          element.textContent,
        ];
        for (const candidate of candidates) {
          const normalized = normalize(candidate);
          if (normalized.length > 0) return normalized;
        }
        return "";
      };
      return Array.from(document.querySelectorAll(candidateSelector))
        .slice(0, max)
        .map((element, index) => {
          element.setAttribute("data-live-demo-agent-el-index", String(index));
          const rect = element.getBoundingClientRect();
          const style = window.getComputedStyle(element);
          const visible =
            rect.width >= 4 &&
            rect.height >= 4 &&
            style.visibility !== "hidden" &&
            style.display !== "none";
          const tagName = element.tagName.toLowerCase();
          const htmlElement = element as HTMLElement;
          const disabled =
            (element as HTMLButtonElement | HTMLInputElement).disabled ||
            element.getAttribute("aria-disabled") === "true";
          const label = labelOf(element);
          const parentText = normalize(element.parentElement?.textContent).slice(0, 300);
          return {
            role: roleOf(element),
            label,
            tagName,
            inputType: element.getAttribute("type") ?? undefined,
            href: element.getAttribute("href") ?? undefined,
            placeholder: element.getAttribute("placeholder") ?? undefined,
            ariaLabel: element.getAttribute("aria-label") ?? undefined,
            text: normalize(element.textContent),
            surroundingText: parentText,
            selectorHint: `[data-live-demo-agent-el-index="${String(index)}"]`,
            bbox: {
              x: Math.round(rect.x),
              y: Math.round(rect.y),
              width: Math.round(rect.width),
              height: Math.round(rect.height),
            },
            visible,
            enabled: !disabled && htmlElement.isConnected,
          };
        })
        .filter((element) => element.visible || element.role !== "unknown");
    },
    { candidateSelector: selectors, max: maxElements },
  );
  return raw.sort(compareRawElements);
}

export function toPublicElement(element: InternalElement): UIElement {
  return {
    element_id: element.element_id,
    role: element.role,
    label: element.label,
    bbox: element.bbox,
    visible: element.visible,
    enabled: element.enabled,
    risk_level: element.risk_level,
    confidence: element.confidence,
  };
}

function compareRawElements(left: RawElement, right: RawElement): number {
  return (
    left.bbox.y - right.bbox.y ||
    left.bbox.x - right.bbox.x ||
    rolePriority(left.role) - rolePriority(right.role) ||
    left.label.localeCompare(right.label)
  );
}

function rolePriority(role: ElementRole): number {
  const order: ElementRole[] = [
    "button",
    "link",
    "input",
    "textarea",
    "select",
    "checkbox",
    "radio",
    "navigation",
    "tab",
    "modal",
    "unknown",
  ];
  return order.indexOf(role);
}

export function bboxCenter(bbox: BoundingBox): { x: number; y: number } {
  return { x: bbox.x + bbox.width / 2, y: bbox.y + bbox.height / 2 };
}
