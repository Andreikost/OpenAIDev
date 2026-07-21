import type { Ablation, AuthConfig, AuthSession, AuthUser, BaselineManifest, DrawingAudit, Evaluation, ExperimentRecord, ResearchAudit, State } from './types';

const SESSION_STORAGE_KEY = 'colonymind-session-v1';
const existingSession = window.localStorage.getItem(SESSION_STORAGE_KEY);
const sessionId = existingSession ?? `cm_${crypto.randomUUID().replaceAll('-', '')}`;
if (!existingSession) window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
const experimentWorkspaceId = `exp_${crypto.randomUUID().replaceAll('-', '')}`;
const AUTH_TOKEN_KEY = 'colonymind-google-session-v1';

export function authToken() { return window.localStorage.getItem(AUTH_TOKEN_KEY); }
export function storeAuthToken(token: string) { window.localStorage.setItem(AUTH_TOKEN_KEY, token); }
export function clearAuthToken() { window.localStorage.removeItem(AUTH_TOKEN_KEY); }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');
  headers.set('X-ColonyMind-Session', sessionId);
  headers.set('X-Experiment-Workspace', experimentWorkspaceId);
  const token = authToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(path, { ...init, headers });
  if (!response.ok) throw new Error(await response.text() || `Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const api = {
  state: () => request<State>('/api/state'),
  step: (steps: number) => request<State>('/api/step', { method: 'POST', body: JSON.stringify({ steps }) }),
  reset: (seed: number) => request<State>('/api/reset', { method: 'POST', body: JSON.stringify({ seed }) }),
  evaluate: () => request<Evaluation>('/api/evaluate', { method: 'POST' }),
  auditDrawing: (pixels: number[]) => request<DrawingAudit>('/api/audit-drawing', { method: 'POST', body: JSON.stringify({ pixels }) }),
  ablate: (organismId: string) => request<Ablation>('/api/ablate', { method: 'POST', body: JSON.stringify({ organism_id: organismId }) }),
  report: () => request<Record<string, unknown>>('/api/report'),
  researchAudit: () => request<ResearchAudit>('/api/research-audit', { method: 'POST' }),
  authConfig: () => request<AuthConfig>('/api/auth/config'),
  authMe: () => request<{ user: AuthUser | null }>('/api/auth/me'),
  googleLogin: (accessToken: string) => request<AuthSession>('/api/auth/google', { method: 'POST', body: JSON.stringify({ accessToken }) }),
  baseline: () => request<BaselineManifest>('/api/experiments/baseline'),
  experiments: () => request<ExperimentRecord[]>('/api/experiments'),
  createExperiment: (instruction: string, parentId?: string) => request<ExperimentRecord>('/api/experiments', { method: 'POST', body: JSON.stringify({ instruction, parentId: parentId || null }) }),
  runExperiment: (id: string) => request<ExperimentRecord>(`/api/experiments/${id}/run`, { method: 'POST' }),
  deleteExperiment: (id: string) => request<{ deleted: boolean; baselinePreserved: boolean }>(`/api/experiments/${id}`, { method: 'DELETE' }),
};
