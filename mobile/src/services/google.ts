/**
 * Google Workspace - not connected yet.
 *
 * The control plane has no Google endpoints, so everything below is example
 * data. It is exported behind `isDemo` so the screens can say so out loud
 * rather than showing invented mail as if it were yours.
 */
import { DriveFile, Email, CalendarEvent } from './types';

const mockDriveFiles: DriveFile[] = [
  { id: 'gd-1', name: 'Architecture.pdf', mimeType: 'application/pdf', modifiedTime: '2026-09-02T10:00:00Z', size: '2.1 MB' },
  { id: 'gd-2', name: 'Project Notes.docx', mimeType: 'application/vnd.google-apps.document', modifiedTime: '2026-08-30T16:00:00Z', size: '340 KB' },
  { id: 'gd-3', name: 'Budget_Q3.xlsx', mimeType: 'application/vnd.google-apps.spreadsheet', modifiedTime: '2026-09-03T11:00:00Z', size: '890 KB' },
  { id: 'gd-4', name: 'Team Photo.jpg', mimeType: 'image/jpeg', modifiedTime: '2026-08-28T14:00:00Z', size: '4.5 MB' },
  { id: 'gd-5', name: 'Hackwave Deck.pptx', mimeType: 'application/vnd.google-apps.presentation', modifiedTime: '2026-09-03T15:00:00Z', size: '8.2 MB' },
];

const mockEmails: Email[] = [
  { id: 'em-1', from: 'Sarah Chen', subject: 'Hackwave submission deadline', snippet: 'Just a reminder that the final submission is due...', date: '2026-09-04T14:30:00Z', isRead: false, isImportant: true },
  { id: 'em-2', from: 'Alex Kumar', subject: 'Code review feedback', snippet: 'I reviewed your PR and left some comments on...', date: '2026-09-04T13:15:00Z', isRead: false, isImportant: true },
  { id: 'em-3', from: 'Team Updates', subject: 'Weekly sync notes', snippet: 'Here are the notes from today\'s sync meeting...', date: '2026-09-04T11:00:00Z', isRead: true, isImportant: false },
  { id: 'em-4', from: 'GitHub', subject: 'New issue: Performance optimization', snippet: 'A new issue was opened in your repository...', date: '2026-09-04T09:30:00Z', isRead: true, isImportant: false },
];

const mockCalendarEvents: CalendarEvent[] = [
  { id: 'cal-1', title: 'Team Standup', startTime: '2026-09-04T10:00:00Z', endTime: '2026-09-04T10:15:00Z' },
  { id: 'cal-2', title: 'Hackwave Review', startTime: '2026-09-04T14:00:00Z', endTime: '2026-09-04T15:00:00Z', location: 'Room 204' },
  { id: 'cal-3', title: 'Design Review', startTime: '2026-09-05T11:00:00Z', endTime: '2026-09-05T12:00:00Z', attendees: ['Sarah', 'Alex', 'Maya'] },
  { id: 'cal-4', title: 'Sprint Planning', startTime: '2026-09-05T14:00:00Z', endTime: '2026-09-05T15:30:00Z' },
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const googleService = {
  // Drive
  async getDriveFiles(): Promise<DriveFile[]> {
    await delay(400);
    return [...mockDriveFiles];
  },

  async searchDrive(query: string): Promise<DriveFile[]> {
    await delay(600);
    const q = query.toLowerCase();
    return mockDriveFiles.filter(f => f.name.toLowerCase().includes(q));
  },

  // Gmail
  async getEmails(): Promise<Email[]> {
    await delay(400);
    return [...mockEmails];
  },

  async getImportantEmails(): Promise<Email[]> {
    await delay(300);
    return mockEmails.filter(e => e.isImportant);
  },

  async getUnreadCount(): Promise<number> {
    return mockEmails.filter(e => !e.isRead).length;
  },

  // Calendar
  async getCalendarEvents(): Promise<CalendarEvent[]> {
    await delay(400);
    return [...mockCalendarEvents];
  },

  async getTodayEvents(): Promise<CalendarEvent[]> {
    await delay(300);
    return mockCalendarEvents.filter(e => e.startTime.includes('2026-09-04'));
  },

  // Status
  /** Nothing is connected to a real Google account yet. */
  isConnected(): boolean {
    return false;
  },

  /** True while these answers are examples rather than your data. */
  isDemo: true,
};
