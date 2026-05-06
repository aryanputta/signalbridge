/**
 * Offline feedback queue backed by IndexedDB.
 *
 * When the backend is unreachable, feedback is stored locally and
 * flushed automatically the next time the backend responds.
 * Nothing is lost even if the server process is not running.
 */
import { useEffect, useRef } from "react";
import type { FeedbackPayload } from "../types";

const DB_NAME = "signalbridge_offline";
const STORE = "pending_feedback";
const DB_VERSION = 1;

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { autoIncrement: true });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function enqueue(payload: FeedbackPayload): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).add(payload);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function dequeueAll(): Promise<{ key: IDBValidKey; value: FeedbackPayload }[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const results: { key: IDBValidKey; value: FeedbackPayload }[] = [];
    const tx = db.transaction(STORE, "readonly");
    const cursor = tx.objectStore(STORE).openCursor();
    cursor.onsuccess = (e) => {
      const c = (e.target as IDBRequest).result as IDBCursorWithValue | null;
      if (c) { results.push({ key: c.key, value: c.value }); c.continue(); }
      else resolve(results);
    };
    cursor.onerror = () => reject(cursor.error);
  });
}

async function deleteKey(key: IDBValidKey): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function submitFeedbackWithQueue(
  payload: FeedbackPayload,
  submitFn: (p: FeedbackPayload) => Promise<unknown>,
): Promise<void> {
  try {
    await submitFn(payload);
  } catch {
    await enqueue(payload);
  }
}

export function useOfflineFlusher(submitFn: (p: FeedbackPayload) => Promise<unknown>): void {
  const flushing = useRef(false);

  useEffect(() => {
    const flush = async () => {
      if (flushing.current) return;
      flushing.current = true;
      try {
        const items = await dequeueAll();
        for (const { key, value } of items) {
          try {
            await submitFn(value);
            await deleteKey(key);
          } catch {
            break; // backend still down, stop trying
          }
        }
      } finally {
        flushing.current = false;
      }
    };

    flush();
    const interval = setInterval(flush, 30_000);
    window.addEventListener("online", flush);
    return () => {
      clearInterval(interval);
      window.removeEventListener("online", flush);
    };
  }, [submitFn]);
}
