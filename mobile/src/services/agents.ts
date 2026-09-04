import { Agent, AgentStatus } from './types';

const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: 'Coding Agent',
    description: 'Writes, reviews, and tests code',
    icon: 'code-slash',
    status: 'idle',
    framework: 'native',
    tasksCompleted: 23,
    failureRate: 0.02,
  },
  {
    id: 'agent-2',
    name: 'Research Agent',
    description: 'Searches the web and analyzes information',
    icon: 'search',
    status: 'busy',
    framework: 'native',
    tasksCompleted: 45,
    failureRate: 0.01,
  },
  {
    id: 'agent-3',
    name: 'Writing Agent',
    description: 'Creates and edits documents and content',
    icon: 'create-outline',
    status: 'busy',
    framework: 'native',
    tasksCompleted: 31,
    failureRate: 0.03,
  },
  {
    id: 'agent-4',
    name: 'File Agent',
    description: 'Manages files across devices',
    icon: 'folder-open-outline',
    status: 'idle',
    framework: 'native',
    tasksCompleted: 67,
    failureRate: 0.01,
  },
  {
    id: 'agent-5',
    name: 'Browser Agent',
    description: 'Navigates and interacts with websites',
    icon: 'globe-outline',
    status: 'idle',
    framework: 'mcp',
    tasksCompleted: 18,
    failureRate: 0.05,
  },
  {
    id: 'agent-6',
    name: 'Google Agent',
    description: 'Works with Google Workspace',
    icon: 'logo-google',
    status: 'active',
    framework: 'native',
    tasksCompleted: 52,
    failureRate: 0.02,
  },
  {
    id: 'agent-7',
    name: 'Computer Agent',
    description: 'Controls connected computers',
    icon: 'desktop-outline',
    status: 'active',
    framework: 'native',
    tasksCompleted: 34,
    failureRate: 0.04,
  },
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const agentsService = {
  async getAgents(): Promise<Agent[]> {
    await delay(300);
    return [...mockAgents];
  },

  async getAgent(id: string): Promise<Agent | undefined> {
    await delay(200);
    return mockAgents.find(a => a.id === id);
  },

  async quarantineAgent(id: string, reason: string): Promise<void> {
    await delay(500);
    const agent = mockAgents.find(a => a.id === id);
    if (agent) {
      agent.status = 'quarantined';
      agent.quarantineReason = reason;
    }
  },

  async resumeAgent(id: string): Promise<void> {
    await delay(500);
    const agent = mockAgents.find(a => a.id === id);
    if (agent) {
      agent.status = 'idle';
      agent.quarantineReason = undefined;
    }
  },
};
