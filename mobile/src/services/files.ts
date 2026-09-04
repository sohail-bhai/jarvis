import { FileItem, FileSource, FileType } from './types';

const mockFiles: FileItem[] = [
  {
    id: 'f1',
    name: 'Hackwave_Final.pptx',
    type: 'presentation',
    source: 'computer',
    sourcePath: 'Projects/Hackwave',
    size: '4.2 MB',
    modifiedAt: '2026-09-03T14:00:00Z',
    modifiedRelative: 'Modified yesterday',
  },
  {
    id: 'f2',
    name: 'Architecture.pdf',
    type: 'pdf',
    source: 'drive',
    sourcePath: 'Google Drive',
    size: '2.1 MB',
    modifiedAt: '2026-09-02T10:00:00Z',
    modifiedRelative: 'Modified 2 days ago',
  },
  {
    id: 'f3',
    name: 'Dataset.zip',
    type: 'archive',
    source: 'computer',
    sourcePath: 'ML Project',
    size: '156 MB',
    modifiedAt: '2026-09-01T08:00:00Z',
    modifiedRelative: 'Modified 3 days ago',
  },
  {
    id: 'f4',
    name: 'Project Notes.docx',
    type: 'document',
    source: 'drive',
    sourcePath: 'Google Drive',
    size: '340 KB',
    modifiedAt: '2026-08-30T16:00:00Z',
    modifiedRelative: 'Modified 5 days ago',
  },
  {
    id: 'f5',
    name: 'Meeting Recording.mp4',
    type: 'other',
    source: 'phone',
    sourcePath: 'Phone',
    size: '1.2 GB',
    modifiedAt: '2026-09-04T09:00:00Z',
    modifiedRelative: 'Modified today',
  },
  {
    id: 'f6',
    name: 'Budget_Q3.xlsx',
    type: 'spreadsheet',
    source: 'drive',
    sourcePath: 'Google Drive / Finance',
    size: '890 KB',
    modifiedAt: '2026-09-03T11:00:00Z',
    modifiedRelative: 'Modified yesterday',
  },
  {
    id: 'f7',
    name: 'AI_Research_Summary.docx',
    type: 'document',
    source: 'computer',
    sourcePath: 'Documents / Research',
    size: '520 KB',
    modifiedAt: '2026-09-04T13:00:00Z',
    modifiedRelative: 'Modified 2 hours ago',
  },
  {
    id: 'f8',
    name: 'app_screenshot.png',
    type: 'image',
    source: 'phone',
    sourcePath: 'Phone / Screenshots',
    size: '2.4 MB',
    modifiedAt: '2026-09-04T12:30:00Z',
    modifiedRelative: 'Modified today',
  },
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const filesService = {
  async getFiles(source?: FileSource): Promise<FileItem[]> {
    await delay(400);
    if (source) {
      return mockFiles.filter(f => f.source === source);
    }
    return [...mockFiles];
  },

  async searchFiles(query: string, source?: FileSource): Promise<FileItem[]> {
    await delay(600);
    const q = query.toLowerCase();
    let results = mockFiles.filter(
      f => f.name.toLowerCase().includes(q) || (f.sourcePath && f.sourcePath.toLowerCase().includes(q))
    );
    if (source) {
      results = results.filter(f => f.source === source);
    }
    return results;
  },

  async getFile(id: string): Promise<FileItem | undefined> {
    await delay(200);
    return mockFiles.find(f => f.id === id);
  },

  async getRecentFiles(limit = 5): Promise<FileItem[]> {
    await delay(300);
    return [...mockFiles]
      .sort((a, b) => new Date(b.modifiedAt).getTime() - new Date(a.modifiedAt).getTime())
      .slice(0, limit);
  },

  getFileTypeColor(type: FileType): string {
    const map: Record<FileType, string> = {
      presentation: '#E85D4A',
      pdf: '#E85D4A',
      document: '#3B7DDD',
      spreadsheet: '#4CAF6E',
      archive: '#6B7B94',
      image: '#F5A623',
      code: '#8B5CF6',
      folder: '#6B7B94',
      other: '#6B7B94',
    };
    return map[type];
  },

  getFileTypeIcon(type: FileType): string {
    const map: Record<FileType, string> = {
      presentation: 'easel-outline',
      pdf: 'document-text-outline',
      document: 'document-outline',
      spreadsheet: 'grid-outline',
      archive: 'archive-outline',
      image: 'image-outline',
      code: 'code-slash-outline',
      folder: 'folder-outline',
      other: 'document-outline',
    };
    return map[type];
  },
};
