/**
 * Google Workspace, through the computer.
 *
 * The phone never holds a Google token. It asks the computer, and the computer
 * - which did the OAuth and stores the token - answers. Every answer carries
 * `live`, so a screen showing example data always knows it is doing so and can
 * say it out loud.
 */
import { request } from '../api/client';
import { CalendarEvent, DriveFile, Email } from './types';

export type GoogleState = 'live' | 'needs_authorization' | 'not_configured';

export interface GoogleStatus {
  connected: boolean;
  state: GoogleState;
  detail: string;
  mode: 'live' | 'demo';
  account: string;
  services: Record<string, { status: string; label: string }>;
}

/** Answers arrive labelled: real, or an example the screen must own up to. */
export interface Answer<T> {
  live: boolean;
  items: T[];
  notice?: string;
}

interface RawPayload<T> {
  live: boolean;
  items: T[];
  notice?: string;
}

interface RawDriveFile {
  id: string;
  name: string;
  mimeType?: string;
  modifiedTime?: string;
  size?: string;
  webViewLink?: string;
}

interface RawEmail {
  id: string;
  sender?: string;
  subject?: string;
  snippet?: string;
  unread?: boolean;
}

interface RawEvent {
  id: string;
  summary?: string;
  description?: string;
  location?: string;
  start?: { dateTime?: string; date?: string };
  end?: { dateTime?: string; date?: string };
  attendees?: { email?: string; displayName?: string }[];
}

function readableSize(size?: string): string | undefined {
  const bytes = Number(size);
  if (!size || Number.isNaN(bytes) || bytes <= 0) return undefined;
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value < 10 && unit > 0 ? value.toFixed(1) : Math.round(value)} ${units[unit]}`;
}

function toDriveFile(raw: RawDriveFile): DriveFile {
  return {
    id: raw.id,
    name: raw.name,
    mimeType: raw.mimeType ?? 'application/octet-stream',
    modifiedTime: raw.modifiedTime ?? '',
    size: readableSize(raw.size),
  };
}

function toEmail(raw: RawEmail): Email {
  return {
    id: raw.id,
    from: raw.sender ?? 'Unknown',
    subject: raw.subject ?? '(no subject)',
    snippet: raw.snippet ?? '',
    date: '',
    isRead: !raw.unread,
    // Gmail's own "important" marking is a separate call; unread is the honest
    // stand-in and is what the screen actually sorts on.
    isImportant: Boolean(raw.unread),
  };
}

function toEvent(raw: RawEvent): CalendarEvent {
  return {
    id: raw.id,
    title: raw.summary ?? 'Untitled event',
    startTime: raw.start?.dateTime ?? raw.start?.date ?? '',
    endTime: raw.end?.dateTime ?? raw.end?.date ?? '',
    location: raw.location,
    attendees: raw.attendees?.map(person => person.displayName || person.email || '').filter(Boolean),
  };
}

function answer<Raw, T>(payload: RawPayload<Raw>, map: (raw: Raw) => T): Answer<T> {
  return {
    live: Boolean(payload?.live),
    items: (payload?.items ?? []).map(map),
    notice: payload?.notice,
  };
}

export const googleService = {
  /** Whether the computer's Google account is connected, and to whom. */
  async getStatus(): Promise<GoogleStatus> {
    return request<GoogleStatus>('/api/google/status');
  },

  /**
   * Start the sign-in. The browser opens on the computer, because that is
   * where the token belongs - the phone only learns the outcome.
   */
  async connect(): Promise<{ detail: string }> {
    return request<{ detail: string }>('/api/google/connect', { method: 'POST' });
  },

  async disconnect(): Promise<GoogleStatus> {
    return request<GoogleStatus>('/api/google/disconnect', { method: 'POST' });
  },

  async getDriveFiles(limit = 20): Promise<Answer<DriveFile>> {
    return answer(await request<RawPayload<RawDriveFile>>(
      `/api/google/drive?limit=${limit}`), toDriveFile);
  },

  async searchDrive(query: string, limit = 20): Promise<Answer<DriveFile>> {
    return answer(await request<RawPayload<RawDriveFile>>(
      `/api/google/drive/search?query=${encodeURIComponent(query)}&limit=${limit}`), toDriveFile);
  },

  async getEmails(query = 'is:unread', limit = 10): Promise<Answer<Email>> {
    return answer(await request<RawPayload<RawEmail>>(
      `/api/google/gmail?query=${encodeURIComponent(query)}&limit=${limit}`), toEmail);
  },

  async getImportantEmails(limit = 10): Promise<Answer<Email>> {
    return this.getEmails('is:unread is:important', limit);
  },

  async getCalendarEvents(limit = 10): Promise<Answer<CalendarEvent>> {
    return answer(await request<RawPayload<RawEvent>>(
      `/api/google/calendar?limit=${limit}`), toEvent);
  },

  /** Today's events, filtered here so the server stays a plain listing. */
  async getTodayEvents(): Promise<Answer<CalendarEvent>> {
    const events = await this.getCalendarEvents(25);
    const today = new Date().toDateString();
    return {
      ...events,
      items: events.items.filter(
        event => event.startTime && new Date(event.startTime).toDateString() === today),
    };
  },

  async draftEmail(to: string, subject: string, body: string) {
    return request('/api/google/gmail/draft', { method: 'POST', body: { to, subject, body } });
  },

  async createDoc(title: string, content = '') {
    return request('/api/google/docs', { method: 'POST', body: { title, content } });
  },

  async createSlides(title: string, slides: string[] = []) {
    return request('/api/google/slides', { method: 'POST', body: { title, slides } });
  },
};
