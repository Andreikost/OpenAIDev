import { useState } from 'react';
import { api } from './api';
import type { ResearchAudit } from './types';

type Props = {
  enabled: boolean;
  stepCount: number;
  onBeforeAudit: () => void;
};

function readableError(error: unknown) {
  if (!(error instanceof Error)) return 'The research audit could not be completed.';
  if (error.message.includes('not configured')) return 'The GPT-5.6 auditor is not configured on this server.';
  return 'GPT-5.6 could not audit this snapshot. The learner was not modified.';
}

export function ResearchAuditorPanel({ enabled, stepCount, onBeforeAudit }: Props) {
  const [audit, setAudit] = useState<ResearchAudit | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function runAudit() {
    onBeforeAudit();
    setBusy(true);
    setError('');
    try {
      setAudit(await api.researchAudit());
    } catch (requestError) {
      setError(readableError(requestError));
    } finally {
      setBusy(false);
    }
  }

  return <section className="panel research-auditor-panel">
    <div className="panel-header research-auditor-header">
      <div>
        <p className="panel-title">GPT-5.6 Research Auditor</p>
        <span>Independent interpretation of a frozen, aggregate-only evidence snapshot.</span>
      </div>
      <span className="gpt-boundary-badge">OPENAI · EXTERNAL · READ ONLY</span>
    </div>

    <div className="research-auditor-intro">
      <div className="gpt-orb"><i /><i /><i /><b>5.6</b></div>
      <div>
        <strong>Let a second intelligence challenge the experiment.</strong>
        <p>GPT-5.6 sees metrics, structural counts, evaluation evidence, and declared limitations—never raw retinal pixels, cell prototypes, or a learning endpoint.</p>
      </div>
      <button className="primary" disabled={!enabled || busy} onClick={() => void runAudit()}>
        {busy ? 'Auditing frozen evidence…' : `Audit run at step ${stepCount}`}
      </button>
    </div>

    {error && <p className="research-audit-error">{error}</p>}
    {!audit && !error && <div className="research-audit-empty">
      <b>WHAT THE AUDITOR RETURNS</b>
      <span>Evidence-backed findings</span><span>Scientific risks</span><span>Three controlled next experiments</span><span>Publication readiness</span>
    </div>}

    {audit && <div className="research-audit-result">
      <div className="research-verdict">
        <div><span>{audit.model}</span><b className={`verdict-${audit.analysis.verdict.replaceAll(' ', '-')}`}>{audit.analysis.verdict}</b></div>
        <h2>{audit.analysis.headline}</h2>
        <p>{audit.analysis.judgeTakeaway}</p>
        <small>{audit.analysis.executiveSummary}</small>
      </div>

      <div className="research-findings">
        {audit.analysis.findings.map((finding, index) => <article key={`${finding.title}-${index}`}>
          <span>FINDING {String(index + 1).padStart(2, '0')}</span>
          <h3>{finding.title}</h3>
          <p>{finding.observation}</p>
          <ul>{finding.evidence.map((evidence) => <li key={evidence}>{evidence}</li>)}</ul>
          <small>{finding.interpretation}</small>
        </article>)}
      </div>

      <div className="research-next-grid">
        <article className="publication-card">
          <span>PUBLICATION READINESS</span>
          <strong>{audit.analysis.publicationReadiness.stage}</strong>
          <p><b>Strongest evidence</b>{audit.analysis.publicationReadiness.strongestEvidence}</p>
          <p><b>Still missing</b>{audit.analysis.publicationReadiness.missingEvidence}</p>
        </article>
        <article className="risk-card">
          <span>SCIENTIFIC RISKS</span>
          {audit.analysis.risks.map((risk) => <p key={risk.issue}><i className={`risk-${risk.severity}`}>{risk.severity}</i><b>{risk.issue}</b><small>{risk.whyItMatters}</small></p>)}
        </article>
      </div>

      <div className="experiment-roadmap">
        <span className="result-kicker">NEXT CONTROLLED EXPERIMENTS</span>
        <div>{audit.analysis.nextExperiments.map((experiment, index) => <article key={`${experiment.title}-${index}`}>
          <i>{String(index + 1).padStart(2, '0')} · {experiment.priority}</i>
          <h3>{experiment.title}</h3>
          <p><b>Hypothesis</b>{experiment.hypothesis}</p>
          <p><b>Protocol</b>{experiment.protocol}</p>
          <p><b>Success</b>{experiment.successMetric}</p>
        </article>)}</div>
      </div>

      <div className="research-boundary-proof">
        <span><b>STATE PRESERVED</b>{audit.snapshotExtractionHashBefore} = {audit.snapshotExtractionHashAfter}</span>
        <span><b>NO WRITE PATH</b>{audit.learningWriteAccess ? 'write access detected' : 'learning write access: false'}</span>
        <span><b>NO RAW RETINA</b>{audit.rawRetinaShared ? 'shared' : 'raw pixels: not shared'}</span>
        <span><b>RESOURCE CLAIM</b>{audit.analysis.resourceAssessment.status}</span>
        {audit.cached && <span><b>COST CONTROL</b>cached audit reused</span>}
      </div>
    </div>}
  </section>;
}
