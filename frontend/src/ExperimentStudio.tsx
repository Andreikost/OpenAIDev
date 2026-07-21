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

  async function createAndRun() {
    if (!canAudit) { setMessage('Train the ecosystem before deriving an experiment.'); return; }
    setBusy(true);
    try {
      if (!auditIsCurrent) {
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

  async function remove(record: ExperimentRecord) {
    await api.deleteExperiment(record.id);
    setExperiments((items) => items.filter((item) => item.id !== record.id));
    if (selectedId === record.id) setSelectedId(null);
    setMessage(`Version ${record.version} deleted. Baseline v1 is still preserved.`);
  }

  const aggregate = selected?.result?.aggregate;
  return <section className="panel experiment-studio">
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
        <div className="experiment-compose-actions">
          <label>Derive from<select value={parentId} onChange={(event) => setParentId(event.target.value)}><option value={baseline?.id ?? 'colonymind-build-week-baseline-v1'}>Baseline v1</option>{experiments.map((item) => <option key={item.id} value={item.id}>Version {item.version} · {item.proposal.shortLabel}</option>)}</select></label>
          <button className="primary" disabled={!canAudit || busy} onClick={() => void createAndRun()}>{busy ? 'Auditing & designing…' : selected ? (auditIsCurrent ? 'Create & run variant' : 'Refresh audit & run variant') : (auditIsCurrent ? 'Implement auditor experiment' : 'Refresh audit & implement')}</button>
        </div>
        {!canAudit && <small className="experiment-gate">Train the ecosystem first.</small>}
        {canAudit && !audit && <small className="experiment-gate">This action will freeze and audit the current state before creating the version.</small>}
        {canAudit && audit && !auditIsCurrent && <small className="experiment-gate">The ecosystem advanced after this audit. This action will refresh the audit automatically before branching.</small>}
        {message && <p className="experiment-message">{message}</p>}
      </div>

      <div className="version-rail">
        <article className="version-card baseline selected"><span>BASE</span><b>Baseline v1</b><small>Always preserved</small></article>
        {experiments.map((record) => <article key={record.id} className={`version-card ${selected?.id === record.id ? 'selected' : ''}`} onClick={() => { setSelectedId(record.id); setParentId(record.id); }}>
          <span>V{record.version} · {record.status}</span><b>{record.proposal.shortLabel}</b><small>{record.proposal.protocol.seeds.length} seeds · {record.proposal.protocol.trainingSteps} steps · {record.proposal.protocol.nuisanceProfile}</small>
          <button aria-label={`Delete version ${record.version}`} onClick={(event) => { event.stopPropagation(); void remove(record); }}>×</button>
        </article>)}
      </div>
    </div>

    {selected && <div className="experiment-detail">
      <div className="experiment-detail-head"><div><span>VERSION {selected.version} · {selected.status}</span><h3>{selected.proposal.title}</h3><p>{selected.proposal.hypothesis}</p></div><b>{selected.persistent ? 'SAVED' : 'TEMPORARY'}</b></div>
      <div className="protocol-strip"><span><b>TYPE</b>{selected.proposal.protocol.experimentType.replaceAll('_', ' ')}</span><span><b>SEEDS</b>{selected.proposal.protocol.seeds.join(', ')}</span><span><b>TRAINING</b>{selected.proposal.protocol.trainingSteps} steps</span><span><b>EVALUATION</b>{selected.proposal.protocol.samplesPerShape * 3} samples · {selected.proposal.protocol.nuisanceProfile}</span></div>
      {selected.status === 'completed' && aggregate && <>
        <div className="experiment-metrics"><article><span>PURITY</span><strong>{metric(aggregate.purity.mean)}</strong><small>{metric(aggregate.purity.min)}–{metric(aggregate.purity.max)}</small></article><article><span>NMI</span><strong>{metric(aggregate.nmi.mean)}</strong><small>community completeness</small></article><article><span>ARI</span><strong>{metric(aggregate.ari.mean)}</strong><small>chance-adjusted agreement</small></article><article><span>FRAGMENTATION</span><strong>{metric(aggregate.fragmentation.mean)}</strong><small>1.0 ≈ one community/class</small></article></div>
        <div className="experiment-preserved"><b>{selected.result?.baselinePreserved ? 'BASELINE PRESERVED' : 'VERIFY RESULT'}</b><span>{selected.result?.interpretationBoundary}</span></div>
      </>}
      {(selected.status === 'queued' || selected.status === 'running') && <div className="experiment-running"><i /><span>Independent engines are training. You may continue exploring the baseline.</span></div>}
      {selected.error && <p className="experiment-message error">{selected.error}</p>}
      <div className="success-criteria"><span>SUCCESS CRITERIA</span>{selected.proposal.successCriteria.map((criterion) => <p key={criterion}>✓ {criterion}</p>)}</div>
    </div>}
    <footer>{user ? `Versions are private to ${user.email} and persist in PostgreSQL.` : 'Anonymous versions live only in this page session and disappear after refresh.'}</footer>
  </section>;
}
