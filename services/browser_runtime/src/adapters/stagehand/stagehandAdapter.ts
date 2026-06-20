import { BrowserRuntimeError } from "../../errors.js";
import type { StagehandActionResult, StagehandContext, StagehandObservation } from "./stagehandTypes.js";

export class DisabledStagehandAdapter {
  observe(instruction: string, context: StagehandContext): Promise<StagehandObservation[]> {
    void instruction;
    void context;
    return Promise.resolve([]);
  }

  extract<T>(instruction: string, schema: unknown, context: StagehandContext): Promise<T> {
    void instruction;
    void schema;
    void context;
    return Promise.reject(new BrowserRuntimeError("stagehand_disabled", "Stagehand is disabled.", 501));
  }

  act(instruction: string, context: StagehandContext): Promise<StagehandActionResult> {
    void instruction;
    void context;
    return Promise.reject(
      new BrowserRuntimeError(
        "stagehand_hot_path_blocked",
        "Stagehand cannot execute hot-path actions in Phase 5.",
        403,
      ),
    );
  }
}
