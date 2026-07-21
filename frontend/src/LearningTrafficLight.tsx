import { useEffect, useMemo, useState } from 'react';
import type { Evaluation, State } from './types';

type SignalSample = {
  step: number;
  meanLoss: number;
  food: number;
  cells: number;
  organisms: number;
  microSignatures: number;
  colonies: number;
  memories: number;
};

type SignalPhase = 'discovering' | 'digesting' | 'digested';

const HISTORY_LIMIT = 40;
const OBSERVATION_WINDOW_STEPS = 288;
const MIN_CALIBRATED_SPAN = 192;

function clamp(value: number, minimum = 0, maximum = 1) {
  return Math.max(minimum, Math.min(maximum, value));
}

function average(values: number[]) {
  return values.reduce((total, value) => total + value, 0) / Math.max(1, values.length);
}

function sampleFrom(state: State): SignalSample {
  return {
    step: state.stepCount,
    meanLoss: state.metrics.meanLoss,
    food: state.metrics.currentMicroFood,
    cells: state.metrics.residentCells,
    organisms: state.metrics.residentOrganisms,
    microSignatures: state.metrics.microSignatures,
    colonies: state.metrics.activeColonies,
    memories: state.metrics.consolidatedMemories,
  };
}

function deriveSignal(history: SignalSample[]) {
  const latest = history.at(-1);
  if (!latest) {
    return { phase: 'discovering' as SignalPhase, score: 0, calibrated: false, span: 0, food: 0, meanLoss: 0, growthRate: null as number | null };
  }

  const windowStart = latest.step - OBSERVATION_WINDOW_STEPS;
  const recent = history.filter((sample) => sample.step >= windowStart);
  const first = recent[0] ?? latest;
  const span = latest.step - first.step;
  const calibrated = recent.length >= 3 && span >= MIN_CALIBRATED_SPAN;
  const batches = Math.max(1, span / 96);
  const growthUnits = Math.max(0, latest.cells - first.cells) * 3
    + Math.max(0, latest.organisms - first.organisms) * 4
    + Math.max(0, latest.microSignatures - first.microSignatures) * 0.45
    + Math.max(0, latest.colonies - first.colonies) * 2;
  const growthRate = calibrated ? growthUnits / batches : null;
  const food = average(recent.map((sample) => sample.food));
  const meanLoss = average(recent.map((sample) => sample.meanLoss));

  const maturityScore = clamp(latest.memories / 5);
  const lossScore = clamp((0.075 - meanLoss) / 0.025);
  const foodScore = clamp((0.55 - food) / 0.35);
  const structureScore = growthRate === null ? 0.35 : clamp((1.75 - growthRate) / 1.4);
  const score = Math.round((maturityScore * 0.25 + lossScore * 0.25 + foodScore * 0.25 + structureScore * 0.25) * 100);

  const streamDigested = calibrated
    && latest.step >= 480
    && latest.memories >= 3
    && meanLoss <= 0.061
    && food <= 0.38
    && growthRate !== null
    && growthRate <= 0.75;

  let phase: SignalPhase = 'digesting';
  if (latest.step < 192 || latest.memories === 0) phase = 'discovering';
  if (streamDigested) phase = 'digested';

  return { phase, score, calibrated, span, food, meanLoss, growthRate };
}

const COPY: Record<SignalPhase, { eyebrow: string; title: string; body: string }> = {
  discovering: {
    eyebrow: 'HUNGRY · DISCOVERING',
    title: 'Novel information is still feeding new structure.',
    body: 'Cells, organisms, and micro-signatures are still being recruited to digest the retinal stream.',
  },
  digesting: {
    eyebrow: 'DIGESTING · CONSOLIDATING',
    title: 'The ecosystem is forming stable memories.',
    body: 'Residual novelty or recent structural growth remains. The signal stays amber while the evidence window matures.',
  },
  digested: {
    eyebrow: 'CURRENT STREAM DIGESTED',
    title: 'Little food remains for additional growth.',
    body: 'Recent inputs are being absorbed with low residual novelty and almost no new structure. The architecture appears saturated on this stream.',
  },
};

export function LearningTrafficLight({ state, evaluation }: { state: State; evaluation: Evaluation | null }) {
  const [history, setHistory] = useState<SignalSample[]>([]);

  useEffect(() => {
    setHistory((current) => {
      const next = sampleFrom(state);
      const last = current.at(-1);
      if (state.stepCount === 0 || (last && state.stepCount < last.step)) return state.stepCount === 0 ? [] : [next];
      if (last?.step === next.step) return [...current.slice(0, -1), next];
      return [...current, next].slice(-HISTORY_LIMIT);
    });
  }, [state.stateHash, state.stepCount]);

  const signal = useMemo(() => deriveSignal(history), [history]);
  const copy = COPY[signal.phase];
  const evaluatorConfirmed = evaluation !== null && evaluation.purity >= 0.9;

  return <section className={`learning-signal signal-${signal.phase}`} aria-live="polite">
    <div className="traffic-lights" aria-label={`Learning signal: ${copy.eyebrow.toLowerCase()}`}>
      <i className={signal.phase === 'discovering' ? 'active' : ''} data-light="red" />
      <i className={signal.phase === 'digesting' ? 'active' : ''} data-light="amber" />
      <i className={signal.phase === 'digested' ? 'active' : ''} data-light="green" />
    </div>
    <div className="learning-signal-copy">
      <span>{copy.eyebrow}</span>
      <strong>{copy.title}</strong>
      <p>{copy.body}</p>
      <small>Green is ecological saturation on recent unlabeled inputs—not proof of generalization. Confirm with Hidden evaluation and the Research Auditor.</small>
    </div>
    <div className="learning-signal-readout">
      <div className="saturation-score"><span>Ecological saturation</span><strong>{signal.score}%</strong><i><b style={{ width: `${signal.score}%` }} /></i></div>
      <dl>
        <div><dt>Fine-detail food</dt><dd>{signal.food.toFixed(3)}</dd></div>
        <div><dt>Mean residual loss</dt><dd>{signal.meanLoss.toFixed(4)}</dd></div>
        <div><dt>Structural growth</dt><dd>{signal.growthRate === null ? 'calibrating' : `+${signal.growthRate.toFixed(2)} / 96 steps`}</dd></div>
        <div><dt>Evidence window</dt><dd>{signal.calibrated ? `${signal.span} steps` : `${signal.span}/${MIN_CALIBRATED_SPAN} steps`}</dd></div>
      </dl>
      <span className={`evaluation-confirmation ${evaluatorConfirmed ? 'confirmed' : ''}`}>{evaluatorConfirmed ? `✓ Hidden evaluator confirms ${Math.round(evaluation.purity * 100)}% purity` : 'Hidden evaluator confirmation pending'}</span>
    </div>
  </section>;
}
