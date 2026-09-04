import { ApprovalRequest } from './types';

const mockApprovals: ApprovalRequest[] = [
  {
    id: 'apr-1',
    taskId: 'task-1',
    title: 'Update your presentation',
    description: "I'm ready to update your Hackwave presentation with the latest research findings.",
    action: 'modify_document',
    metadata: {
      'Document': 'Hackwave_Final.pptx',
      'Changes': '12 slides updated',
      'Sources added': '3',
    },
    createdAt: '2026-09-04T15:25:00Z',
    status: 'pending',
  },
  {
    id: 'apr-2',
    taskId: 'task-2',
    title: 'Merge project changes',
    description: "Ready to merge your project changes to the main branch.",
    action: 'github_change',
    metadata: {
      'Repository': 'Hackwave',
      'Tests': '142 passed',
      'Files changed': '8',
    },
    createdAt: '2026-09-04T15:20:00Z',
    status: 'pending',
  },
];

let approvals = [...mockApprovals];
let nextId = 3;

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const approvalsService = {
  async getPendingApprovals(): Promise<ApprovalRequest[]> {
    await delay(300);
    return approvals.filter(a => a.status === 'pending');
  },

  async getAllApprovals(): Promise<ApprovalRequest[]> {
    await delay(300);
    return [...approvals];
  },

  async getApprovalCount(): Promise<number> {
    return approvals.filter(a => a.status === 'pending').length;
  },

  async approve(id: string): Promise<void> {
    await delay(800);
    const approval = approvals.find(a => a.id === id);
    if (approval) {
      approval.status = 'approved';
    }
  },

  async deny(id: string): Promise<void> {
    await delay(300);
    const approval = approvals.find(a => a.id === id);
    if (approval) {
      approval.status = 'denied';
    }
  },

  async createApproval(approval: Omit<ApprovalRequest, 'id' | 'status'>): Promise<ApprovalRequest> {
    const newApproval: ApprovalRequest = {
      ...approval,
      id: `apr-${nextId++}`,
      status: 'pending',
    };
    approvals.unshift(newApproval);
    return newApproval;
  },
};
