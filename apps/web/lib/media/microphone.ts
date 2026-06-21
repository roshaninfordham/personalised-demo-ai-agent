export async function requestMicrophone(): Promise<MediaStream> {
  if (typeof navigator === "undefined" || !("mediaDevices" in navigator)) {
    throw new Error("Microphone APIs are not available in this browser.");
  }
  return navigator.mediaDevices.getUserMedia({ audio: true, video: false });
}

export function stopMediaStream(stream: MediaStream): void {
  for (const track of stream.getTracks()) {
    track.stop();
  }
}

export function setStreamMuted(stream: MediaStream, muted: boolean): void {
  for (const track of stream.getAudioTracks()) {
    track.enabled = !muted;
  }
}
