import "@testing-library/jest-dom/vitest";

class TestResizeObserver {
  observe(): void {
    // jsdom does not compute layout; tests only need the API surface.
  }

  unobserve(): void {
    // no-op
  }

  disconnect(): void {
    // no-op
  }
}

Object.defineProperty(globalThis, "ResizeObserver", {
  value: TestResizeObserver,
  writable: true,
});

Object.defineProperty(globalThis, "requestAnimationFrame", {
  value: (callback: FrameRequestCallback): number =>
    window.setTimeout(() => {
      callback(performance.now());
    }, 16),
  writable: true,
});

Object.defineProperty(globalThis, "cancelAnimationFrame", {
  value: (id: number): void => {
    window.clearTimeout(id);
  },
  writable: true,
});
