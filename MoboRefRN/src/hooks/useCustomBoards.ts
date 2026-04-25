import { useCallback, useEffect, useSyncExternalStore } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Motherboard } from '../models/Motherboard';

const STORAGE_KEY = 'custom_boards_v1';

// External store: every screen reads from the same snapshot.
// When boards change, all subscribers are notified synchronously
// via useSyncExternalStore (React 18's canonical primitive for this).
let _snapshot: Motherboard[] = [];
let _hydrated = false;
const _listeners = new Set<() => void>();

function emitChange() {
  _listeners.forEach((cb) => cb());
}

function subscribe(cb: () => void): () => void {
  _listeners.add(cb);
  return () => { _listeners.delete(cb); };
}

function getSnapshot(): Motherboard[] {
  return _snapshot;
}

async function hydrate() {
  if (_hydrated) return;
  _hydrated = true;
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (raw) {
      _snapshot = JSON.parse(raw);
      emitChange();
    }
  } catch { /* ignore */ }
}

async function setBoards(next: Motherboard[]) {
  _snapshot = next;
  emitChange();
  try { await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
}

export function useCustomBoards() {
  const customBoards = useSyncExternalStore(subscribe, getSnapshot);

  useEffect(() => { hydrate(); }, []);

  const addCustomBoard = useCallback((board: Motherboard) => {
    setBoards([board, ..._snapshot]);
  }, []);

  const removeCustomBoard = useCallback((id: string) => {
    setBoards(_snapshot.filter((b) => b.id !== id));
  }, []);

  return { customBoards, addCustomBoard, removeCustomBoard };
}
