/**
 * The machines JARVIS can work on.
 *
 * The computer running the control plane is one of these, and so is this
 * phone once it pairs. A device is registered on the server, so what the
 * phone lists is what the desktop app lists.
 */
import { request } from '../api/client';
import { RawDevice, toDevice } from '../api/mappers';
import { Device } from './types';

export const devicesService = {
  async getDevices(): Promise<Device[]> {
    const raw = await request<RawDevice[]>('/api/devices');
    return raw.map(toDevice);
  },

  async getDevice(id: string): Promise<Device | undefined> {
    const devices = await this.getDevices();
    return devices.find(device => device.id === id);
  },

  async getOnlineCount(): Promise<number> {
    const devices = await this.getDevices();
    return devices.filter(device => device.status === 'online').length;
  },

  /** Revoke one device's access without disturbing any other. */
  async unpair(id: string): Promise<void> {
    await request(`/api/devices/${id}/token`, { method: 'DELETE' });
  },
};
