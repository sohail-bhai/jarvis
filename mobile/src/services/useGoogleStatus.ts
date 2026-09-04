/**
 * Whether Google is connected, for the screens that only show a badge.
 *
 * Asking the computer is a request, so the answer starts as "unknown" rather
 * than as "not connected" - a badge that guesses is the same problem as a
 * screen that pretends.
 */
import { useCallback, useEffect, useState } from 'react';

import { GoogleStatus, googleService } from './google';

export interface GoogleStatusView {
  status: GoogleStatus | null;
  /** True until the first answer arrives. */
  loading: boolean;
  /** True once Google will really answer. */
  connected: boolean;
  /** True when what a screen shows is an example, not the user's data. */
  demo: boolean;
  /** Why it is not connected, in the computer's own words. */
  detail: string;
  refresh: () => Promise<void>;
}

export function useGoogleStatus(): GoogleStatusView {
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setStatus(await googleService.getStatus());
    } catch {
      // The computer is unreachable, which is not the same as Google being
      // disconnected. Both end up showing "not connected", and the detail
      // below says which one it was.
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    status,
    loading,
    connected: Boolean(status?.connected),
    demo: !status?.connected,
    detail: status?.detail ?? 'JARVIS could not reach your computer.',
    refresh,
  };
}
