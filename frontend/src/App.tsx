import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from './api';
import { LivingArchitecture3D } from './LivingArchitecture3D';
import type { Ablation, DrawingAudit, Evaluation, Organism, RetinalStimulus, State } from './types';

const INITIAL_STATE: State = {
  seed: 20260718, stepCount: 0, stateHash: 'awaiting-api', currentStimulus: null,
  metrics: { loss: 0, meanLoss: 0, activeCells: 0, residentCells: 0, activeOrganisms: 0, residentOrganisms: 0, dormantOrganisms: 0, consolidatedMemories: 0, digestedSamples: 0, totalInformationFood: 0, microSignatures: 0, microColonies: 0, currentMicroFood: 0, microDigestedDetails: 0, activeColonies: 0, activeSynapsesProxy: 0, memoryBytesProxy: 0, resourceScore: 0, events: 0 },
  cells: [], organisms: [], colonies: [], memories: [], microSignatures: [], microColonies: [], informationPatches: [], events: [],
};

function Retina({ stimulus }: { stimulus: RetinalStimulus | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const side = stimulus?.retinaSide ?? 64;
  const pixels = stimulus?.retinaPixels ?? Array.from({ length: side * side }, () => 0);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext('2d');
    if (!canvas || !context) return;
    canvas.width = side;
    canvas.height = side;
    const image = context.createImageData(side, side);
    pixels.forEach((intensity, index) => {
      const value = Math.max(0, Math.min(1, intensity));
      image.data[index * 4] = 5 + value * 85;
      image.data[index * 4 + 1] = 13 + value * 218;
      image.data[index * 4 + 2] = 20 + value * 235;
      image.data[index * 4 + 3] = 255;
    });
    context.putImageData(image, 0, 0);
  }, [pixels, side]);

  return <div className={`retina ${stimulus ? 'active' : 'empty'}`}>
    <canvas ref={canvasRef} role="img" aria-label="Unlabeled retinal intensity matrix" />
    <span>RETINA {side}×{side}</span>
  </div>;
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <article className="metric"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</article>;
}

function DrawingAuditLab({ hasLearner, onOrganism }: { hasLearner: boolean; onOrganism: (id: string) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const [hasInk, setHasInk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<DrawingAudit | null>(null);
  const [error, setError] = useState('');

  function clearDrawing() {
    const context = canvasRef.current?.getContext('2d');
    if (!context) return;
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.fillStyle = '#020810';
    context.fillRect(0, 0, 64, 64);
    context.strokeStyle = '#f2fbff';
    context.lineWidth = 3.2;
    context.lineCap = 'round';
    context.lineJoin = 'round';
    setHasInk(false);
    setResult(null);
    setError('');
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = 64;
    canvas.height = 64;
    clearDrawing();
  }, []);

  function point(event: React.PointerEvent<HTMLCanvasElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    return { x: (event.clientX - box.left) / box.width * 64, y: (event.clientY - box.top) / box.height * 64 };
  }

  function beginStroke(event: React.PointerEvent<HTMLCanvasElement>) {
    const context = canvasRef.current?.getContext('2d');
    if (!context) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const start = point(event);
    drawing.current = true;
    context.beginPath();
    context.moveTo(start.x, start.y);
    setResult(null);
    setError('');
  }

  function continueStroke(event: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current) return;
    const context = canvasRef.current?.getContext('2d');
    if (!context) return;
    const next = point(event);
    context.lineTo(next.x, next.y);
    context.stroke();
    setHasInk(true);
  }

  function endStroke() {
    drawing.current = false;
  }

  async function auditDrawing() {
    const context = canvasRef.current?.getContext('2d');
    if (!context) return;
    const data = context.getImageData(0, 0, 64, 64).data;
    const pixels = Array.from({ length: 64 * 64 }, (_value, index) => data[index * 4] / 255);
    setBusy(true);
    setError('');
    try {
      const audit = await api.auditDrawing(pixels);
      setResult(audit);
      if (audit.ecosystemResponse.organismId) onOrganism(audit.ecosystemResponse.organismId);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'The drawing could not be audited.');
    } finally {
      setBusy(false);
    }
  }

  const labelGlyph: Record<string, string> = { circle: '○', triangle: '△', square: '□', unmapped: '?' };
  return <section className="panel draw-lab">
    <div className="panel-header"><div><p className="panel-title">Draw & audit lab</p><span>Probe the learned architecture with your own 64 × 64 retinal input.</span></div><span className="read-only-badge">READ ONLY</span></div>
    <div className="draw-lab-grid">
      <article className="draw-stage">
        <div className="draw-canvas-shell"><canvas ref={canvasRef} className="draw-canvas" aria-label="Draw a circle, triangle, or square" onPointerDown={beginStroke} onPointerMove={continueStroke} onPointerUp={endStroke} onPointerCancel={endStroke} /></div>
        <p>Draw one closed shape: circle, triangle, or square.</p>
        <div className="draw-actions"><button className="primary" disabled={!hasInk || busy} onClick={() => void auditDrawing()}>{busy ? 'Auditing…' : 'Ask learner + auditor'}</button><button className="secondary" onClick={clearDrawing}>Clear</button></div>
        {!hasLearner && <small>Train the ecosystem first to compare its response; the external auditor can still inspect the drawing.</small>}
        {error && <small className="draw-error">{error}</small>}
      </article>
      <article className="probe-result learner-result">
        <span className="result-kicker">ECOSYSTEM RESPONSE · NO LABEL ACCESS</span>
        {result ? <><strong>{result.ecosystemResponse.organismId ?? 'No organism yet'}</strong><dl><div><dt>Relative response</dt><dd>{Math.round(result.ecosystemResponse.confidence * 100)}%</dd></div><div><dt>Reconstruction error</dt><dd>{result.ecosystemResponse.reconstructionError?.toFixed(4) ?? '—'}</dd></div><div><dt>Colony</dt><dd>{result.ecosystemResponse.colonyId ?? 'independent'}</dd></div></dl></> : <p className="empty-copy">The closest learned organism will respond here. It sees pixels, never the shape name.</p>}
      </article>
      <article className={`probe-result auditor-result ${result?.agreement ? 'agreement' : ''}`}>
        <span className="result-kicker">EXTERNAL GEOMETRIC AUDITOR</span>
        {result ? <><div className="auditor-label"><i>{labelGlyph[result.externalAuditor.drawnLabel] ?? '?'}</i><div><strong>{result.externalAuditor.drawnLabel}</strong><span>{Math.round(result.externalAuditor.confidence * 100)}% relative confidence</span></div></div><div className="score-bars">{Object.entries(result.externalAuditor.labelScores).map(([label, score]) => <div key={label}><span>{label}</span><i><b style={{ width: `${Math.round(score * 100)}%` }}/></i><em>{Math.round(score * 100)}%</em></div>)}</div><div className={`agreement-box ${result.agreement ? 'yes' : 'no'}`}><b>{result.agreement ? 'AGREEMENT' : 'DISAGREEMENT'}</b><span>Auditor maps {result.ecosystemResponse.organismId ?? 'no organism'} to <strong>{result.externalAuditor.organismAssociatedLabel}</strong>.</span></div><small>{result.modelModified ? 'Warning: model changed' : `State preserved · ${result.stateHashAfter}`}</small></> : <p className="empty-copy">This independent observer owns the labels and checks the learner without changing it.</p>}
      </article>
    </div>
  </section>;
}

export default function App() {
  const [state, setState] = useState<State>(INITIAL_STATE);
  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState(12);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [ablation, setAblation] = useState<Ablation | null>(null);
  const [reporting, setReporting] = useState(false);
  const [notice, setNotice] = useState('Connect to the learning engine to begin.');

  const refresh = useCallback(async () => {
    try { setState(await api.state()); setNotice(''); } catch { setNotice('API unavailable. Start the FastAPI service to connect the ecosystem.'); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    if (!running) return;
    let cancelled = false;
    let timer = 0;
    const advance = async () => {
      try {
        const nextState = await api.step(speed);
        if (!cancelled) setState(nextState);
      } catch {
        if (!cancelled) { setRunning(false); setNotice('Training paused because the API is unavailable.'); }
      }
      if (!cancelled) timer = window.setTimeout(() => { void advance(); }, 650);
    };
    void advance();
    return () => { cancelled = true; window.clearTimeout(timer); };
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
  async function downloadReport() {
    setReporting(true);
    try {
      const report = await api.report();
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      const timestamp = new Date().toISOString().replaceAll(':', '-').replaceAll('.', '-');
      anchor.href = url;
      const reportStep = (report as { simulation?: { stepCount?: number } }).simulation?.stepCount ?? state.stepCount;
      anchor.download = `colonymind-performance-step-${reportStep}-${timestamp}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setNotice('JSON performance report downloaded with learning and audit evidence.');
    } catch {
      setNotice('The JSON performance report could not be generated.');
    } finally {
      setReporting(false);
    }
  }

  return <main>
    <nav><div className="brand"><i>◌</i><span>COLONY<span>MIND</span></span></div><div className="nav-copy">SELF-ORGANIZING VISION <b>•</b> BUILD WEEK 2026</div><div className="nav-actions"><button className="report-button" disabled={reporting} onClick={() => void downloadReport()}>{reporting ? 'Preparing JSON…' : '↓ Download JSON report'}</button><button className="outline" onClick={() => void reset()}>Reset ecosystem</button></div></nav>
    <section className="hero">
      <div><p className="eyebrow">A RESOURCE-AWARE LEARNING LAB</p><h1>Watch a vision architecture <em>organize itself.</em></h1><p className="lede">Unlabeled shapes enter as information. Cells become organisms. Organisms form colonies only when cooperation earns its computational cost.</p><div className="hero-actions"><button className="primary" onClick={() => setRunning((value) => !value)}>{running ? 'Pause learning' : 'Start learning'}</button><button className="secondary" onClick={() => void trainOnce()}>Advance {speed} steps</button><select value={speed} onChange={(event) => setSpeed(Number(event.target.value))} aria-label="Training batch size"><option value={4}>4 steps</option><option value={12}>12 steps</option><option value={36}>36 steps</option><option value={96}>96 steps</option></select></div></div>
      <div className="hero-orbit"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="hero-node">0<br/><small>fixed layers</small></div><span className="shape triangle">△</span><span className="shape circle">○</span><span className="shape square">□</span></div>
    </section>
    {notice && <p className="notice">{notice}</p>}
    <section className="metrics"><Metric label="Unsupervised loss" value={state.metrics.loss.toFixed(4)} hint="lower is better"/><Metric label="Micro-signature layer" value={`${state.metrics.microSignatures}/${state.metrics.microColonies}`} hint="detail units / colonies"/><Metric label="Processing cells" value={`${state.metrics.activeCells}/${state.metrics.residentCells}`} hint="active / resident"/><Metric label="Organism memory" value={`${state.metrics.activeOrganisms}/${state.metrics.residentOrganisms}`} hint="relevant / resident"/><Metric label="Consolidated memories" value={state.metrics.consolidatedMemories} hint={`${state.metrics.digestedSamples} samples fully digested`}/><Metric label="Resource score" value={state.metrics.resourceScore.toFixed(3)} hint="benefit − proxy cost"/></section>
    <section className="workspace">
      <aside className="panel input-panel"><p className="panel-title">Retinal information stream</p><div className="retina-card"><Retina stimulus={state.currentStimulus}/><div><strong>{state.currentStimulus ? 'Unlabeled retinal stimulus' : 'Waiting for photons'}</strong><span>{state.currentStimulus ? `${state.currentStimulus.renderMode} · ${Math.round(state.currentStimulus.scale * 100)}% scale · ${Math.round(state.currentStimulus.rotation * 180 / Math.PI)}° rotation · noise ${state.currentStimulus.noise}` : 'The learner begins with zero cells and sees only pixel intensity.'}</span></div></div><dl><div><dt>Semantic labels received</dt><dd>Never</dd></div><div><dt>Current step</dt><dd>{state.stepCount}</dd></div><div><dt>Retinal resolution</dt><dd>{state.currentStimulus ? `${state.currentStimulus.retinaSide} × ${state.currentStimulus.retinaSide}` : '64 × 64'}</dd></div><div><dt>Fine-detail food</dt><dd>{state.metrics.currentMicroFood.toFixed(3)}</dd></div><div><dt>Micro details digested</dt><dd>{state.metrics.microDigestedDetails}</dd></div><div><dt>Position offset</dt><dd>{state.currentStimulus ? `${state.currentStimulus.offsetX}, ${state.currentStimulus.offsetY}` : '—'}</dd></div><div><dt>Occluded area</dt><dd>{Math.round((state.currentStimulus?.occlusion ?? 0) * 100)}%</dd></div></dl><div className="rule"><b>Hierarchical retinal boundary</b><span>Pixels feed local edge and curvature micro-signatures. Their coactivation colonies compose a rotation-tolerant intermediate signature; no shape name enters either layer.</span></div></aside>
      <section className="panel ecosystem"><div className="panel-header"><div><p className="panel-title">Living architecture · 3D</p><span>Explore how retinal details become cells, organisms, colonies, and persistent memories.</span></div><span className="seed">seed {state.seed}</span></div><div className="micro-layer-summary"><span>INTERMEDIATE LAYER</span><b>{state.metrics.microSignatures} micro-signatures</b><i>{state.metrics.microColonies} coactivation colonies · food {state.metrics.currentMicroFood.toFixed(3)}</i></div><LivingArchitecture3D state={state} selectedId={selectedId} onSelect={setSelectedId}/><div className="legend architecture-legend"><span><i className="micro-dot"/>micro-signature</span><span><i className="food-dot"/>information food</span><span><i className="digested-dot"/>memory engram</span><span><i className="dot cyan"/>cell / organism</span><span><i className="ring"/>colony membrane</span></div></section>
      <aside className="panel inspector"><p className="panel-title">Selected organism</p>{selected ? <><div className="organism-heading"><i style={{ background: selected.color }}/><div><strong>{selected.id}</strong><span>lineage {selected.lineage}</span></div><b className={`lifecycle-badge ${selected.lifecycleState}`}>{selected.lifecycleState}</b></div><dl><div><dt>Cells</dt><dd>{cellsByOrganism[selected.id] ?? 0}</dd></div><div><dt>Intermediate signature</dt><dd>{selected.intermediateDimensions} dims</dd></div><div><dt>Explicit micro affinities</dt><dd>{Object.keys(selected.microAffinities ?? {}).length}</dd></div><div><dt>Micro profile updates</dt><dd>{selected.microProfileUpdates ?? 0}</dd></div><div><dt>Global age</dt><dd>{selected.ageSteps} steps</dd></div><div><dt>Learning wins</dt><dd>{selected.wins}</dd></div><div><dt>Undigested food evidence</dt><dd>{selected.foodEvidence.toFixed(3)}</dd></div><div><dt>Digestion evidence</dt><dd>{selected.digestionEvidence.toFixed(1)}</dd></div><div><dt>Consolidated memories</dt><dd>{selected.memoryIds.length}</dd></div><div><dt>Inactive</dt><dd>{selected.inactiveSteps} steps</dd></div><div><dt>Reactivations</dt><dd>{selected.reactivations}</dd></div><div><dt>Protected for</dt><dd>{Math.max(0, selected.protectedUntil - state.stepCount)} steps</dd></div><div><dt>Energy</dt><dd>{Math.round(selected.energy * 100)}%</dd></div><div><dt>Marginal contribution</dt><dd>{selected.contribution.toFixed(4)}</dd></div><div><dt>Colony</dt><dd>{selected.colonyId ?? 'independent'}</dd></div></dl><button className="secondary full" onClick={() => void runAblation(selected)}>Run read-only ablation</button>{ablation?.organismId === selected.id && <div className="ablation"><b>Evidence</b><span>Loss changes by {ablation.delta.toFixed(4)} when {selected.id} is removed.</span><small>{ablation.modelModified ? 'Warning: state changed' : 'Live state preserved'}</small></div>}</> : <p className="empty-copy">An organism inspector will appear after the first unlabeled stimulus creates a pioneer cell.</p>}</aside>
    </section>
    <DrawingAuditLab hasLearner={state.organisms.length > 0} onOrganism={setSelectedId}/>
    <section className="lower-grid"><article className="panel evidence"><div className="panel-header"><div><p className="panel-title">Hidden evaluation</p><span>Labels remain outside the learning loop.</span></div><button className="secondary" onClick={() => void revealEvaluation()} disabled={!state.organisms.length}>Reveal evaluation</button></div>{evaluation ? <div className="evaluation"><strong>{Math.round(evaluation.purity * 100)}% purity</strong><p>{evaluation.note}</p>{evaluation.communities.map((community) => <span key={community.organismId}>{community.organismId} → {community.dominantHiddenLabel} · {community.samples} held-out samples</span>)}</div> : <p className="empty-copy">Train first, then reveal the evaluator's read-only community mapping.</p>}</article>
      <article className="panel events"><p className="panel-title">Evidence log</p><div className="event-list">{state.events.length ? state.events.map((event, index) => <div key={`${event.step}-${index}`}><b>{event.kind.replaceAll('_', ' ')}</b><span>step {event.step} · {event.reasons.join(' · ').replaceAll('_', ' ').toLowerCase()}</span></div>) : <p className="empty-copy">The log records why each structure exists.</p>}</div></article>
    </section>
    <footer>ColonyMind is a controlled learning benchmark. Resource values are compute proxies, not measured electrical watts.</footer>
  </main>;
}
