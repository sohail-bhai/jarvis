/**
 * Where the phone keeps its pairing token and the address of the computer.
 *
 * The token is a credential, so on a real device it goes into the platform
 * keystore rather than plain storage. Expo SecureStore has no web
 * implementation, so the browser falls back to localStorage - good enough for
 * `expo start --web` during development, and never where a phone would be.
 */
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const web = Platform.OS === 'web';

export async function readValue(key: string): Promise<string | null> {
  try {
    if (web) return globalThis.localStorage?.getItem(key) ?? null;
    return await SecureStore.getItemAsync(key);
  } catch {
    // A cleared keystore or a browser with storage disabled reads as absent,
    // which sends the user back to the connect screen rather than crashing.
    return null;
  }
}

export async function writeValue(key: string, value: string): Promise<void> {
  if (web) {
    globalThis.localStorage?.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

export async function clearValue(key: string): Promise<void> {
  try {
    if (web) {
      globalThis.localStorage?.removeItem(key);
      return;
    }
    await SecureStore.deleteItemAsync(key);
  } catch {
    // Nothing stored is the state we wanted anyway.
  }
}
