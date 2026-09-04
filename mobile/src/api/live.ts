/**
 * The live feed from the computer.
 *
 * Polling would show the phone a task that finished ten seconds ago. The
 * control plane pushes each event as it happens, so a step that starts on the
 * computer appears on the phone while it is still running.
 *
 * A phone loses its connection constantly - a tunnel, a locked screen, a
 * change of network - so dropping is normal and reconnecting is automatic.
 * The socket carries the same token as the REST calls.
 */
import { getToken, socketUrl } from './client';
import { RawEvent } from './mappers';

type EventHandler = (event: RawEvent) => void;
type StatusHandler = (connected: boolean) => void;

export interface LiveOptions {
  /** Only these event types, comma-free. Empty means everything. */
  types?: string[];
  /** Only events belonging to this task. */
  taskId?: string;
  onEvent: EventHandler;
  onStatus?: StatusHandler;
}

const FIRST_RETRY_MS = 1000;
const MAX_RETRY_MS = 15000;

/**
 * Open the stream and keep it open. Returns a function that closes it for
 * good - call it when the screen goes away, or the phone will hold a socket
 * open behind a screen nobody is looking at.
 */
export function openEventStream(options: LiveOptions): () => void {
  let socket: WebSocket | null = null;
  let retryMs = FIRST_RETRY_MS;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let closed = false;

  const connect = () => {
    if (closed) return;
    if (!getToken()) {
      // Not paired yet. Nothing to listen to, and the server would refuse.
      options.onStatus?.(false);
      return;
    }

    const params: Record<string, string> = {};
    if (options.types?.length) params.types = options.types.join(',');
    if (options.taskId) params.task_id = options.taskId;

    try {
      socket = new WebSocket(socketUrl('/ws/events', params));
    } catch {
      scheduleRetry();
      return;
    }

    socket.onopen = () => {
      retryMs = FIRST_RETRY_MS;
      options.onStatus?.(true);
    };

    socket.onmessage = message => {
      try {
        options.onEvent(JSON.parse(message.data as string) as RawEvent);
      } catch {
        // A malformed frame is not worth tearing the stream down for.
      }
    };

    socket.onerror = () => {
      // onclose always follows, and that is where the retry lives.
    };

    socket.onclose = () => {
      options.onStatus?.(false);
      scheduleRetry();
    };
  };

  const scheduleRetry = () => {
    if (closed) return;
    socket = null;
    retryTimer = setTimeout(connect, retryMs);
    // Back off so a computer that is switched off is not hammered.
    retryMs = Math.min(retryMs * 2, MAX_RETRY_MS);
  };

  connect();

  return () => {
    closed = true;
    if (retryTimer) clearTimeout(retryTimer);
    socket?.close();
    socket = null;
  };
}
