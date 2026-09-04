// ==========================================
// JARVIS — Shared Type Definitions
// ==========================================

// ---- Tasks ----
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'waiting_approval';

export interface TaskStep {
  id: string;
  title: string;
  status: TaskStatus;
  detail?: string;
  agentName?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  progress: number; // 0–100
  steps: TaskStep[];
  createdAt: string;
  updatedAt: string;
  result?: string;
  error?: string;
  requiresApproval?: boolean;
  approvalId?: string;
}

// ---- Devices ----
export type DeviceStatus = 'online' | 'offline' | 'connected';
export type DeviceType = 'laptop' | 'desktop' | 'phone' | 'server' | 'tablet';

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  status: DeviceStatus;
  lastSeen: string;
  os?: string;
  capabilities?: string[];
}

// ---- Files ----
export type FileSource = 'computer' | 'phone' | 'drive' | 'server';
export type FileType = 'presentation' | 'document' | 'pdf' | 'spreadsheet' | 'image' | 'archive' | 'code' | 'folder' | 'other';

export interface FileItem {
  id: string;
  name: string;
  type: FileType;
  source: FileSource;
  sourcePath?: string;
  size?: string;
  modifiedAt: string;
  modifiedRelative?: string;
}

// ---- Activity ----
export type ActivityType = 'info' | 'success' | 'warning' | 'error' | 'approval';

export interface ActivityEntry {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp: string;
  timeLabel: string;
  taskId?: string;
}

// ---- Agents ----
export type AgentStatus = 'active' | 'idle' | 'busy' | 'paused' | 'quarantined' | 'error';
export type AgentFramework = 'native' | 'openclaw' | 'langgraph' | 'crewai' | 'mcp' | 'custom';

export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: AgentStatus;
  framework: AgentFramework;
  tasksCompleted: number;
  failureRate: number;
  lastActive?: string;
  quarantineReason?: string;
}

// ---- Approvals ----
export type ApprovalAction = 'send_email' | 'delete_files' | 'modify_document' | 'github_change' | 'publish' | 'financial' | 'external_access';

export interface ApprovalRequest {
  id: string;
  taskId: string;
  title: string;
  description: string;
  action: ApprovalAction;
  metadata: Record<string, string | number>;
  createdAt: string;
  status: 'pending' | 'approved' | 'denied';
  expiresAt?: string;
}

// ---- Google ----
export interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  modifiedTime: string;
  webViewLink?: string;
  iconLink?: string;
  size?: string;
}

export interface Email {
  id: string;
  from: string;
  subject: string;
  snippet: string;
  date: string;
  isRead: boolean;
  isImportant: boolean;
}

export interface CalendarEvent {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  location?: string;
  attendees?: string[];
}

// ---- Security ----
export interface SecurityEvent {
  id: string;
  type: 'access_granted' | 'access_revoked' | 'login' | 'sensitive_action' | 'permission_expired';
  description: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high';
}

export interface Permission {
  id: string;
  service: string;
  scope: string;
  grantedAt: string;
  expiresAt?: string;
  taskId?: string;
  isTemporary: boolean;
}

// ---- User ----
export interface User {
  id: string;
  name: string;
  initials: string;
  workspace: string;
}

// ---- Memory ----
export interface MemoryItem {
  id: string;
  type: 'project' | 'preference' | 'context' | 'file_reference';
  key: string;
  value: string;
  lastAccessed: string;
}
