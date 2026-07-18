export type EventItem = { step: number; kind: string; entityId: string; reasons: string[]; metrics: Record<string, number> };
export type Cell = { id: string; organism_id: string; prototype: number[]; energy: number; utility: number; activation: number; age_steps: number; redundancy: number };
export type Organism = { id: string; lineage: string; color: string; cellIds: string[]; energy: number; utility: number; contribution: number; colonyId: string | null; ageSteps: number; x: number; y: number };
export type Colony = { id: string; member_ids: string[]; core_members: string[]; energy: number; state: string; formed_step: number; synergy: number };
export type State = {
  seed: number;
  stepCount: number;
  stateHash: string;
  currentStimulus: { id: string; rotation: number; noise: number; occlusion: number; visualShape: string } | null;
  metrics: { loss: number; meanLoss: number; activeCells: number; activeOrganisms: number; activeColonies: number; activeSynapsesProxy: number; memoryBytesProxy: number; resourceScore: number; events: number };
  cells: Cell[];
  organisms: Organism[];
  colonies: Colony[];
  events: EventItem[];
};
export type Evaluation = { modelModified: boolean; sampleCount: number; purity: number; communities: { organismId: string; dominantHiddenLabel: string; samples: number }[]; note: string };
export type Ablation = { organismId: string; modelModified: boolean; baselineLoss: number; ablatedLoss: number; delta: number; note: string };
