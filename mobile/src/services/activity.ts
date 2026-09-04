/**
 * The timeline: what JARVIS actually did, in plain English.
 *
 * These are observable actions recorded by the computer - never model
 * reasoning. The phone reads them; it does not write them, because an entry
 * that only the phone knows about would not be part of the shared record.
 */
import { request } from '../api/client';
import { RawEvent, toActivity } from '../api/mappers';
import { ActivityEntry } from './types';

export const activityService = {
  async getActivity(limit = 50): Promise<ActivityEntry[]> {
    const raw = await request<RawEvent[]>(`/api/activity?limit=${limit}`);
    return raw.map(toActivity);
  },

  async getRecentActivity(limit = 5): Promise<ActivityEntry[]> {
    return this.getActivity(limit);
  },
};
