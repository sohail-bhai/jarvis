/**
 * Tasks, as the computer sees them.
 *
 * Nothing here is simulated any more: a task created from the phone is a task
 * on the control plane, worked by the same agent loop the desktop app uses,
 * and the progress shown is the progress that actually happened.
 */
import { request } from '../api/client';
import { RawTask, toTask } from '../api/mappers';
import { Task } from './types';

const ACTIVE: Task['status'][] = ['running', 'pending', 'waiting_approval'];

export const tasksService = {
  async getTasks(): Promise<Task[]> {
    const raw = await request<RawTask[]>('/api/tasks?limit=50');
    return raw.map(toTask);
  },

  async getActiveTasks(): Promise<Task[]> {
    const raw = await request<RawTask[]>('/api/tasks?active_only=true&limit=50');
    return raw.map(toTask);
  },

  async getCompletedTasks(): Promise<Task[]> {
    const raw = await request<RawTask[]>('/api/tasks?limit=50');
    return raw.map(toTask).filter(task => !ACTIVE.includes(task.status));
  },

  /** One task with its steps. The list endpoint omits them; this does not. */
  async getTask(id: string): Promise<Task | undefined> {
    const raw = await request<RawTask>(`/api/tasks/${id}`);
    return toTask(raw);
  },

  /**
   * Ask the computer to do something. The control plane breaks the goal into
   * steps and starts working them, so this returns a task that is already
   * running rather than an empty one waiting to be filled in.
   */
  async createTask(goal: string): Promise<Task> {
    const raw = await request<RawTask>('/api/tasks', {
      method: 'POST',
      body: { goal, autoplan: true, run: true },
    });
    return toTask(raw);
  },

  async cancelTask(id: string): Promise<void> {
    await request(`/api/tasks/${id}/cancel`, { method: 'POST' });
  },
};
