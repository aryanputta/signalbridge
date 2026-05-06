/**
 * Detects repeated urgent signals within a rolling 30-minute window.
 * Returns a warning message if the same signal fires 3+ times without
 * a confirmed resolution between them.
 */
import { useState, useCallback } from "react";

interface SignalEvent {
  signal: string;
  at: number; // ms timestamp
  resolved: boolean;
}

const WINDOW_MS = 30 * 60 * 1000; // 30 minutes
const REPEAT_THRESHOLD = 3;

const URGENT_SIGNALS = new Set(["pain", "help", "bathroom", "medication", "anxiety"]);

export function useRepeatDetection() {
  const [history, setHistory] = useState<SignalEvent[]>([]);
  const [warning, setWarning] = useState<string | null>(null);

  const recordSignal = useCallback((signal: string) => {
    if (!URGENT_SIGNALS.has(signal)) return;

    const now = Date.now();
    setHistory((prev) => {
      const updated = [
        ...prev.filter((e) => now - e.at < WINDOW_MS),
        { signal, at: now, resolved: false },
      ];

      const recent = updated.filter((e) => e.signal === signal && !e.resolved);
      if (recent.length >= REPEAT_THRESHOLD) {
        setWarning(
          `"${signal}" has been signaled ${recent.length} times in the last 30 minutes without a confirmed response. Please check directly.`
        );
      } else {
        setWarning(null);
      }

      return updated;
    });
  }, []);

  const resolveSignal = useCallback((signal: string) => {
    setHistory((prev) =>
      prev.map((e) => (e.signal === signal && !e.resolved ? { ...e, resolved: true } : e))
    );
    setWarning(null);
  }, []);

  const dismissWarning = useCallback(() => setWarning(null), []);

  return { warning, recordSignal, resolveSignal, dismissWarning };
}
