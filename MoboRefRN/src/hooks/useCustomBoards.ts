import { useState, useCallback, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Motherboard } from '../models/Motherboard';

const STORAGE_KEY = 'custom_boards_v1';

// Module-level singleton: all hook instances share the same in-memory state.
// When any screen adds/removes a custom board, every other screen is notified instantly.
let _cache: Motherboard[] = [];
let _loaded = false;
const _listeners = new Set<(boards: Motherboard[]) => void>();

function broadcast(boards: Motherboard[]) {
  _cache = boards;
  _listeners.forEach((fn) => fn([...boards]));
}

async function persist(boards: Motherboard[]) {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(boards));
  broadcast(boards);
}

export function useCustomBoards() {
  const [customBoards, setCustomBoards] = useState<Motherboard[]>(_cache);

  useEffect(() => {
    _listeners.add(setCustomBoards);
    if (!_loaded) {
      _loaded = true;
      AsyncStorage.getItem(STORAGE_KEY).then((raw) => {
        if (raw) {
          try { broadcast(JSON.parse(raw)); } catch { /* ignore */ }
        }
      });
    } else {
      setCustomBoards([..._cache]);
    }
    return () => { _listeners.delete(setCustomBoards); };
  }, []);

  const addCustomBoard = useCallback((board: Motherboard) => {
    persist([board, ..._cache]);
  }, []);

  const removeCustomBoard = useCallback((id: string) => {
    persist(_cache.filter((b) => b.id !== id));
  }, []);

  return { customBoards, addCustomBoard, removeCustomBoard };
}
