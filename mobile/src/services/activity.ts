import { ActivityEntry, ActivityType } from './types';

const mockActivity: ActivityEntry[] = [
  {
    id: 'a1',
    type: 'success',
    title: 'Found 3 documents on your computer',
    timestamp: '2026-09-04T15:24:00Z',
    timeLabel: '3:24 PM',
  },
  {
    id: 'a2',
    type: 'info',
    title: 'Checked Google Drive for related files',
    timestamp: '2026-09-04T15:22:00Z',
    timeLabel: '3:22 PM',
  },
  {
    id: 'a3',
    type: 'info',
    title: 'Researching latest information online',
    timestamp: '2026-09-04T15:20:00Z',
    timeLabel: '3:20 PM',
  },
  {
    id: 'a4',
    type: 'success',
    title: 'Updating your presentation',
    timestamp: '2026-09-04T15:18:00Z',
    timeLabel: '3:18 PM',
  },
  {
    id: 'a5',
    type: 'success',
    title: 'Completed file organization',
    description: 'Organized 47 files into 8 folders',
    timestamp: '2026-09-04T15:15:00Z',
    timeLabel: '3:15 PM',
  },
  {
    id: 'a6',
    type: 'approval',
    title: 'Approved: Merge project changes',
    timestamp: '2026-09-04T14:30:00Z',
    timeLabel: '2:30 PM',
  },
  {
    id: 'a7',
    type: 'warning',
    title: 'Server connection lost',
    description: 'Retrying when server comes back online',
    timestamp: '2026-09-04T13:45:00Z',
    timeLabel: '1:45 PM',
  },
  {
    id: 'a8',
    type: 'success',
    title: 'Research summary completed',
    description: 'Summarized 5 AI agent frameworks',
    timestamp: '2026-09-04T11:30:00Z',
    timeLabel: '11:30 AM',
  },
];

let activity = [...mockActivity];
let nextId = 9;

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const activityService = {
  async getActivity(): Promise<ActivityEntry[]> {
    await delay(300);
    return [...activity];
  },

  async addActivity(entry: Omit<ActivityEntry, 'id'>): Promise<ActivityEntry> {
    const newEntry: ActivityEntry = {
      ...entry,
      id: `a${nextId++}`,
    };
    activity.unshift(newEntry);
    return newEntry;
  },

  async getRecentActivity(limit = 5): Promise<ActivityEntry[]> {
    await delay(200);
    return activity.slice(0, limit);
  },
};
