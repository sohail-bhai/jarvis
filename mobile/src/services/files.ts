/**
 * The computer's files, from the phone.
 *
 * Only the folders listed in `file_shares` on the computer are reachable, and
 * every path is checked on the server, so nothing here can wander outside
 * them. Browsing uses the relative path the server returns rather than an
 * absolute one, which is what keeps a request inside its share.
 *
 * Files move both ways: pull one down to open or keep, and push one up when
 * something on the phone belongs on the computer.
 */
import { Directory, File, Paths } from 'expo-file-system';
import * as DocumentPicker from 'expo-document-picker';
import * as Sharing from 'expo-sharing';

import { getHost, getToken, request } from '../api/client';
import { relativeLabel, toIso } from '../api/mappers';
import { FileItem, FileSource, FileType } from './types';

interface RawFile {
  name: string;
  path: string;
  relative: string;
  is_dir: boolean;
  size: number;
  modified: number;
  kind: string;
}

/** What `GET /api/files` answers: a folder, and what is inside it. */
interface RawListing {
  path: string;
  parent: string;
  entries: RawFile[];
  truncated: boolean;
}

interface RawShare {
  name: string;
  path: string;
}

export interface Listing {
  /** Where you are, as the server names it. Empty is the top level. */
  path: string;
  /** The folder above, or empty when there is none. */
  parent: string;
  files: FileItem[];
  truncated: boolean;
}

/** Map a MIME type onto the icon set the file list already draws. */
function toFileType(raw: RawFile): FileType {
  if (raw.is_dir) return 'folder';

  const kind = raw.kind ?? '';
  const extension = raw.name.split('.').pop()?.toLowerCase() ?? '';

  if (kind.startsWith('image/')) return 'image';
  if (kind.includes('pdf')) return 'pdf';
  if (['ppt', 'pptx', 'odp', 'key'].includes(extension)) return 'presentation';
  if (['xls', 'xlsx', 'ods', 'csv'].includes(extension)) return 'spreadsheet';
  if (['doc', 'docx', 'odt', 'txt', 'md', 'rtf'].includes(extension)) return 'document';
  if (['zip', 'tar', 'gz', 'rar', '7z'].includes(extension)) return 'archive';
  if (['py', 'ts', 'tsx', 'js', 'jsx', 'json', 'sh', 'go', 'rs', 'java'].includes(extension)) return 'code';
  return 'other';
}

function readableSize(bytes: number): string | undefined {
  if (!bytes) return undefined;
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value < 10 && unit > 0 ? value.toFixed(1) : Math.round(value)} ${units[unit]}`;
}

function toFileItem(raw: RawFile): FileItem {
  return {
    // The path is unique and stable, which an index would not be.
    id: raw.relative || raw.path,
    name: raw.name,
    type: toFileType(raw),
    source: 'computer' as FileSource,
    sourcePath: raw.relative || raw.path,
    size: readableSize(raw.size),
    modifiedAt: toIso(raw.modified),
    modifiedRelative: relativeLabel(raw.modified),
  };
}

/** The address of a file endpoint, for the calls that bypass `request`. */
function endpoint(path: string): string {
  return `${getHost()}${path}`;
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const filesService = {
  /** The folders the computer is willing to show at all. */
  async getShares(): Promise<RawShare[]> {
    return request<RawShare[]>('/api/files/shares');
  },

  /** List one folder, with the way back out of it. */
  async list(path = ''): Promise<Listing> {
    const raw = await request<RawListing>(`/api/files?path=${encodeURIComponent(path)}`);
    return {
      path: raw.path ?? '',
      parent: raw.parent ?? '',
      files: (raw.entries ?? []).map(toFileItem),
      truncated: Boolean(raw.truncated),
    };
  },

  /** Just the contents, for callers that do not care where they are. */
  async getFiles(path = ''): Promise<FileItem[]> {
    return (await this.list(path)).files;
  },

  /** "Where did I put it" - search by name across every shared folder. */
  async searchFiles(query: string): Promise<FileItem[]> {
    if (!query.trim()) return [];
    const raw = await request<RawFile[]>(
      `/api/files/search?query=${encodeURIComponent(query.trim())}`,
    );
    return raw.map(toFileItem);
  },

  async getRecentFiles(limit = 5): Promise<FileItem[]> {
    const files = await this.getFiles();
    return files
      .filter(file => file.type !== 'folder')
      .sort((a, b) => (a.modifiedAt < b.modifiedAt ? 1 : -1))
      .slice(0, limit);
  },

  /**
   * Pull a file down to the phone and hand it to whatever opens it.
   *
   * The copy lands in the cache directory, which the system may clear later -
   * this is for reading and forwarding a file, not for keeping one.
   */
  async download(file: FileItem): Promise<string> {
    const url = endpoint(`/api/files/download?path=${encodeURIComponent(file.sourcePath ?? '')}`);
    const destination = new Directory(Paths.cache, 'jarvis');
    if (!destination.exists) destination.create({ intermediates: true });

    const saved = await File.downloadFileAsync(url, destination, {
      headers: authHeaders(),
      idempotent: true,
    });
    return saved.uri;
  },

  /** Download, then offer it to the phone's own share sheet. */
  async openOnPhone(file: FileItem): Promise<void> {
    const uri = await this.download(file);
    if (!(await Sharing.isAvailableAsync())) {
      throw new Error(`Saved to the phone, but nothing here can open ${file.name}.`);
    }
    await Sharing.shareAsync(uri, { dialogTitle: file.name });
  },

  /**
   * Send something from the phone to a shared folder on the computer.
   *
   * Returns null when the picker was dismissed, so a cancelled choice is not
   * reported as a failure.
   */
  async uploadFromPhone(folder = ''): Promise<FileItem | null> {
    const picked = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true });
    if (picked.canceled || !picked.assets?.length) return null;

    const asset = picked.assets[0];
    const form = new FormData();
    // React Native's FormData takes a file by descriptor rather than by bytes.
    form.append('file', {
      uri: asset.uri,
      name: asset.name || 'upload',
      type: asset.mimeType || 'application/octet-stream',
    } as unknown as Blob);
    form.append('folder', folder);
    form.append('overwrite', 'false');

    const response = await fetch(endpoint('/api/files/upload'), {
      method: 'POST',
      headers: { Accept: 'application/json', ...authHeaders() },
      body: form,
    });

    const text = await response.text();
    let payload: any = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = null;
    }

    if (!response.ok) {
      throw new Error(
        payload?.error?.message ?? payload?.detail
          ?? `Your computer refused the file (${response.status}).`,
      );
    }
    return toFileItem(payload as RawFile);
  },

  /** Delete a file on the computer. Off unless the computer allows it. */
  async remove(file: FileItem): Promise<void> {
    await request(`/api/files?path=${encodeURIComponent(file.sourcePath ?? '')}`, {
      method: 'DELETE',
    });
  },
};
