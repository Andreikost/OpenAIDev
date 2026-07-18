import type { Ablation, Evaluation, State } from './types';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!response.ok) throw new Error(await response.text() || `Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const api = {
  state: () => request<State>('/api/state'),
  step: (steps: number) => request<State>('/api/step', { method: 'POST', body: JSON.stringify({ steps }) }),
  reset: (seed: number) => request<State>('/api/reset', { method: 'POST', body: JSON.stringify({ seed }) }),
  evaluate: () => request<Evaluation>('/api/evaluate', { method: 'POST' }),
  ablate: (organismId: string) => request<Ablation>('/api/ablate', { method: 'POST', body: JSON.stringify({ organism_id: organismId }) }),
};
