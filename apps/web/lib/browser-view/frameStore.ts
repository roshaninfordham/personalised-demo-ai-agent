export type BrowserFrameMode = "screenshot" | "video" | "webrtc";

export type BrowserFrameState = {
  screenId: string;
  screenHash: string;
  imageUrl: string | null;
  width: number;
  height: number;
  title?: string;
  url?: string;
  updatedAt: string;
  stale: boolean;
};

export class FrameStore {
  private current: BrowserFrameState | null = null;
  private preloaded: string | null = null;

  setFrame(frame: BrowserFrameState): void {
    this.preloaded = this.current?.imageUrl ?? null;
    this.current = frame;
  }

  getFrame(): BrowserFrameState | null {
    return this.current;
  }

  retainedImageUrls(): string[] {
    return [this.current?.imageUrl, this.preloaded].filter((value): value is string => value !== null);
  }
}
