import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api';
import type { Ablation, Evaluation, Organism, State } from './types';

const INITIAL_STATE: State = {
  seed: 20260718, stepCount: 0, stateHash: 'awaiting-api', currentStimulus: null,
  metrics: { loss: 0, meanLoss: 0, activeCells: 0, activeOrganisms: 0, activeColonies: 0, activeSynapsesProxy: 0, memoryBytesProxy: 0, resourceScore: 0, events: 0 },
  cells: [], organisms: [], colonies: [], events: [],
};

function ShapeGlyph({ shape }: { shape?: string }) {
  if (shape === 'triangle') return <polygon points="50,14 88,82 12,82" />;
  if (shape === 'square') return <rect x="20" y="20" width="60" height="60" rx="3" />;
  return <circle cx="50" cy="50" r="31" />;
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <article className="metric"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</article>;
}

export default function App() {
  const [state, setState] = useState<State>(INITIAL_STATE);
  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState(12);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [ablation, setAblation] = useState<Ablation | null>(null);
  const [notice, setNotice] = useState('Connect to the learning engine to begin.');

  const refresh = useCallback(async () => {
    try { setState(await api.state()); setNotice(''); } catch { setNotice('API unavailable. Start the FastAPI service to connect the ecosystem.'); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => { void api.step(speed).then(setState).catch(() => { setRunning(false); setNotice('Training paused because the API is unavailable.'); }); }, 650);
    return () => window.clearInterval(timer);
  }, [running, speed]);

  const selected = useMemo(() => state.organisms.find((organism) => organism.id === selectedId) ?? state.organisms[0], [state.organisms, selectedId]);
  const cellsByOrganism = useMemo(() => state.cells.reduce<Record<string, number>>((counts, cell) => ({ ...counts, [cell.organism_id]: (counts[cell.organism_id] ?? 0) + 1 }), {}), [state.cells]);

  async function trainOnce() {
    try { setState(await api.step(speed)); setNotice(''); } catch { setNotice('Unable to reach the learning engine.'); }
  }
  async function reset() {
    setRunning(false); setEvaluation(null); setAblation(null); setState(await api.reset(20260718)); setSelectedId(null); setNotice('The ecosystem was reset to zero learned structure.');
  }
  async function revealEvaluation() { setEvaluation(await api.evaluate()); }
  async function runAblation(organism: Organism) { setAblation(await api.ablate(organism.id)); }

  return <main>
    <nav><div className="brand"><i>◌</i><span>COLONY<span>MIND</span></span></div><div className="nav-copy">SELF-ORGANIZING VISION <b>•</b> BUILD WEEK 2026</div><button className="outline" onClick={() => void reset()}>Reset ecosystem</button></nav>
    <section className="hero">
      <div><p className="eyebrow">A RESOURCE-AWARE LEARNING LAB</p><h1>Watch a vision architecture <em>organize itself.</em></h1><p className="lede">Unlabeled shapes enter as information. Cells become organisms. Organisms form colonies only when cooperation earns its computational cost.</p><div className="hero-actions"><button className="primary" onClick={() => setRunning((value) => !value)}>{running ? 'Pause learning' : 'Start learning'}</button><button className="secondary" onClick={() => void trainOnce()}>Advance {speed} steps</button><select value={speed} onChange={(event) => setSpeed(Number(event.target.value))} aria-label="Training batch size"><option value={4}>4 steps</option><option value={12}>12 steps</option><option value={36}>36 steps</option><option value={96}>96 steps</option></select></div></div>
      <div className="hero-orbit"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="hero-node">0<br/><small>fixed layers</small></div><span className="shape triangle">△</span><span className="shape circle">○</span><span className="shape square">□</span></div>
    </section>
    {notice && <p className="notice">{notice}</p>}
    <section className="metrics"><Metric label="Unsupervised loss" value={state.metrics.loss.toFixed(4)} hint="lower is better"/><Metric label="Active cells" value={state.metrics.activeCells}/><Metric label="Organism experts" value={state.metrics.activeOrganisms}/><Metric label="Colonies" value={state.metrics.activeColonies}/><Metric label="Resource score" value={state.metrics.resourceScore.toFixed(3)} hint="benefit − proxy cost"/><Metric label="State hash" value={state.stateHash}/></section>
    <section className="workspace">
      <aside className="panel input-panel"><p className="panel-title">Information stream</p><div className="shape-card"><svg viewBox="0 0 100 100" className={state.currentStimulus?.visualShape ?? 'empty'}><ShapeGlyph shape={state.currentStimulus?.visualShape}/></svg><div><strong>{state.currentStimulus ? 'Unlabeled visual stimulus' : 'Waiting for first stimulus'}</strong><span>{state.currentStimulus ? `rotation ${state.currentStimulus.rotation} · noise ${state.currentStimulus.noise}` : 'The learner begins with zero cells.'}</span></div></div><dl><div><dt>Labels used in training</dt><dd>Never</dd></div><div><dt>Current step</dt><dd>{state.stepCount}</dd></div><div><dt>Occlusion</dt><dd>{state.currentStimulus?.occlusion ?? 0}</dd></div></dl><div className="rule"><b>Resource rule</b><span>A new structure must reduce error enough to cover its active compute and memory proxy.</span></div></aside>
      <section className="panel ecosystem"><div className="panel-header"><div><p className="panel-title">Living architecture</p><span>Click an organism to inspect its contribution.</span></div><span className="seed">seed {state.seed}</span></div><svg viewBox="0 0 100 100" className="ecosystem-svg" role="img" aria-label="ColonyMind learning ecosystem">
        <defs><radialGradient id="glow"><stop stopColor="#64d9ff" stopOpacity=".8"/><stop offset="1" stopColor="#64d9ff" stopOpacity="0"/></radialGradient></defs>
        {state.colonies.map((colony) => { const members = state.organisms.filter((organism) => colony.member_ids.includes(organism.id)); const x = members.reduce((sum, item) => sum + item.x, 0) / Math.max(1, members.length); const y = members.reduce((sum, item) => sum + item.y, 0) / Math.max(1, members.length); return <g key={colony.id}><circle className="colony-ring" cx={x} cy={y} r={18 + members.length * 3}/><text x={x} y={y - 20 - members.length * 3}>{colony.id}</text></g>; })}
        {state.organisms.map((organism) => <g key={organism.id} className="organism" onClick={() => setSelectedId(organism.id)}><circle cx={organism.x} cy={organism.y} r="12" fill="url(#glow)" opacity=".35"/><circle cx={organism.x} cy={organism.y} r="6" fill={organism.color} className={selected?.id === organism.id ? 'selected' : ''}/>{Array.from({ length: cellsByOrganism[organism.id] ?? 0 }).map((_, index) => <circle key={index} cx={organism.x + Math.cos(index * 2.1) * 9} cy={organism.y + Math.sin(index * 2.1) * 9} r="1.5" fill={organism.color}/>)}</g>)}
        {!state.organisms.length && <text className="empty-text" x="50" y="50">Start from zero</text>}
      </svg><div className="legend"><span><i className="dot cyan"/>cell</span><span><i className="dot violet"/>organism</span><span><i className="ring"/>persistent colony</span></div></section>
      <aside className="panel inspector"><p className="panel-title">Selected organism</p>{selected ? <><div className="organism-heading"><i style={{ background: selected.color }}/><div><strong>{selected.id}</strong><span>lineage {selected.lineage}</span></div></div><dl><div><dt>Cells</dt><dd>{cellsByOrganism[selected.id] ?? 0}</dd></div><div><dt>Energy</dt><dd>{Math.round(selected.energy * 100)}%</dd></div><div><dt>Marginal contribution</dt><dd>{selected.contribution.toFixed(4)}</dd></div><div><dt>Colony</dt><dd>{selected.colonyId ?? 'independent'}</dd></div></dl><button className="secondary full" onClick={() => void runAblation(selected)}>Run read-only ablation</button>{ablation?.organismId === selected.id && <div className="ablation"><b>Evidence</b><span>Loss changes by {ablation.delta.toFixed(4)} when {selected.id} is removed.</span><small>{ablation.modelModified ? 'Warning: state changed' : 'Live state preserved'}</small></div>}</> : <p className="empty-copy">An organism inspector will appear after the first unlabeled stimulus creates a pioneer cell.</p>}</aside>
    </section>
    <section className="lower-grid"><article className="panel evidence"><div className="panel-header"><div><p className="panel-title">Hidden evaluation</p><span>Labels remain outside the learning loop.</span></div><button className="secondary" onClick={() => void revealEvaluation()} disabled={!state.organisms.length}>Reveal evaluation</button></div>{evaluation ? <div className="evaluation"><strong>{Math.round(evaluation.purity * 100)}% purity</strong><p>{evaluation.note}</p>{evaluation.communities.map((community) => <span key={community.organismId}>{community.organismId} → {community.dominantHiddenLabel} · {community.samples} held-out samples</span>)}</div> : <p className="empty-copy">Train first, then reveal the evaluator's read-only community mapping.</p>}</article>
      <article className="panel events"><p className="panel-title">Evidence log</p><div className="event-list">{state.events.length ? state.events.map((event, index) => <div key={`${event.step}-${index}`}><b>{event.kind.replaceAll('_', ' ')}</b><span>step {event.step} · {event.reasons.join(' · ').replaceAll('_', ' ').toLowerCase()}</span></div>) : <p className="empty-copy">The log records why each structure exists.</p>}</div></article>
    </section>
    <footer>ColonyMind is a controlled learning benchmark. Resource values are compute proxies, not measured electrical watts.</footer>
  </main>;
}
