/**
 * What happens when you type something into the box.
 *
 * This used to guess at the request with keyword matching and then act out a
 * scripted set of steps. It no longer needs to: the goal goes to the computer,
 * which plans the steps and works them with the same agent loop and the same
 * safety rules as the desktop app. What the phone shows afterwards is what
 * really happened.
 */
import { tasksService } from './tasks';
import { Task } from './types';

export const jarvisService = {
  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  },

  getSuggestions(): { label: string; icon: string }[] {
    return [
      { label: 'Continue my project', icon: 'arrow-forward-circle-outline' },
      { label: 'Find my files', icon: 'folder-outline' },
      { label: 'Check my emails', icon: 'mail-outline' },
      { label: 'Research something', icon: 'search-outline' },
    ];
  },

  /** Send the goal to the computer and hand back the task it started. */
  async processCommand(text: string): Promise<Task> {
    return tasksService.createTask(text.trim());
  },

  /**
   * Follow one task until it stops changing. Polling is enough here: the
   * timeline arrives over the live socket, and this only fills in the step
   * list behind it.
   */
  watchTask(taskId: string, onUpdate: (task: Task) => void): () => void {
    let stopped = false;

    const poll = async () => {
      if (stopped) return;
      try {
        const task = await tasksService.getTask(taskId);
        if (stopped || !task) return;
        onUpdate(task);
        if (['completed', 'failed', 'cancelled'].includes(task.status)) return;
      } catch {
        // A dropped connection is not the end of the task. Try again.
      }
      if (!stopped) timer = setTimeout(poll, 2000);
    };

    let timer: ReturnType<typeof setTimeout> = setTimeout(poll, 500);

    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  },
};
