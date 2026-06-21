import { describe, expect, it, vi } from "vitest";

import { requestMicrophone, setStreamMuted, stopMediaStream } from "../lib/media/microphone";

describe("microphone helpers", () => {
  it("requests audio only when called", async () => {
    const stream = fakeStream();
    const getUserMedia = vi.fn(() => Promise.resolve(stream));
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia },
      configurable: true,
    });
    await expect(requestMicrophone()).resolves.toBe(stream);
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true, video: false });
  });

  it("mutes and stops tracks", () => {
    const track = { enabled: true, stop: vi.fn() };
    const stream = {
      getAudioTracks: () => [track],
      getTracks: () => [track],
    } as unknown as MediaStream;
    setStreamMuted(stream, true);
    expect(track.enabled).toBe(false);
    stopMediaStream(stream);
    expect(track.stop).toHaveBeenCalledTimes(1);
  });
});

function fakeStream(): MediaStream {
  return {
    getAudioTracks: () => [],
    getTracks: () => [],
  } as unknown as MediaStream;
}
