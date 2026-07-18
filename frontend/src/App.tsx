import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from './api';
import type { Ablation, Evaluation, Organism, RetinalStimulus, State } from './types';

const INITIAL_STATE: State = {
  seed: 20260718, stepCount: 0, stateHash: 'awaiting-api', currentStimulus: null,
  metrics: { loss: 0, meanLoss: 0, activeCells: 0, activeOrganisms: 0, activeColonies: 0, activeSynapsesProxy: 0, memoryBytesProxy: 0, resourceScore: 0, events: 0 },
  cells: [], organisms: [], colonies: [], informationPatches: [], events: [],
};

function Retina({ stimulus }: { stimulus: RetinalStimulus | null }) {
  const side = stimulus?.retinaSide ?? 32;
  const pixels = stimulus?.retinaPixels ?? Array.from({ length: side * side }, () => 0);
  return <div className={`retina ${stimulus ? 'active' : 'empty'}`}>
    <svg viewBox={`0 0 ${side} ${side}`} role="img" aria-label="Unlabeled retinal intensity matrix">
      <rect width={side} height={side} className="retina-background" />
      {pixels.map((intensity, index) => <rect key={index} x={index % side} y={Math.floor(index / side)} width="1.02" height="1.02" fill={`rgba(102, 224, 255, ${Math.max(0.02, intensity)})`} />)}
      {Array.from({ length: side + 1 }, (_, index) => <path key={`v-${index}`} d={`M ${index} 0 V ${side}`} />)}
      {Array.from({ length: side + 1 }, (_, index) => <path key={`h-${index}`} d={`M 0 ${index} H ${side}`} />)}
    </svg>
    <span>RETINA {side}×{side}</span>
  </div>;
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <article className="metric"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</article>;
}

function LivingArchitecture({ state, selectedId, onSelect }: { state: State; selectedId: string | null; onSelect: (id: string) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let animation = 0;
    const draw = (now: number) => {
      const canvas = canvasRef.current;
      const context = canvas?.getContext('2d');
      if (!canvas || !context) return;
      const box = canvas.getBoundingClientRect();
      const density = window.devicePixelRatio || 1;
      const pixelWidth = Math.max(1, Math.round(box.width * density));
      const pixelHeight = Math.max(1, Math.round(box.height * density));
      if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) { canvas.width = pixelWidth; canvas.height = pixelHeight; }
      context.setTransform(canvas.width / 100, 0, 0, canvas.height / 100, 0, 0);
      context.clearRect(0, 0, 100, 100);
      const background = context.createRadialGradient(50, 48, 4, 50, 48, 72);
      background.addColorStop(0, '#0d2a3c'); background.addColorStop(0.55, '#071724'); background.addColorStop(1, '#030b13');
      context.fillStyle = background; context.fillRect(0, 0, 100, 100);
      context.lineWidth = 0.12; context.strokeStyle = 'rgba(112,218,255,.075)';
      for (let grid = 10; grid < 100; grid += 10) { context.beginPath(); context.moveTo(grid, 0); context.lineTo(grid, 100); context.stroke(); context.beginPath(); context.moveTo(0, grid); context.lineTo(100, grid); context.stroke(); }

      state.informationPatches.forEach((patch, index) => {
        const age = Math.max(0, state.stepCount - patch.createdStep);
        const pulse = 1 + Math.sin(now * 0.006 + index) * 0.22;
        const alpha = Math.max(0.12, 0.85 - age / 22);
        context.globalAlpha = alpha;
        context.strokeStyle = patch.consumedBy ? '#5cd7ff' : '#ffc36d';
        context.fillStyle = patch.consumedBy ? 'rgba(85,215,255,.18)' : 'rgba(255,187,93,.3)';
        context.beginPath(); context.arc(patch.x, patch.y, (1.2 + patch.amount * 2.5) * pulse, 0, Math.PI * 2); context.fill(); context.stroke();
        context.beginPath(); context.moveTo(patch.x - 1.4, patch.y); context.lineTo(patch.x + 1.4, patch.y); context.moveTo(patch.x, patch.y - 1.4); context.lineTo(patch.x, patch.y + 1.4); context.stroke();
      });
      context.globalAlpha = 1;

      state.colonies.forEach((colony) => {
        const members = state.organisms.filter((organism) => colony.member_ids.includes(organism.id));
        if (!members.length) return;
        const centerX = members.reduce((sum, organism) => sum + organism.x, 0) / members.length;
        const centerY = members.reduce((sum, organism) => sum + organism.y, 0) / members.length;
        context.strokeStyle = 'rgba(177,132,255,.7)'; context.lineWidth = 0.45; context.setLineDash([1.4, 1.1]);
        members.forEach((organism) => { context.beginPath(); context.moveTo(centerX, centerY); context.lineTo(organism.x, organism.y); context.stroke(); });
        context.beginPath(); context.arc(centerX, centerY, 8 + Math.sqrt(members.length) * 4 + Math.sin(now * .002) * .8, 0, Math.PI * 2); context.stroke(); context.setLineDash([]);
        context.fillStyle = '#c9afff'; context.font = "2.4px 'DM Mono', monospace"; context.textAlign = 'center'; context.fillText(colony.id, centerX, centerY - 11);
      });

      const cellCounts = state.cells.reduce<Record<string, number>>((counts, cell) => ({ ...counts, [cell.organism_id]: (counts[cell.organism_id] ?? 0) + 1 }), {});
      state.organisms.forEach((organism, organismIndex) => {
        const x = organism.x + Math.sin(now * .0017 + organismIndex * 2.1) * .55;
        const y = organism.y + Math.cos(now * .0014 + organismIndex * 1.7) * .55;
        const cells = cellCounts[organism.id] ?? 1;
        const radius = 2.7 + Math.sqrt(cells) * .9;
        context.strokeStyle = organism.color; context.globalAlpha = .28; context.lineWidth = .8;
        context.beginPath(); context.moveTo(x, y); context.lineTo(x - Math.cos(organism.heading) * (5 + radius), y - Math.sin(organism.heading) * (5 + radius)); context.stroke();
        context.globalAlpha = .18; context.fillStyle = organism.color; context.beginPath(); context.arc(x, y, radius * 2.5, 0, Math.PI * 2); context.fill();
        context.globalAlpha = 1; context.fillStyle = organism.color; context.beginPath(); context.arc(x, y, radius, 0, Math.PI * 2); context.fill();
        context.strokeStyle = selectedId === organism.id ? '#ffffff' : organism.color; context.lineWidth = selectedId === organism.id ? .75 : .22; context.stroke();
        for (let cell = 0; cell < cells; cell += 1) { const angle = now * .0012 * (cell % 2 ? -1 : 1) + cell * 2.399 + organismIndex; const orbit = radius + 2.4 + (cell % 3) * .7; context.fillStyle = organism.color; context.beginPath(); context.arc(x + Math.cos(angle) * orbit, y + Math.sin(angle) * orbit, .65 + (cell % 2) * .18, 0, Math.PI * 2); context.fill(); }
        context.fillStyle = '#d9efff'; context.font = "2px 'DM Mono', monospace"; context.textAlign = 'center'; context.fillText(organism.id, x, y + radius + 5.2);
      });
      context.globalAlpha = 1;
      if (!state.organisms.length) { context.fillStyle = '#6f8ca3'; context.font = "3px 'DM Mono', monospace"; context.textAlign = 'center'; context.fillText('ZERO LEARNED STRUCTURE', 50, 50); }
      animation = requestAnimationFrame(draw);
    };
    animation = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animation);
  }, [state, selectedId]);

  function selectAt(event: React.MouseEvent<HTMLCanvasElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width * 100;
    const y = (event.clientY - box.top) / box.height * 100;
    const nearest = state.organisms.map((organism) => ({ organism, distance: Math.hypot(organism.x - x, organism.y - y) })).sort((a, b) => a.distance - b.distance)[0];
    if (nearest && nearest.distance < 12) onSelect(nearest.organism.id);
  }

  return <canvas ref={canvasRef} className="ecosystem-canvas" onClick={selectAt} aria-label="Living self-organizing learning habitat" />;
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
      <aside className="panel input-panel"><p className="panel-title">Retinal information stream</p><div className="retina-card"><Retina stimulus={state.currentStimulus}/><div><strong>{state.currentStimulus ? 'Unlabeled retinal stimulus' : 'Waiting for photons'}</strong><span>{state.currentStimulus ? `${Math.round(state.currentStimulus.scale * 100)}% scale · ${Math.round(state.currentStimulus.rotation * 180 / Math.PI)}° rotation · noise ${state.currentStimulus.noise}` : 'The learner begins with zero cells and sees only pixel intensity.'}</span></div></div><dl><div><dt>Semantic labels received</dt><dd>Never</dd></div><div><dt>Current step</dt><dd>{state.stepCount}</dd></div><div><dt>Retinal resolution</dt><dd>{state.currentStimulus ? `${state.currentStimulus.retinaSide} × ${state.currentStimulus.retinaSide}` : '32 × 32'}</dd></div><div><dt>Position offset</dt><dd>{state.currentStimulus ? `${state.currentStimulus.offsetX}, ${state.currentStimulus.offsetY}` : '—'}</dd></div><div><dt>Occluded area</dt><dd>{Math.round((state.currentStimulus?.occlusion ?? 0) * 100)}%</dd></div></dl><div className="rule"><b>Retinal boundary</b><span>The generator knows which shape it renders. The learner receives only the fine-grained, anti-aliased intensity matrix shown above.</span></div></aside>
      <section className="panel ecosystem"><div className="panel-header"><div><p className="panel-title">Living architecture</p><span>Organisms forage retinal information; colonies add cohesion only when cooperation pays.</span></div><span className="seed">seed {state.seed}</span></div><LivingArchitecture state={state} selectedId={selected?.id ?? null} onSelect={setSelectedId}/><div className="legend"><span><i className="food-dot"/>information food</span><span><i className="dot cyan"/>cell</span><span><i className="dot violet"/>organism</span><span><i className="ring"/>persistent colony</span></div></section>
      <aside className="panel inspector"><p className="panel-title">Selected organism</p>{selected ? <><div className="organism-heading"><i style={{ background: selected.color }}/><div><strong>{selected.id}</strong><span>lineage {selected.lineage}</span></div></div><dl><div><dt>Cells</dt><dd>{cellsByOrganism[selected.id] ?? 0}</dd></div><div><dt>Energy</dt><dd>{Math.round(selected.energy * 100)}%</dd></div><div><dt>Marginal contribution</dt><dd>{selected.contribution.toFixed(4)}</dd></div><div><dt>Colony</dt><dd>{selected.colonyId ?? 'independent'}</dd></div></dl><button className="secondary full" onClick={() => void runAblation(selected)}>Run read-only ablation</button>{ablation?.organismId === selected.id && <div className="ablation"><b>Evidence</b><span>Loss changes by {ablation.delta.toFixed(4)} when {selected.id} is removed.</span><small>{ablation.modelModified ? 'Warning: state changed' : 'Live state preserved'}</small></div>}</> : <p className="empty-copy">An organism inspector will appear after the first unlabeled stimulus creates a pioneer cell.</p>}</aside>
    </section>
    <section className="lower-grid"><article className="panel evidence"><div className="panel-header"><div><p className="panel-title">Hidden evaluation</p><span>Labels remain outside the learning loop.</span></div><button className="secondary" onClick={() => void revealEvaluation()} disabled={!state.organisms.length}>Reveal evaluation</button></div>{evaluation ? <div className="evaluation"><strong>{Math.round(evaluation.purity * 100)}% purity</strong><p>{evaluation.note}</p>{evaluation.communities.map((community) => <span key={community.organismId}>{community.organismId} → {community.dominantHiddenLabel} · {community.samples} held-out samples</span>)}</div> : <p className="empty-copy">Train first, then reveal the evaluator's read-only community mapping.</p>}</article>
      <article className="panel events"><p className="panel-title">Evidence log</p><div className="event-list">{state.events.length ? state.events.map((event, index) => <div key={`${event.step}-${index}`}><b>{event.kind.replaceAll('_', ' ')}</b><span>step {event.step} · {event.reasons.join(' · ').replaceAll('_', ' ').toLowerCase()}</span></div>) : <p className="empty-copy">The log records why each structure exists.</p>}</div></article>
    </section>
    <footer>ColonyMind is a controlled learning benchmark. Resource values are compute proxies, not measured electrical watts.</footer>
  </main>;
}
