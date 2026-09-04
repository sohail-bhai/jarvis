import { MemoryItem } from './types';

const mockMemory: MemoryItem[] = [
  { id: 'm1', type: 'project', key: 'hackwave', value: 'Hackwave - AI Security Presentation Project', lastAccessed: '2026-09-04T15:00:00Z' },
  { id: 'm2', type: 'project', key: 'ml-research', value: 'ML Research - Computer Vision Project', lastAccessed: '2026-09-03T10:00:00Z' },
  { id: 'm3', type: 'preference', key: 'editor', value: 'VS Code', lastAccessed: '2026-09-04T12:00:00Z' },
  { id: 'm4', type: 'file_reference', key: 'latest-pptx', value: 'Hackwave_Final.pptx on Laptop', lastAccessed: '2026-09-04T15:10:00Z' },
  { id: 'm5', type: 'context', key: 'current-focus', value: 'Preparing Hackwave presentation for submission', lastAccessed: '2026-09-04T15:00:00Z' },
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const memoryService = {
  async getMemory(): Promise<MemoryItem[]> {
    await delay(200);
    return [...mockMemory];
  },

  async getProjects(): Promise<MemoryItem[]> {
    await delay(200);
    return mockMemory.filter(m => m.type === 'project');
  },

  async addContext(key: string, value: string): Promise<void> {
    await delay(200);
    mockMemory.push({
      id: `m${mockMemory.length + 1}`,
      type: 'context',
      key,
      value,
      lastAccessed: new Date().toISOString(),
    });
  },
};
