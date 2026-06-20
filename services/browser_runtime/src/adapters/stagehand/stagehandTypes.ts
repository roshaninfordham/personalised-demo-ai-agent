export type StagehandContext = {
  browserSessionId: string;
  screenId?: string;
};

export type StagehandObservation = {
  label: string;
  confidence: number;
};

export type StagehandActionResult = {
  proposedAction: string;
  confidence: number;
};

