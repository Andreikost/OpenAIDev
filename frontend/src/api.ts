import type { Ablation, DrawingAudit, Evaluation, State } from './types';

const SESSION_STORAGE_KEY = 'colonymind-session-v1';
const existingSession = window.localStorage.getItem(SESSION_STORAGE_KEY);
const sessionId = existingSession ?? `cm_${crypto.randomUUID().replaceAll('-', '')}`;
if (!existingSession) window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');
  headers.set('X-ColonyMind-Session', sessionId);
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
};
