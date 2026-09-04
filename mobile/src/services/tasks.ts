import { Task, TaskStatus, TaskStep } from './types';

// Simulated task data
const mockTasks: Task[] = [
  {
    id: 'task-1',
    title: 'Prepare presentation',
    description: 'Researching and updating slides...',
    status: 'running',
    progress: 65,
    steps: [
      { id: 's1', title: 'Searching for relevant files', status: 'completed', agentName: 'File Agent', completedAt: '3:18 PM' },
      { id: 's2', title: 'Researching latest information', status: 'completed', agentName: 'Research Agent', completedAt: '3:20 PM' },
      { id: 's3', title: 'Updating presentation slides', status: 'running', agentName: 'Writing Agent' },
      { id: 's4', title: 'Upload to Google Drive', status: 'pending', agentName: 'Google Agent' },
    ],
    createdAt: '2026-09-04T15:10:00Z',
    updatedAt: '2026-09-04T15:25:00Z',
  },
  {
    id: 'task-2',
    title: 'Run tests on project',
    description: 'Running tests...',
    status: 'running',
    progress: 20,
    steps: [
      { id: 's1', title: 'Connecting to laptop', status: 'completed', agentName: 'Computer Agent', completedAt: '3:22 PM' },
      { id: 's2', title: 'Running test suite', status: 'running', agentName: 'Coding Agent' },
      { id: 's3', title: 'Collecting results', status: 'pending' },
    ],
    createdAt: '2026-09-04T15:22:00Z',
    updatedAt: '2026-09-04T15:24:00Z',
  },
  {
    id: 'task-3',
    title: 'Organize my files',
    description: 'Completed - 2 hours ago',
    status: 'completed',
    progress: 100,
    steps: [
      { id: 's1', title: 'Scanning file structure', status: 'completed', agentName: 'File Agent' },
      { id: 's2', title: 'Categorizing documents', status: 'completed', agentName: 'File Agent' },
      { id: 's3', title: 'Moving files to organized folders', status: 'completed', agentName: 'File Agent' },
    ],
    createdAt: '2026-09-04T13:00:00Z',
    updatedAt: '2026-09-04T13:15:00Z',
    result: 'Organized 47 files into 8 folders',
  },
  {
    id: 'task-4',
    title: 'Research AI frameworks',
    description: 'Completed - 4 hours ago',
    status: 'completed',
    progress: 100,
    steps: [
      { id: 's1', title: 'Searching the web', status: 'completed', agentName: 'Browser Agent' },
      { id: 's2', title: 'Reading documentation', status: 'completed', agentName: 'Research Agent' },
      { id: 's3', title: 'Preparing summary', status: 'completed', agentName: 'Writing Agent' },
    ],
    createdAt: '2026-09-04T11:00:00Z',
    updatedAt: '2026-09-04T11:30:00Z',
    result: 'Summary of 5 AI agent frameworks prepared',
  },
];

let tasks = [...mockTasks];
let nextId = 5;

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const tasksService = {
  async getTasks(): Promise<Task[]> {
    await delay(300);
    return [...tasks];
  },

  async getActiveTasks(): Promise<Task[]> {
    await delay(200);
    return tasks.filter(t => t.status === 'running' || t.status === 'pending' || t.status === 'waiting_approval');
  },

  async getCompletedTasks(): Promise<Task[]> {
    await delay(200);
    return tasks.filter(t => t.status === 'completed' || t.status === 'failed' || t.status === 'cancelled');
  },

  async getTask(id: string): Promise<Task | undefined> {
    await delay(200);
    return tasks.find(t => t.id === id);
  },

  async createTask(title: string, description: string): Promise<Task> {
    await delay(500);
    const task: Task = {
      id: `task-${nextId++}`,
      title,
      description,
      status: 'running',
      progress: 0,
      steps: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    tasks.unshift(task);
    return task;
  },

  async cancelTask(id: string): Promise<void> {
    await delay(100);
    const task = tasks.find(t => t.id === id);
    if (task) {
      task.status = 'cancelled';
      task.error = 'Task was cancelled by user.';
      task.updatedAt = new Date().toISOString();
      if (task.steps) {
        task.steps = task.steps.map(s => {
          if (s.status === 'running' || s.status === 'pending') {
            return { ...s, status: 'failed' };
          }
          return s;
        });
      }
      // Import dynamically or require jarvisService to cancel timeouts
      try {
        const { jarvisService } = require('./jarvis');
        jarvisService.cancelTaskTimeouts(id);
      } catch (e) {}

      try {
        const { activityService } = require('./activity');
        await activityService.addActivity({
          type: 'warning',
          title: `Cancelled task: "${task.title}"`,
          timestamp: new Date().toISOString(),
          timeLabel: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        });
      } catch (e) {}
    }
  },

  async updateTaskProgress(id: string, progress: number, status?: TaskStatus): Promise<void> {
    const task = tasks.find(t => t.id === id);
    if (task) {
      task.progress = progress;
      if (status) task.status = status;
      task.updatedAt = new Date().toISOString();
    }
  },

  // Simulate task progress for demo
  simulateProgress(id: string, onUpdate: (task: Task) => void): () => void {
    let cancelled = false;
    const task = tasks.find(t => t.id === id);
    if (!task) return () => {};

    const interval = setInterval(() => {
      if (cancelled || task.progress >= 100) {
        clearInterval(interval);
        if (task.progress >= 100) {
          task.status = 'completed';
          task.updatedAt = new Date().toISOString();
          onUpdate({ ...task });
        }
        return;
      }
      task.progress = Math.min(100, task.progress + Math.floor(Math.random() * 8 + 2));
      task.updatedAt = new Date().toISOString();
      onUpdate({ ...task });
    }, 1500);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  },
};
