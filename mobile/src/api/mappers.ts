/**
 * Turning control-plane JSON into the shapes the screens already render.
 *
 * The server speaks in the vocabulary of the control plane - goals, steps,
 * helpers, events. The phone's components were written against their own
 * types. Translating in one place means neither side has to change to suit
 * the other, and a server field that is renamed later breaks here rather than
 * in nine screens.
 */
import {
  ActivityEntry,
  ActivityType,
  Agent,
  AgentFramework,
  AgentStatus,
  ApprovalAction,
  ApprovalRequest,
  Device,
  DeviceType,
  Permission,
  Task,
  TaskStatus,
  TaskStep,
} from '../services/types';

// ---- server payloads ----

export interface RawStep {
  id: string;
  task_id: string;
  position: number;
  label: string;
  status: string;
  detail: string;
  depends_on: number[];
  agent_id: string;
  capability: string;
  attempts: number;
  artifacts: string[];
}

export interface RawTask {
  id: string;
  goal: string;
  status: string;
  helper_id: string;
  device_id: string;
  summary: string;
  created_at: number;
  updated_at: number;
  steps?: RawStep[];
  progress?: number;      // 0-1 from the server, 0-100 on the phone
  current_step?: string;
}

export interface RawEvent {
  id: string;
  task_id: string;
  type: string;
  message: string;
  actor: string;
  timestamp: number;
  agent_id: string;
  capability: string;
  risk: string;
  approval_id: string;
  result: string;
}

export interface RawApproval {
  id: string;
  task_id: string;
  action: string;
  question: string;
  reason: string;
  impact: string;
  status: string;
  created_at: number;
  capability: string;
}

export interface RawDevice {
  id: string;
  name: string;
  kind: string;
  platform: string;
  status: string;
  last_seen: number;
  paired_at: number;
  capabilities: string[];
}

export interface RawAgent {
  id: string;
  name: string;
  framework: string;
  status: string;
  capabilities: string[];
  last_active: number;
  success_count: number;
  error_count: number;
  error_rate: number;
  enabled: boolean;
}

export interface RawPermission {
  id: string;
  task_id: string;
  resource: string;
  actions: string[];
  status: string;
  granted_at: number;
  expires_at: number;
  seconds_remaining: number;
}

export interface RawStatus {
  stopped: boolean;
  devices: number;
  helpers: number;
  agents_offline: number;
  agents_quarantined: number;
  active_tasks: number;
  pending_approvals: number;
  temporary_access: number;
}

// ---- time ----

/** The server sends seconds since the epoch; JavaScript wants milliseconds. */
export function toIso(seconds: number): string {
  if (!seconds) return '';
  return new Date(seconds * 1000).toISOString();
}

export function timeLabel(seconds: number): string {
  if (!seconds) return '';
  return new Date(seconds * 1000).toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function relativeLabel(seconds: number): string {
  if (!seconds) return '';
  const elapsed = Date.now() / 1000 - seconds;
  if (elapsed < 60) return 'just now';
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)} min ago`;
  if (elapsed < 86400) return `${Math.floor(elapsed / 3600)} hr ago`;
  if (elapsed < 172800) return 'yesterday';
  return `${Math.floor(elapsed / 86400)} days ago`;
}

// ---- tasks ----

const STEP_STATUS: Record<string, TaskStatus> = {
  pending: 'pending',
  active: 'running',
  done: 'completed',
  failed: 'failed',
  skipped: 'cancelled',
};

const TASK_STATUS: Record<string, TaskStatus> = {
  pending: 'pending',
  running: 'running',
  waiting_approval: 'waiting_approval',
  completed: 'completed',
  failed: 'failed',
  cancelled: 'cancelled',
};

export function toStep(raw: RawStep): TaskStep {
  return {
    id: raw.id,
    title: raw.label,
    status: STEP_STATUS[raw.status] ?? 'pending',
    detail: raw.detail || undefined,
    agentName: raw.agent_id || undefined,
  };
}

export function toTask(raw: RawTask): Task {
  const status = TASK_STATUS[raw.status] ?? 'pending';
  const steps = (raw.steps ?? []).map(toStep);

  // The list endpoint returns tasks without steps, so progress may be absent.
  // Deriving it from the steps we do have beats showing a bar stuck at zero.
  const ratio =
    raw.progress !== undefined
      ? raw.progress
      : steps.length
        ? steps.filter(step => step.status === 'completed').length / steps.length
        : status === 'completed'
          ? 1
          : 0;

  return {
    id: raw.id,
    title: raw.goal,
    description: raw.summary || raw.current_step || describeStatus(status),
    status,
    progress: Math.round(ratio * 100),
    steps,
    createdAt: toIso(raw.created_at),
    updatedAt: toIso(raw.updated_at),
    result: raw.summary || undefined,
    error: status === 'failed' ? raw.summary || 'This task did not finish.' : undefined,
    requiresApproval: status === 'waiting_approval',
  };
}

function describeStatus(status: TaskStatus): string {
  switch (status) {
    case 'running':
      return 'JARVIS is working on this.';
    case 'waiting_approval':
      return 'Waiting for your approval.';
    case 'completed':
      return 'Finished.';
    case 'failed':
      return 'This task did not finish.';
    case 'cancelled':
      return 'You stopped this task.';
    default:
      return 'Waiting to start.';
  }
}

// ---- activity ----

/** Which events read as good news, a warning, or a problem in the timeline. */
const EVENT_TONE: Record<string, ActivityType> = {
  task_completed: 'success',
  step_finished: 'success',
  permission_granted: 'success',
  approval_resolved: 'success',
  task_failed: 'error',
  agent_offline: 'error',
  agent_quarantined: 'error',
  capability_denied: 'warning',
  task_cancelled: 'warning',
  emergency_stop: 'warning',
  permission_revoked: 'warning',
  approval_requested: 'approval',
};

export function toActivity(raw: RawEvent): ActivityEntry {
  return {
    id: raw.id,
    type: raw.result === 'failed' ? 'error' : (EVENT_TONE[raw.type] ?? 'info'),
    title: raw.message,
    description: raw.capability || undefined,
    timestamp: toIso(raw.timestamp),
    timeLabel: timeLabel(raw.timestamp),
    taskId: raw.task_id || undefined,
  };
}

// ---- approvals ----

/**
 * The server's action is a free-text label, because it describes whatever the
 * agent is about to do. The phone renders one of a fixed set of icons, so the
 * label is matched to the closest one and the real wording is kept in view.
 */
function toApprovalAction(action: string, capability: string): ApprovalAction {
  const text = `${action} ${capability}`.toLowerCase();
  if (text.includes('mail') || text.includes('send')) return 'send_email';
  if (text.includes('delete') || text.includes('remove')) return 'delete_files';
  if (text.includes('git') || text.includes('merge') || text.includes('commit')) return 'github_change';
  if (text.includes('deploy') || text.includes('publish')) return 'publish';
  if (text.includes('pay') || text.includes('purchase')) return 'financial';
  if (text.includes('write') || text.includes('document') || text.includes('doc')) return 'modify_document';
  return 'external_access';
}

export function toApproval(raw: RawApproval): ApprovalRequest {
  const metadata: Record<string, string | number> = {};
  if (raw.impact) metadata['What changes'] = raw.impact;
  if (raw.reason) metadata['Why'] = raw.reason;
  if (raw.capability) metadata['Access'] = raw.capability;

  return {
    id: raw.id,
    taskId: raw.task_id,
    title: raw.action || 'JARVIS needs your approval',
    description: raw.question,
    action: toApprovalAction(raw.action, raw.capability),
    metadata,
    createdAt: toIso(raw.created_at),
    status: raw.status === 'declined' ? 'denied' : (raw.status as 'pending' | 'approved'),
  };
}

// ---- devices ----

const DEVICE_TYPE: Record<string, DeviceType> = {
  computer: 'desktop',
  laptop: 'laptop',
  phone: 'phone',
  tablet: 'tablet',
  server: 'server',
  nas: 'server',
  cloud: 'server',
};

export function toDevice(raw: RawDevice): Device {
  return {
    id: raw.id,
    name: raw.name,
    type: DEVICE_TYPE[raw.kind] ?? 'desktop',
    status: raw.status === 'online' ? 'online' : 'offline',
    lastSeen: relativeLabel(raw.last_seen),
    os: raw.platform || undefined,
    capabilities: raw.capabilities,
  };
}

// ---- agents ----

const AGENT_STATUS: Record<string, AgentStatus> = {
  idle: 'idle',
  working: 'busy',
  offline: 'error',
  quarantined: 'quarantined',
};

const AGENT_ICONS: Record<string, string> = {
  research: 'search-outline',
  web: 'globe-outline',
  browser: 'globe-outline',
  code: 'code-slash-outline',
  coding: 'code-slash-outline',
  files: 'folder-outline',
  filesystem: 'folder-outline',
  google: 'mail-outline',
  documents: 'document-text-outline',
};

function iconFor(capabilities: string[]): string {
  for (const capability of capabilities) {
    const key = capability.split('.')[0];
    if (AGENT_ICONS[key]) return AGENT_ICONS[key];
  }
  return 'sparkles-outline';
}

export function toAgent(raw: RawAgent): Agent {
  const capabilities = raw.capabilities ?? [];
  return {
    id: raw.id,
    name: raw.name,
    description: capabilities.length ? capabilities.join(', ') : 'General purpose',
    icon: iconFor(capabilities),
    status: raw.enabled === false ? 'paused' : (AGENT_STATUS[raw.status] ?? 'idle'),
    framework: (raw.framework as AgentFramework) ?? 'native',
    tasksCompleted: raw.success_count ?? 0,
    failureRate: raw.error_rate ?? 0,
    lastActive: relativeLabel(raw.last_active),
    quarantineReason:
      raw.status === 'quarantined' ? 'JARVIS stopped this helper.' : undefined,
  };
}

// ---- permissions ----

export function toPermission(raw: RawPermission): Permission {
  return {
    id: raw.id,
    service: raw.resource,
    scope: (raw.actions ?? []).join(', '),
    grantedAt: toIso(raw.granted_at),
    expiresAt: toIso(raw.expires_at),
    taskId: raw.task_id || undefined,
    isTemporary: true,
  };
}
