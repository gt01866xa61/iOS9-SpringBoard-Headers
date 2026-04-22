import { useState, useCallback, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Motherboard } from '../models/Motherboard';

const STORAGE_KEY = 'custom_boards_v1';

export function useCustomBoards() {
  const [customBoards, setCustomBoards] = useState<Motherboard[]>([]);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((raw) => {
      if (raw) {
        try { setCustomBoards(JSON.parse(raw)); } catch { /* ignore */ }
      }
    });
  }, []);

  const persist = useCallback(async (updated: Motherboard[]) => {
    setCustomBoards(updated);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }, []);

  const addCustomBoard = useCallback(
    (board: Motherboard) => {
      persist([board, ...customBoards]);
    },
    [customBoards, persist]
  );

  const removeCustomBoard = useCallback(
    (id: string) => {
      persist(customBoards.filter((b) => b.id !== id));
    },
    [customBoards, persist]
  );

  return { customBoards, addCustomBoard, removeCustomBoard };
}
