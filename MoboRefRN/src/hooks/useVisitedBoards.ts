import { useCallback, useEffect, useSyncExternalStore } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type VisitStatus = 'confirmed' | 'wrong';

const STORAGE_KEY = 'visited_boards_v2';

let _snapshot: Record<string, VisitStatus> = {};
let _hydrated = false;
const _listeners = new Set<() => void>();

function emitChange() { _listeners.forEach((cb) => cb()); }

function subscribe(cb: () => void): () => void {
  _listeners.add(cb);
  return () => { _listeners.delete(cb); };
}

function getSnapshot(): Record<string, VisitStatus> { return _snapshot; }

async function hydrate() {
  if (_hydrated) return;
  _hydrated = true;
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (raw) {
      _snapshot = JSON.parse(raw) as Record<string, VisitStatus>;
      emitChange();
    }
  } catch {}
}

async function setStatus(id: string, status: VisitStatus) {
  _snapshot = { ..._snapshot, [id]: status };
  emitChange();
  try { await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(_snapshot)); } catch {}
}

export function useVisitedBoards() {
  const visitRecord = useSyncExternalStore(subscribe, getSnapshot);

  useEffect(() => { hydrate(); }, []);

  const markConfirmed = useCallback((id: string) => { setStatus(id, 'confirmed'); }, []);
  const markWrong = useCallback((id: string) => { setStatus(id, 'wrong'); }, []);

  return { visitRecord, markConfirmed, markWrong };
}
