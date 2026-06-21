export type AudioLevelMeter = {
  start(onLevel: (level: number) => void): void;
  stop(): void;
};

export function createAudioLevelMeter(stream: MediaStream): AudioLevelMeter {
  let context: AudioContext | null = null;
  let frame = 0;
  return {
    start(onLevel) {
      context = new AudioContext();
      const source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 1024;
      source.connect(analyser);
      const data = new Uint8Array(analyser.fftSize);
      const tick = (): void => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (const value of data) {
          const centered = (value - 128) / 128;
          sum += centered * centered;
        }
        onLevel(Math.max(0, Math.min(1, Math.sqrt(sum / data.length) * 4)));
        frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    },
    stop() {
      cancelAnimationFrame(frame);
      void context?.close();
      context = null;
    },
  };
}
