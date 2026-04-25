import { useCallback, useEffect, useSyncExternalStore } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = 'visited_boards_v1';

let _snapshot: Set<string> = new Set();
let _hydrated = false;
const _listeners = new Set<() => void>();

function emitChange() { _listeners.forEach((cb) => cb()); }

function subscribe(cb: () => void): () => void {
  _listeners.add(cb);
  return () => { _listeners.delete(cb); };
}

function getSnapshot(): Set<string> { return _snapshot; }

async function hydrate() {
  if (_hydrated) return;
  _hydrated = true;
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (raw) {
      _snapshot = new Set(JSON.parse(raw) as string[]);
      emitChange();
    }
  } catch {}
}

async function markVisitedInternal(id: string) {
  if (_snapshot.has(id)) return;
  _snapshot = new Set([..._snapshot, id]);
  emitChange();
  try { await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify([..._snapshot])); } catch {}
}

export function useVisitedBoards() {
  const visitedIds = useSyncExternalStore(subscribe, getSnapshot);

  useEffect(() => { hydrate(); }, []);

  const markVisited = useCallback((id: string) => { markVisitedInternal(id); }, []);

  return { visitedIds, markVisited };
}
