/**
 * The computer's files, from the phone.
 *
 * Only the folders listed in `file_shares` on the computer are reachable, and
 * every path is checked on the server, so nothing here can wander outside
 * them. Browsing uses the relative path the server returns rather than an
 * absolute one, which is what keeps a request inside its share.
 */
import { request } from '../api/client';
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

interface RawShare {
  name: string;
  path: string;
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

export const filesService = {
  /** The folders the computer is willing to show at all. */
  async getShares(): Promise<RawShare[]> {
    return request<RawShare[]>('/api/files/shares');
  },

  /** List one folder. An empty path lists the shares themselves. */
  async getFiles(path = ''): Promise<FileItem[]> {
    const raw = await request<RawFile[]>(`/api/files?path=${encodeURIComponent(path)}`);
    return raw.map(toFileItem);
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
};
