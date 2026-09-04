/**
 * The phone's connection to the JARVIS control plane.
 *
 * Every screen talks to the computer through this one module, so the address,
 * the pairing token and the shape of a failure are decided in a single place.
 * The server is the same one the desktop app uses; the phone is simply another
 * paired device holding its own token.
 */
import { clearValue, readValue, writeValue } from './storage';

const HOST_KEY = 'jarvis.host';
const TOKEN_KEY = 'jarvis.token';
const DEVICE_KEY = 'jarvis.device';

/** A build can ship a default address; anything typed on the phone wins. */
const DEFAULT_HOST = process.env.EXPO_PUBLIC_JARVIS_URL ?? '';

let host = DEFAULT_HOST;
let token: string | null = null;
let deviceId: string | null = null;
let loaded = false;

/** How long a request may hang before we call the computer unreachable. */
const TIMEOUT_MS = 15000;

export type ErrorKind =
  | 'bad_request'
  | 'unauthenticated'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'invalid_request'
  | 'rate_limited'
  | 'internal_error'
  | 'unreachable';

export class ApiError extends Error {
  status: number;
  kind: ErrorKind;

  constructor(message: string, status: number, kind: ErrorKind) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.kind = kind;
  }

  /** True when the answer is "pair again", not "try again". */
  get needsPairing() {
    return this.kind === 'unauthenticated' || this.kind === 'forbidden';
  }
}

/** Read the stored address and token once, before the first request. */
export async function loadConnection(): Promise<void> {
  if (loaded) return;
  host = (await readValue(HOST_KEY)) || DEFAULT_HOST;
  token = await readValue(TOKEN_KEY);
  deviceId = await readValue(DEVICE_KEY);
  loaded = true;
}

export function getHost(): string {
  return host;
}

export function getToken(): string | null {
  return token;
}

export function getDeviceId(): string | null {
  return deviceId;
}

/** True once the phone knows an address and holds a token for it. */
export function isConnected(): boolean {
  return Boolean(host && token);
}

/**
 * Accept what the user typed: a bare address, a host and port, or a full URL.
 * `192.168.1.20:8765` and `http://192.168.1.20:8765/` mean the same computer.
 */
export function normaliseHost(input: string): string {
  const trimmed = input.trim().replace(/\/+$/, '');
  if (!trimmed) return '';
  const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
  return /:\d+$/.test(withScheme) ? withScheme : `${withScheme}:8765`;
}

export async function setHost(value: string): Promise<void> {
  host = normaliseHost(value);
  await writeValue(HOST_KEY, host);
}

export async function setCredentials(newToken: string, newDeviceId: string): Promise<void> {
  token = newToken;
  deviceId = newDeviceId;
  await writeValue(TOKEN_KEY, newToken);
  await writeValue(DEVICE_KEY, newDeviceId);
}

/** Forget this phone's access. The computer keeps its own record. */
export async function forgetCredentials(): Promise<void> {
  token = null;
  deviceId = null;
  await clearValue(TOKEN_KEY);
  await clearValue(DEVICE_KEY);
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  /** Pairing happens before a token exists, so it opts out of the header. */
  anonymous?: boolean;
  timeoutMs?: number;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  await loadConnection();

  if (!host) {
    throw new ApiError('JARVIS is not connected to a computer yet.', 0, 'unreachable');
  }

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (token && !options.anonymous) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs ?? TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${host}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
  } catch {
    // Wrong address, computer asleep, or the phone left the network. The
    // caller only needs to know the computer could not be reached.
    throw new ApiError(`Could not reach JARVIS at ${host}.`, 0, 'unreachable');
  } finally {
    clearTimeout(timer);
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let payload: any = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    // The control plane answers every failure with one envelope.
    const envelope = payload?.error ?? {};
    throw new ApiError(
      envelope.message ?? payload?.detail ?? `JARVIS returned ${response.status}.`,
      response.status,
      (envelope.kind as ErrorKind) ?? kindFromStatus(response.status),
    );
  }

  return payload as T;
}

function kindFromStatus(status: number): ErrorKind {
  if (status === 401) return 'unauthenticated';
  if (status === 403) return 'forbidden';
  if (status === 404) return 'not_found';
  if (status === 409) return 'conflict';
  if (status === 422) return 'invalid_request';
  if (status === 429) return 'rate_limited';
  return 'internal_error';
}

/** The WebSocket address for a live stream, carrying the token as a query. */
export function socketUrl(path: string, params: Record<string, string> = {}): string {
  const base = host.replace(/^http/i, 'ws');
  const query = new URLSearchParams({ ...params, ...(token ? { token } : {}) });
  return `${base}${path}?${query.toString()}`;
}
