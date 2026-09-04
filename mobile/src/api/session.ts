/**
 * Pairing the phone with the computer, and knowing whether it still is.
 *
 * Reaching the port is not the same as being allowed to use it. The phone
 * trades a code shown on the computer for a token of its own, which can later
 * be revoked without disturbing the desktop app or any other device.
 */
import { Platform } from 'react-native';

import {
  ApiError,
  forgetCredentials,
  getHost,
  isConnected,
  loadConnection,
  normaliseHost,
  request,
  setCredentials,
  setHost,
} from './client';

export interface ConnectionState {
  /** Address of the computer running the control plane. */
  host: string;
  /** True once this phone holds a token for that computer. */
  paired: boolean;
  /** True when the last call to the computer succeeded. */
  reachable: boolean;
  /** What went wrong, in language a person can act on. */
  problem: string;
}

interface PairResponse {
  device: { id: string; name: string };
  token: string;
}

export interface HealthResponse {
  ok: boolean;
  version: string;
}

function devicePlatform(): string {
  return Platform.OS === 'ios' ? 'ios' : Platform.OS === 'android' ? 'android' : 'web';
}

export const sessionService = {
  async load(): Promise<ConnectionState> {
    await loadConnection();
    return { host: getHost(), paired: isConnected(), reachable: false, problem: '' };
  },

  /**
   * Check an address before asking the user for a pairing code, so a typo is
   * reported as a wrong address rather than as a wrong code.
   */
  async checkHost(input: string): Promise<HealthResponse> {
    await setHost(normaliseHost(input));
    return request<HealthResponse>('/health', { anonymous: true, timeoutMs: 6000 });
  },

  /** Trade the six-digit code shown on the computer for this phone's token. */
  async pair(code: string, name: string): Promise<PairResponse> {
    const response = await request<PairResponse>('/api/pair', {
      method: 'POST',
      anonymous: true,
      body: {
        code: code.trim(),
        name: name.trim() || 'My phone',
        kind: 'phone',
        platform: devicePlatform(),
      },
    });

    await setCredentials(response.token, response.device.id);
    return response;
  },

  /** Forget this computer. The computer keeps its record until it is revoked. */
  async disconnect(): Promise<void> {
    await forgetCredentials();
  },

  /** Is the computer there, and does it still accept our token? */
  async ping(): Promise<ConnectionState> {
    const base: ConnectionState = {
      host: getHost(),
      paired: isConnected(),
      reachable: false,
      problem: '',
    };

    if (!base.host) return { ...base, problem: 'No computer connected yet.' };

    try {
      await request('/api/status');
      return { ...base, reachable: true };
    } catch (error) {
      const problem =
        error instanceof ApiError
          ? error.needsPairing
            ? 'This phone is no longer paired with the computer.'
            : error.message
          : 'Could not reach JARVIS.';
      return { ...base, problem };
    }
  },
};
