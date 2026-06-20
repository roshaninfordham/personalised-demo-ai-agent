import type { Page } from "playwright";

export type DomSummary = {
  counts: Record<string, number>;
  landmarks: Array<{ tag: string; text: string }>;
  headings: Array<{ level: number; text: string }>;
  forms: Array<{ index: number; labels: string[]; button_labels: string[] }>;
};

export type DomExtractorOptions = {
  maxNodes: number;
  maxTextPerNode: number;
  maxArrayItems: number;
};

export async function extractDomSummary(page: Page, options: DomExtractorOptions): Promise<DomSummary> {
  return page.evaluate((opts) => {
    const textOf = (element: Element): string =>
      element.textContent.replace(/\s+/g, " ").trim().slice(0, opts.maxTextPerNode);
    const all = Array.from(document.querySelectorAll("body *")).slice(0, opts.maxNodes);
    const count = (selector: string): number => document.querySelectorAll(selector).length;
    const headings = Array.from(document.querySelectorAll("h1,h2,h3,h4,h5,h6"))
      .slice(0, opts.maxArrayItems)
      .map((element) => ({
        level: Number(element.tagName.slice(1)),
        text: textOf(element),
      }))
      .filter((item) => item.text.length > 0);
    const landmarks = Array.from(
      document.querySelectorAll("nav,main,aside,header,footer,[role='navigation']"),
    )
      .slice(0, opts.maxArrayItems)
      .map((element) => ({ tag: element.tagName.toLowerCase(), text: textOf(element) }))
      .filter((item) => item.text.length > 0);
    const forms = Array.from(document.querySelectorAll("form"))
      .slice(0, opts.maxArrayItems)
      .map((form, index) => ({
        index,
        labels: Array.from(form.querySelectorAll("label"))
          .slice(0, 10)
          .map((label) => textOf(label))
          .filter(Boolean),
        button_labels: Array.from(form.querySelectorAll("button,input[type='submit']"))
          .slice(0, 10)
          .map((button) => textOf(button) || button.getAttribute("value") || "")
          .filter(Boolean),
      }));
    return {
      counts: {
        buttons: count("button,input[type='button'],input[type='submit'],[role='button']"),
        links: count("a[href]"),
        inputs: count("input,textarea,select,[contenteditable='true']"),
        forms: count("form"),
        navs: count("nav,[role='navigation']"),
        tables: count("table,[role='table'],[role='grid']"),
        charts: all.filter((element) => /chart|graph|canvas|svg/i.test(element.getAttribute("class") ?? ""))
          .length,
        dialogs: count("dialog,[role='dialog'],[aria-modal='true']"),
      },
      landmarks,
      headings,
      forms,
    };
  }, options);
}
