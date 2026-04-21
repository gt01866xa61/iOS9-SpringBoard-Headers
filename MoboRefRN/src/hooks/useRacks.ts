import { useState, useCallback, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Rack, RackSlot } from '../models/Rack';
import { Motherboard } from '../models/Motherboard';

const STORAGE_KEY = 'racks_v1';

function uuid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function useRacks() {
  const [racks, setRacks] = useState<Rack[]>([]);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((raw) => {
      if (raw) {
        try {
          setRacks(JSON.parse(raw));
        } catch {
          // ignore corrupt data
        }
      }
    });
  }, []);

  const persist = useCallback(async (updated: Rack[]) => {
    setRacks(updated);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }, []);

  const addRack = useCallback(
    (name: string, slotCount = 9) => {
      const slots: RackSlot[] = Array.from({ length: slotCount }, (_, i) => ({
        id: uuid(),
        position: i,
      }));
      const rack: Rack = { id: uuid(), name, slots, createdAt: Date.now() };
      persist([...racks, rack]);
    },
    [racks, persist]
  );

  const removeRack = useCallback(
    (rackId: string) => {
      persist(racks.filter((r) => r.id !== rackId));
    },
    [racks, persist]
  );

  const assignMotherboard = useCallback(
    (rackId: string, slotId: string, board: Motherboard) => {
      const updated = racks.map((r) => {
        if (r.id !== rackId) return r;
        return {
          ...r,
          slots: r.slots.map((s) =>
            s.id === slotId ? { ...s, motherboard: board } : s
          ),
        };
      });
      persist(updated);
    },
    [racks, persist]
  );

  const clearSlot = useCallback(
    (rackId: string, slotId: string) => {
      const updated = racks.map((r) => {
        if (r.id !== rackId) return r;
        return {
          ...r,
          slots: r.slots.map((s) =>
            s.id === slotId ? { ...s, motherboard: undefined } : s
          ),
        };
      });
      persist(updated);
    },
    [racks, persist]
  );

  const expandRack = useCallback(
    (rackId: string) => {
      const updated = racks.map((r) => {
        if (r.id !== rackId) return r;
        const base = r.slots.length;
        const newSlots: RackSlot[] = Array.from({ length: 3 }, (_, i) => ({
          id: uuid(),
          position: base + i,
        }));
        return { ...r, slots: [...r.slots, ...newSlots] };
      });
      persist(updated);
    },
    [racks, persist]
  );

  return { racks, addRack, removeRack, assignMotherboard, clearSlot, expandRack };
}
