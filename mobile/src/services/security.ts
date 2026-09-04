import { SecurityEvent, Permission } from './types';

const mockPermissions: Permission[] = [
  {
    id: 'perm-1',
    service: 'Google Drive',
    scope: 'Read & Write files',
    grantedAt: '2026-09-01T10:00:00Z',
    isTemporary: false,
  },
  {
    id: 'perm-2',
    service: 'Gmail',
    scope: 'Read emails, draft replies',
    grantedAt: '2026-09-01T10:00:00Z',
    isTemporary: false,
  },
  {
    id: 'perm-3',
    service: 'Google Calendar',
    scope: 'View and create events',
    grantedAt: '2026-09-01T10:00:00Z',
    isTemporary: false,
  },
  {
    id: 'perm-4',
    service: 'Laptop File Access',
    scope: 'Read files in Projects folder',
    grantedAt: '2026-09-04T15:10:00Z',
    expiresAt: '2026-09-04T16:10:00Z',
    taskId: 'task-1',
    isTemporary: true,
  },
];

const mockEvents: SecurityEvent[] = [
  {
    id: 'sec-1',
    type: 'sensitive_action',
    description: 'Presentation files accessed on Laptop',
    timestamp: '2026-09-04T15:18:00Z',
    severity: 'low',
  },
  {
    id: 'sec-2',
    type: 'access_granted',
    description: 'Temporary access to Laptop files',
    timestamp: '2026-09-04T15:10:00Z',
    severity: 'medium',
  },
  {
    id: 'sec-3',
    type: 'permission_expired',
    description: 'Browser Agent web access expired',
    timestamp: '2026-09-04T14:00:00Z',
    severity: 'low',
  },
];

let emergencyStopped = false;

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const securityService = {
  async getPermissions(): Promise<Permission[]> {
    await delay(300);
    return [...mockPermissions];
  },

  async getSecurityEvents(): Promise<SecurityEvent[]> {
    await delay(300);
    return [...mockEvents];
  },

  async revokePermission(id: string): Promise<void> {
    await delay(500);
    const idx = mockPermissions.findIndex(p => p.id === id);
    if (idx >= 0) {
      mockPermissions.splice(idx, 1);
    }
  },

  async emergencyStop(): Promise<void> {
    await delay(200);
    emergencyStopped = true;
  },

  async resumeFromEmergency(): Promise<void> {
    await delay(200);
    emergencyStopped = false;
  },

  isEmergencyStopped(): boolean {
    return emergencyStopped;
  },

  async getSecurityStatus(): Promise<{ status: 'protected' | 'warning' | 'critical'; message: string }> {
    await delay(200);
    if (emergencyStopped) {
      return { status: 'critical', message: 'All operations stopped' };
    }
    return { status: 'protected', message: 'All systems secure' };
  },
};
