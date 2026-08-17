import { useEffect, useRef } from "react";

/**
 * Poll a callback at `intervalMs` while `active` is true.
 * Avoids overlapping requests (a slow fetch never overlaps the next tick) and
 * clears the timer on unmount / when active flips.
 */
export function usePolling(callback: () => void, intervalMs: number, active: boolean) {
  const cbRef = useRef(callback);
  cbRef.current = callback;

  useEffect(() => {
    if (!active) return;
    let running = false;
    const id = window.setInterval(async () => {
      if (running) return;
      running = true;
      try {
        await cbRef.current();
      } finally {
        running = false;
      }
    }, intervalMs);
    return () => window.clearInterval(id);
  }, [active, intervalMs]);
}