/**
 * Access, and the ability to take it all back.
 *
 * Temporary grants and the emergency stop live on the computer, so stopping
 * everything from the phone stops it everywhere - the desktop app sees the
 * same latch.
 */
import { request } from '../api/client';
import { RawEvent, RawPermission, RawStatus, toPermission, toIso } from '../api/mappers';
import { Permission, SecurityEvent } from './types';

/** Timeline events that belong on a security screen rather than a feed. */
const SECURITY_EVENTS = [
  'permission_granted',
  'permission_revoked',
  'capability_denied',
  'approval_resolved',
  'emergency_stop',
  'agent_quarantined',
].join(',');

const EVENT_KIND: Record<string, SecurityEvent['type']> = {
  permission_granted: 'access_granted',
  permission_revoked: 'access_revoked',
  capability_denied: 'sensitive_action',
  approval_resolved: 'sensitive_action',
  emergency_stop: 'sensitive_action',
  agent_quarantined: 'sensitive_action',
};

const EVENT_SEVERITY: Record<string, SecurityEvent['severity']> = {
  permission_granted: 'low',
  approval_resolved: 'low',
  permission_revoked: 'medium',
  capability_denied: 'high',
  emergency_stop: 'high',
  agent_quarantined: 'high',
};

export const securityService = {
  async getPermissions(): Promise<Permission[]> {
    const raw = await request<RawPermission[]>('/api/permissions');
    return raw.map(toPermission);
  },

  async getSecurityEvents(): Promise<SecurityEvent[]> {
    const raw = await request<RawEvent[]>(`/api/activity?limit=40&types=${SECURITY_EVENTS}`);
    return raw.map(event => ({
      id: event.id,
      type: EVENT_KIND[event.type] ?? 'sensitive_action',
      description: event.message,
      timestamp: toIso(event.timestamp),
      severity: EVENT_SEVERITY[event.type] ?? 'low',
    }));
  },

  async revokePermission(id: string): Promise<void> {
    await request(`/api/permissions/${id}`, { method: 'DELETE' });
  },

  /**
   * Stop everything: active work is cancelled, every temporary grant is
   * revoked, pending approvals are declined. Nothing is deleted, and the
   * computer refuses new work until it is resumed.
   */
  async emergencyStop(): Promise<void> {
    await request('/api/emergency-stop', { method: 'POST' });
  },

  async resumeFromEmergency(): Promise<void> {
    await request('/api/resume', { method: 'POST' });
  },

  async getStatus(): Promise<RawStatus> {
    return request<RawStatus>('/api/status');
  },

  async getSecurityStatus(): Promise<{
    status: 'protected' | 'warning' | 'critical';
    message: string;
    devices: number;
    pendingApprovals: number;
    temporaryAccess: number;
    stopped: boolean;
  }> {
    const status = await this.getStatus();

    // An emergency stop is not a failure, but it is the most important thing
    // on the screen while it is latched.
    const level = status.stopped
      ? 'critical'
      : status.agents_quarantined > 0
        ? 'warning'
        : 'protected';

    const message = status.stopped
      ? 'Everything is stopped. JARVIS will not start new work.'
      : status.agents_quarantined > 0
        ? `${status.agents_quarantined} helper is stopped and being kept aside.`
        : "You're protected";

    return {
      status: level,
      message,
      devices: status.devices,
      pendingApprovals: status.pending_approvals,
      temporaryAccess: status.temporary_access,
      stopped: status.stopped,
    };
  },
};
