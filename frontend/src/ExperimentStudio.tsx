import { useEffect, useMemo, useState } from 'react';
import { api } from './api';
import type { AuthUser, BaselineManifest, ExperimentRecord, ResearchAudit } from './types';

function metric(value: number | undefined) { return value == null ? '—' : value.toFixed(3); }

type Props = {
  audit: ResearchAudit | null;
  currentStateHash: string;
  user: AuthUser | null;
  canAudit: boolean;
  onBeforeAudit: () => void;
  onAudit: (audit: ResearchAudit) => void;
};

export function ExperimentStudio({ audit, currentStateHash, user, canAudit, onBeforeAudit, onAudit }: Props) {
  const [baseline, setBaseline] = useState<BaselineManifest | null>(null);
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [instruction, setInstruction] = useState('');
  const [parentId, setParentId] = useState('colonymind-build-week-baseline-v1');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [auditBusy, setAuditBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function refresh() {
    try {
      const [base, versions] = await Promise.all([api.baseline(), api.experiments()]);
      setBaseline(base);
      setExperiments(versions);
      if (selectedId && !versions.some((item) => item.id === selectedId)) setSelectedId(null);
    } catch { setMessage('Experiment registry is temporarily unavailable.'); }
  }

  useEffect(() => { void refresh(); }, [user]);
  useEffect(() => {
    if (!experiments.some((item) => item.status === 'queued' || item.status === 'running')) return;
    const timer = window.setInterval(() => void refresh(), 1800);
    return () => window.clearInterval(timer);
  }, [experiments]);

  const selected = useMemo(() => experiments.find((item) => item.id === selectedId) ?? experiments.at(-1) ?? null, [experiments, selectedId]);
  const auditIsCurrent = audit?.snapshotStateHash === currentStateHash;
  const selectedParent = experiments.find((item) => item.id === parentId);
  const parentAuditAvailable = Boolean(selectedParent?.result?.externalAudit);
  const designAuditReady = auditIsCurrent || parentAuditAvailable;
  const canDesign = canAudit || parentAuditAvailable;
  const actualStepsRecorded = Boolean(selected?.result?.schema === 'colonymind-experiment-result/v2' && selected.result.runs.every((run) => typeof run.actualTrainingSteps === 'number'));
  const actualStepsVerified = Boolean(actualStepsRecorded && selected?.result?.runs.every((run) => run.actualTrainingSteps === selected.proposal.protocol.trainingSteps));

  async function createAndRun() {
    if (!canDesign) { setMessage('Train and audit the ecosystem, or select an already audited parent version.'); return; }
    setBusy(true);
    try {
      if (!auditIsCurrent && !parentAuditAvailable) {
        onBeforeAudit();
        setMessage('Freezing the current state and refreshing the GPT-5.6 audit…');
        const nextAudit = await api.researchAudit();
        onAudit(nextAudit);
      }
      setMessage('GPT-5.6 is translating current evidence into an allowlisted experiment protocol…');
      const created = await api.createExperiment(instruction.trim(), parentId);
      const queued = await api.runExperiment(created.id);
      setExperiments((items) => [...items, queued]);
      setSelectedId(queued.id);
      setParentId(queued.id);
      setInstruction('');
      setMessage(`Version ${queued.version} is running in an isolated engine. The baseline remains untouched.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'The experiment version could not be created.');
    } finally { setBusy(false); }
  }

  async function auditVersion(record: ExperimentRecord) {
    setAuditBusy(true);
    setMessage('GPT-5.6 is auditing the completed version, its matched control, and machine-verified criteria…');
    try {
      const updated = await api.auditExperiment(record.id);
      setExperiments((items) => items.map((item) => item.id === updated.id ? updated : item));
      setSelectedId(updated.id);
      setParentId(updated.id);
      setMessage(`Version ${updated.version} now has an independent, read-only research audit.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'The completed version could not be audited.');
    } finally { setAuditBusy(false); }
  }

  async function remove(record: ExperimentRecord) {
    await api.deleteExperiment(record.id);
    setExperiments((items) => items.filter((item) => item.id !== record.id));
    if (selectedId === record.id) setSelectedId(null);
    setMessage(`Version ${record.version} deleted. Baseline v1 is still preserved.`);
  }

  const aggregate = selected?.result?.aggregate;
  return <section id="experiment-studio" className="panel experiment-studio">
    <div className="panel-header experiment-studio-header">
      <div><p className="panel-title">Versioned Experiment Studio</p><span>Turn the auditor's diagnosis into isolated, reproducible branches.</span></div>
      <span className={`workspace-mode ${user ? 'persistent' : 'ephemeral'}`}>{user ? 'POSTGRES · PERSISTENT' : 'ANONYMOUS · EPHEMERAL'}</span>
    </div>

    <div className="baseline-lock">
      <div className="baseline-lock-icon">⌾</div>
      <div><span>IMMUTABLE REFERENCE</span><strong>Baseline v1 · Build Week learner</strong><small>{baseline?.commit.slice(0, 8) ?? 'loading'} · core {baseline?.coreSha256.slice(0, 10) ?? 'loading'} · cannot edit or delete</small></div>
      <b>{baseline?.verified === false ? 'VERIFY FAILED' : 'LOCKED'}</b>
    </div>

    <div className="experiment-compose">
      <div className="experiment-chat">
        <div className="chat-message assistant"><i>GPT‑5.6</i><p>I can turn the current audit into a multi-seed replication, robustness test, or learning-curve version. I only configure a validated protocol; I cannot edit the baseline or execute arbitrary code.</p></div>
        {selected && <>
          {selected.instruction && <div className="chat-message user"><i>YOU · VERSION {selected.version}</i><p>{selected.instruction}</p></div>}
          <div className="chat-message assistant"><i>GPT‑5.6 · PROPOSAL</i><p>{selected.proposal.rationale}</p><small>{selected.proposal.judgeExplanation}</small></div>
        </>}
        <textarea value={instruction} onChange={(event) => setInstruction(event.target.value)} placeholder="Optional: add a constraint or request a variant, e.g. ‘prioritize rotation robustness with three seeds’" maxLength={1200} />
        <div className="experiment-suggestions"><button onClick={() => setInstruction('Create a versioned experiment that adds pentagon and star while preserving the three baseline shapes as controls. Use the baseline learning policy first.')}>+ Add new shapes</button><button onClick={() => setInstruction('Propose one bounded learning-kernel parameter change, run it as a derived copy, and compare it against a matched baseline-policy control.')}>⚙ Test kernel tuning</button><button onClick={() => setInstruction('Run a true learning curve with checkpoints at 240, 480, 960, and the final requested step. Verify actual step counts.')}>↗ Learning curve</button></div>
        <div className="experiment-compose-actions">
          <label>Derive from<select value={parentId} onChange={(event) => setParentId(event.target.value)}><option value={baseline?.id ?? 'colonymind-build-week-baseline-v1'}>Baseline v1</option>{experiments.map((item) => <option key={item.id} value={item.id}>Version {item.version} · {item.proposal.shortLabel}</option>)}</select></label>
          <button className="primary" disabled={!canDesign || busy} onClick={() => void createAndRun()}>{busy ? 'Auditing & designing…' : selected ? (designAuditReady ? 'Create & run variant' : 'Refresh audit & run variant') : (designAuditReady ? 'Implement auditor experiment' : 'Refresh audit & implement')}</button>
        </div>
        {!canDesign && <small className="experiment-gate">Train and audit the ecosystem first, or select an audited parent version.</small>}
        {canAudit && !audit && <small className="experiment-gate">This action will freeze and audit the current state before creating the version.</small>}
        {canAudit && audit && !designAuditReady && <small className="experiment-gate">The ecosystem advanced after this audit. This action will refresh the audit automatically before branching.</small>}
        {parentAuditAvailable && <small className="experiment-gate parent-ready">The selected parent has a completed result audit; GPT-5.6 will design from that version instead of the live baseline.</small>}
        {message && <p className="experiment-message">{message}</p>}
      </div>

      <div className="version-rail">
        <article className="version-card baseline selected"><span>BASE</span><b>Baseline v1</b><small>Always preserved</small></article>
        {experiments.map((record) => <article key={record.id} className={`version-card ${selected?.id === record.id ? 'selected' : ''}`} onClick={() => { setSelectedId(record.id); setParentId(record.id); }}>
          <span>V{record.version} · {record.status}</span><b>{record.proposal.shortLabel}</b><small>{record.proposal.protocol.seeds.length} seeds · {record.proposal.protocol.trainingSteps} steps · {record.proposal.kernel.shapes.length} shapes · {record.proposal.kernel.mode.replaceAll('_', ' ')}</small>
          <button aria-label={`Delete version ${record.version}`} onClick={(event) => { event.stopPropagation(); void remove(record); }}>×</button>
        </article>)}
      </div>
    </div>

    {selected && <div className="experiment-detail">
      <div className="experiment-detail-head"><div><span>VERSION {selected.version} · {selected.status}</span><h3>{selected.proposal.title}</h3><p>{selected.proposal.hypothesis}</p></div><b>{selected.persistent ? 'SAVED' : 'TEMPORARY'}</b></div>
      <div className="protocol-strip"><span><b>TYPE</b>{selected.proposal.protocol.experimentType.replaceAll('_', ' ')}</span><span><b>SEEDS</b>{selected.proposal.protocol.seeds.join(', ')}</span><span><b>REQUESTED TRAINING</b>{selected.proposal.protocol.trainingSteps} steps</span><span><b>EVALUATION</b>{selected.proposal.protocol.samplesPerShape * selected.proposal.kernel.shapes.length} samples · {selected.proposal.protocol.nuisanceProfile}</span></div>
      <div className={`kernel-branch ${selected.proposal.kernel.mode}`}><div><span>{selected.proposal.kernel.mode === 'derived_copy' ? 'DERIVED KERNEL COPY' : 'BASELINE POLICY COPY'}</span><strong>{selected.proposal.kernel.shapes.join(' · ')}</strong><small>base {baseline?.coreSha256.slice(0, 10)} · spec {selected.result?.kernelProvenance?.variantSpecSha256?.slice(0, 10) ?? 'awaiting run'} · generated code: never</small></div><div className="kernel-changes">{selected.proposal.kernel.changeSummary.map((change) => <p key={change}>{change}</p>)}{selected.proposal.kernel.mechanisms.map((mechanism) => <b key={mechanism}>mechanism: {mechanism.replaceAll('_', ' ')}</b>)}{Object.entries(selected.proposal.kernel.parameterOverrides).filter((entry) => entry[1] != null).map(([name, value]) => <b key={name}>{name} = {value}</b>)}</div></div>
      {selected.status === 'completed' && aggregate && <>
        <div className="actual-step-proof"><b>ACTUAL EXECUTION</b><span>{actualStepsRecorded ? `${selected.result?.runs.map((run) => run.actualTrainingSteps).join(', ')} steps across seeds` : 'Not recorded by the legacy runner; the displayed target cannot verify execution.'}</span><i>{actualStepsVerified ? 'VERIFIED' : actualStepsRecorded ? 'MISMATCH' : 'LEGACY · UNVERIFIED'}</i></div>
        <div className="experiment-metrics"><article><span>PURITY</span><strong>{metric(aggregate.purity.mean)}</strong><small>{metric(aggregate.purity.min)}–{metric(aggregate.purity.max)}{selected.result?.comparison?.clustering.purity && ` · Δ ${selected.result.comparison.clustering.purity.delta >= 0 ? '+' : ''}${metric(selected.result.comparison.clustering.purity.delta)}`}</small></article><article><span>NMI</span><strong>{metric(aggregate.nmi.mean)}</strong><small>community completeness{selected.result?.comparison?.clustering.nmi && ` · Δ ${selected.result.comparison.clustering.nmi.delta >= 0 ? '+' : ''}${metric(selected.result.comparison.clustering.nmi.delta)}`}</small></article><article><span>ARI</span><strong>{metric(aggregate.ari.mean)}</strong><small>chance-adjusted agreement{selected.result?.comparison?.clustering.ari && ` · Δ ${selected.result.comparison.clustering.ari.delta >= 0 ? '+' : ''}${metric(selected.result.comparison.clustering.ari.delta)}`}</small></article><article><span>FRAGMENTATION</span><strong>{metric(aggregate.fragmentation.mean)}</strong><small>1.0 ≈ one community/class{selected.result?.comparison?.clustering.fragmentation && ` · Δ ${selected.result.comparison.clustering.fragmentation.delta >= 0 ? '+' : ''}${metric(selected.result.comparison.clustering.fragmentation.delta)}`}</small></article></div>
        {selected.result?.comparison && <div className="matched-control"><span>MATCHED BASELINE-POLICY CONTROL · SAME SEEDS, SHAPES & INPUTS</span>{[['cells', selected.result.comparison.structure.cells], ['organisms', selected.result.comparison.structure.organisms], ['micro-signatures', selected.result.comparison.structure.microSignatures], ['resource score', selected.result.comparison.resources.resourceScore]].filter((entry) => entry[1]).map(([label, raw]) => { const value = raw as { variant: number; control: number; delta: number }; return <p key={String(label)}><b>{String(label)}</b><strong>{value.variant}</strong><small>control {value.control} · Δ {value.delta >= 0 ? '+' : ''}{value.delta}</small></p>; })}</div>}
        <div className="experiment-preserved"><b>{selected.result?.baselinePreserved ? 'BASELINE PRESERVED' : 'VERIFY RESULT'}</b><span>{selected.result?.interpretationBoundary}</span></div>
        {selected.result?.criteria?.length ? <div className="verified-criteria"><span>MACHINE-VERIFIED CRITERIA</span>{selected.result.criteria.map((criterion) => <p key={criterion.id} className={criterion.status}><b>{criterion.status === 'passed' ? '✓' : criterion.status === 'failed' ? '×' : '·'}</b><span>{criterion.label}<small>observed {criterion.observed} · required {criterion.required}</small></span></p>)}</div> : <p className="legacy-result-warning">Legacy result: machine-verifiable criteria were not recorded. Re-run as a new version before making formal claims.</p>}
        <div className="version-audit-action"><button className="secondary" disabled={auditBusy} onClick={() => void auditVersion(selected)}>{auditBusy ? 'Auditing version…' : selected.result?.externalAudit ? 'Refresh version audit' : 'Audit this completed version'}</button><span>GPT-5.6 receives aggregate result evidence only—not pixels, prototypes, or a write path.</span></div>
        {selected.result?.externalAudit && <div className="version-audit-summary"><span>GPT-5.6 · VERSION {selected.version} AUDIT</span><b>{selected.result.externalAudit.analysis.verdict}</b><h4>{selected.result.externalAudit.analysis.headline}</h4><p>{selected.result.externalAudit.analysis.judgeTakeaway}</p></div>}
      </>}
      {(selected.status === 'queued' || selected.status === 'running') && <div className="experiment-running"><i /><span>Independent engines are training. You may continue exploring the baseline.</span></div>}
      {selected.error && <p className="experiment-message error">{selected.error}</p>}
      <div className="success-criteria"><span>PREREGISTERED PROPOSAL · VERIFIED ABOVE AFTER RUN</span>{selected.proposal.successCriteria.map((criterion) => <p key={criterion}>· {criterion}</p>)}</div>
    </div>}
    <footer>{user ? `Versions are private to ${user.email} and persist in PostgreSQL.` : 'Anonymous versions live only in this page session and disappear after refresh.'}</footer>
  </section>;
}
