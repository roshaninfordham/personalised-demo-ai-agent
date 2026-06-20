import type { ScreenState } from "@live-demo-agent/contracts";

export type ScreenDiff = {
  urlChanged: boolean;
  hashChanged: boolean;
  elementJaccardDistance: number;
};

export function diffScreens(before: ScreenState | undefined, after: ScreenState): ScreenDiff {
  if (before === undefined) {
    return { urlChanged: true, hashChanged: true, elementJaccardDistance: 1 };
  }
  const beforeSet = new Set(before.elements.map((element) => element.element_id));
  const afterSet = new Set(after.elements.map((element) => element.element_id));
  return {
    urlChanged: before.url !== after.url,
    hashChanged: before.screen_hash !== after.screen_hash,
    elementJaccardDistance: jaccardDistance(beforeSet, afterSet),
  };
}

export function jaccardDistance(left: Set<string>, right: Set<string>): number {
  if (left.size === 0 && right.size === 0) {
    return 0;
  }
  const intersection = [...left].filter((item) => right.has(item)).length;
  const union = new Set([...left, ...right]).size;
  return 1 - intersection / union;
}

