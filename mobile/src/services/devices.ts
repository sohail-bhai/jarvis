import { Device } from './types';

const mockDevices: Device[] = [
  {
    id: 'dev-1',
    name: 'Laptop',
    type: 'laptop',
    status: 'online',
    lastSeen: new Date().toISOString(),
    os: 'macOS',
    capabilities: ['file_access', 'code_execution', 'browser', 'terminal'],
  },
  {
    id: 'dev-2',
    name: 'Desktop',
    type: 'desktop',
    status: 'online',
    lastSeen: new Date().toISOString(),
    os: 'Windows',
    capabilities: ['file_access', 'code_execution', 'browser', 'terminal', 'gpu'],
  },
  {
    id: 'dev-3',
    name: 'Phone',
    type: 'phone',
    status: 'connected',
    lastSeen: new Date().toISOString(),
    os: 'iOS',
    capabilities: ['notifications', 'approvals', 'camera'],
  },
  {
    id: 'dev-4',
    name: 'Server',
    type: 'server',
    status: 'offline',
    lastSeen: '2026-09-03T18:00:00Z',
    os: 'Ubuntu',
    capabilities: ['code_execution', 'terminal', 'gpu', 'docker'],
  },
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const devicesService = {
  async getDevices(): Promise<Device[]> {
    await delay(300);
    return [...mockDevices];
  },

  async getDevice(id: string): Promise<Device | undefined> {
    await delay(200);
    return mockDevices.find(d => d.id === id);
  },

  async getOnlineCount(): Promise<number> {
    return mockDevices.filter(d => d.status !== 'offline').length;
  },

  async sendCommand(deviceId: string, command: string): Promise<{ success: boolean; message: string }> {
    await delay(1000);
    const device = mockDevices.find(d => d.id === deviceId);
    if (!device || device.status === 'offline') {
      return { success: false, message: 'Device is offline' };
    }
    return { success: true, message: `Command sent to ${device.name}` };
  },
};
