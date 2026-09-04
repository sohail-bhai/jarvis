/**
 * Decisions the computer is holding until you answer.
 *
 * This is the point of carrying JARVIS in a pocket: work pauses on the
 * computer, the question arrives on the phone, and answering it here releases
 * exactly the access that was being asked for.
 */
import { request } from '../api/client';
import { RawApproval, toApproval } from '../api/mappers';
import { ApprovalRequest } from './types';

export const approvalsService = {
  async getPendingApprovals(): Promise<ApprovalRequest[]> {
    const raw = await request<RawApproval[]>('/api/approvals');
    return raw.map(toApproval);
  },

  async getAllApprovals(): Promise<ApprovalRequest[]> {
    const raw = await request<RawApproval[]>('/api/approvals?pending_only=false');
    return raw.map(toApproval);
  },

  async getApprovalCount(): Promise<number> {
    const pending = await this.getPendingApprovals();
    return pending.length;
  },

  /** Approve: the held work resumes and the access is released. */
  async approve(id: string): Promise<void> {
    await request(`/api/approvals/${id}`, { method: 'POST', body: { approved: true } });
  },

  /** Decline: the task stops. Nothing is granted. */
  async deny(id: string): Promise<void> {
    await request(`/api/approvals/${id}`, { method: 'POST', body: { approved: false } });
  },
};
