export type Caption = {
  text: string;
  startMs: number;
  endMs: number;
  emphasis?: boolean;
};

export type CueEvent = {
  id: string;
  frame: number;
  component: string;
  phase: string;
  sound?: {
    path: string;
    sourcePeakMs: number;
    peakDbFS: number;
    maxDurationSeconds: number;
    fadeInMs?: number;
    fadeOutMs?: number;
  };
  audio?: {
    path: string;
    sha256: string;
    startSample: number;
    peakSample: number;
    targetSample: number;
    sampleCount: number;
    peakDbFS: number;
    fadeInMs: number;
    fadeOutMs: number;
    licenseStatus: string;
  };
  pan?: number;
};

export type Director = {
  schemaVersion: number;
  fps: number;
  sampleRate: number;
  durationInFrames: number;
  keyframes: Record<string, number>;
  events: CueEvent[];
};

export type Glyph = {
  char: string;
  cue: string;
  word: number;
  line: number;
  x: number;
  width: number;
  color?: string;
};

export const FPS = 30;
export const SAMPLES_PER_FRAME = 1600; // 48000 / 30

export const frameOf = (director: Director, id: string): number => {
  const f = director.keyframes[id];
  if (f === undefined) {
    throw new Error(`Cue mancante nel director: ${id}`);
  }
  return f;
};
