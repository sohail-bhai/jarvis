import { tasksService } from './tasks';
import { filesService } from './files';
import { activityService } from './activity';
import { approvalsService } from './approvals';
import { Task } from './types';

const activeTaskTimeouts = new Map<string, ReturnType<typeof setTimeout>[]>();

function addTimeout(taskId: string, fn: (liveTask: Task) => void | Promise<void>, ms: number) {
  const timer = setTimeout(async () => {
    const task = await tasksService.getTask(taskId);
    if (!task || task.status === 'cancelled') {
      return;
    }
    await fn(task);
  }, ms);

  if (!activeTaskTimeouts.has(taskId)) {
    activeTaskTimeouts.set(taskId, []);
  }
  activeTaskTimeouts.get(taskId)?.push(timer);
}

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

  cancelTaskTimeouts(taskId: string) {
    const timers = activeTaskTimeouts.get(taskId);
    if (timers) {
      timers.forEach(t => clearTimeout(t));
      activeTaskTimeouts.delete(taskId);
    }
  },

  async processCommand(text: string): Promise<Task> {
    const lower = text.toLowerCase();

    // Flow 1: File search / email search
    if (lower.includes('find') || lower.includes('search') || lower.includes('where') || lower.includes('email')) {
      const isEmail = lower.includes('email');
      const task = await tasksService.createTask(
        isEmail ? 'Searching emails' : 'Finding files',
        isEmail ? 'Searching Gmail and connected accounts...' : 'Searching across your devices...'
      );

      task.steps = [
        { id: 's1', title: 'Understanding your request', status: 'completed', agentName: 'JARVIS' },
        { id: 's2', title: isEmail ? 'Searching Gmail Inbox' : 'Searching connected devices', status: 'running', agentName: isEmail ? 'Google Agent' : 'File Agent' },
        { id: 's3', title: isEmail ? 'Filtering relevant threads' : 'Checking Google Drive', status: 'pending', agentName: isEmail ? 'Research Agent' : 'Google Agent' },
      ];

      addTimeout(task.id, async () => {
        task.steps[1].status = 'completed';
        task.steps[2].status = 'running';
        task.progress = 50;
        await activityService.addActivity({
          type: 'info',
          title: isEmail ? 'Found 3 candidate email threads' : 'Searching connected devices for files',
          timestamp: new Date().toISOString(),
          timeLabel: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        });
      }, 1500);

      addTimeout(task.id, async () => {
        task.steps[2].status = 'completed';
        task.progress = 100;
        task.status = 'completed';
        task.result = isEmail ? 'Found matching email from college' : 'Found matching files';
        await activityService.addActivity({
          type: 'success',
          title: isEmail ? 'Email details retrieved successfully' : 'Found files matching your search',
          timestamp: new Date().toISOString(),
          timeLabel: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        });
      }, 3500);

      return task;
    }

    // Flow 2: Research
    if (lower.includes('research') || lower.includes('summarize') || lower.includes('summary')) {
      const task = await tasksService.createTask(
        'Research and summarize',
        'Researching and preparing summary...'
      );

      task.steps = [
        { id: 's1', title: 'Understanding your request', status: 'completed', agentName: 'JARVIS' },
        { id: 's2', title: 'Searching the web', status: 'running', agentName: 'Browser Agent' },
        { id: 's3', title: 'Reading documentation', status: 'pending', agentName: 'Research Agent' },
        { id: 's4', title: 'Preparing summary', status: 'pending', agentName: 'Writing Agent' },
      ];

      addTimeout(task.id, () => { task.steps[1].status = 'completed'; task.steps[2].status = 'running'; task.progress = 30; }, 2000);
      addTimeout(task.id, () => { task.steps[2].status = 'completed'; task.steps[3].status = 'running'; task.progress = 70; }, 4000);
      addTimeout(task.id, () => { task.steps[3].status = 'completed'; task.progress = 100; task.status = 'completed'; task.result = 'Research summary ready'; }, 6000);

      return task;
    }

    // Flow 3: Remote execution
    if (lower.includes('laptop') || lower.includes('computer') || lower.includes('continue') || lower.includes('run')) {
      const task = await tasksService.createTask(
        'Remote task execution',
        'Sending task to your device...'
      );

      task.steps = [
        { id: 's1', title: 'Understanding your request', status: 'completed', agentName: 'JARVIS' },
        { id: 's2', title: 'Connecting to your laptop', status: 'running', agentName: 'Computer Agent' },
        { id: 's3', title: 'Executing task', status: 'pending', agentName: 'Computer Agent' },
        { id: 's4', title: 'Collecting results', status: 'pending' },
      ];

      addTimeout(task.id, () => { task.steps[1].status = 'completed'; task.steps[2].status = 'running'; task.progress = 25; }, 1000);
      addTimeout(task.id, () => { task.steps[2].status = 'completed'; task.steps[3].status = 'running'; task.progress = 60; }, 3000);
      addTimeout(task.id, () => { task.steps[3].status = 'completed'; task.progress = 100; task.status = 'completed'; task.result = 'Task completed on your laptop'; }, 5000);

      return task;
    }

    // Flow 4: Document update (requires approval)
    if (lower.includes('update') || lower.includes('document') || lower.includes('google') || lower.includes('edit')) {
      const task = await tasksService.createTask(
        'Update document',
        'Preparing document changes...'
      );

      task.steps = [
        { id: 's1', title: 'Understanding your request', status: 'completed', agentName: 'JARVIS' },
        { id: 's2', title: 'Preparing changes', status: 'running', agentName: 'Writing Agent' },
        { id: 's3', title: 'Waiting for your approval', status: 'pending' },
        { id: 's4', title: 'Applying changes', status: 'pending', agentName: 'Google Agent' },
      ];
      task.requiresApproval = true;

      addTimeout(task.id, async () => {
        task.steps[1].status = 'completed';
        task.steps[2].status = 'running';
        task.progress = 40;
        task.status = 'waiting_approval';

        await approvalsService.createApproval({
          taskId: task.id,
          title: 'Update your document',
          description: 'Ready to apply changes to your Google Document.',
          action: 'modify_document',
          metadata: {
            'Document': 'Project Notes.docx',
            'Changes': '3 sections updated',
            'Sources': '2 web sources',
          },
          createdAt: new Date().toISOString(),
        });
      }, 2000);

      return task;
    }

    // Default: generic task
    const task = await tasksService.createTask(
      'Working on your request',
      'Processing...'
    );
    task.steps = [
      { id: 's1', title: 'Understanding your request', status: 'running', agentName: 'JARVIS' },
    ];

    addTimeout(task.id, () => { task.progress = 50; task.steps[0].status = 'completed'; }, 1500);
    addTimeout(task.id, () => { task.progress = 100; task.status = 'completed'; task.result = 'Task completed'; }, 3000);

    return task;
  },
};

