/**
 * The AI helpers the computer can hand work to.
 *
 * Health here is observed rather than guessed: the counts and the error rate
 * come from work that actually ran, so a helper that looks fine but keeps
 * failing shows as failing.
 */
import { request } from '../api/client';
import { RawAgent, toAgent } from '../api/mappers';
import { Agent } from './types';

export const agentsService = {
  async getAgents(): Promise<Agent[]> {
    const raw = await request<RawAgent[]>('/api/agents');
    return raw.map(toAgent);
  },

  async getAgent(id: string): Promise<Agent | undefined> {
    const raw = await request<RawAgent>(`/api/agents/${id}`);
    return toAgent(raw);
  },

  /**
   * Stop a helper now: its work is cancelled, its access revoked, and it is
   * given nothing further. Its history stays on the timeline.
   */
  async quarantineAgent(id: string): Promise<void> {
    await request(`/api/agents/${id}/kill`, { method: 'POST' });
  },

  async resumeAgent(id: string): Promise<void> {
    await request(`/api/agents/${id}/enable`, { method: 'POST' });
  },
};
