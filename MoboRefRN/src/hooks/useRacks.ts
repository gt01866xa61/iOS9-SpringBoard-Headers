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
          const parsed: Rack[] = JSON.parse(raw);
          // Re-sort and re-number positions so they are always 0…n-1.
          // Fixes data corrupted by old removeSlot code that left gaps/duplicates.
          const normalized = parsed.map(r => ({
            ...r,
            slots: [...r.slots]
              .sort((a, b) => a.position - b.position)
              .map((s, i) => ({ ...s, position: i })),
          }));
          setRacks(normalized);
          AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
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

  const removeRow = useCallback(
    (rackId: string, rowIndex: number) => {
      const updated = racks.map((r) => {
        if (r.id !== rackId) return r;
        const start = rowIndex * 3;
        const remaining = r.slots.filter((_, i) => i < start || i >= start + 3);
        const reindexed = remaining.map((s, i) => ({ ...s, position: i }));
        return { ...r, slots: reindexed };
      });
      persist(updated);
    },
    [racks, persist]
  );

  // Remove a single slot entirely; remaining slots are reindexed compactly.
  const removeSlot = useCallback(
    (rackId: string, slotId: string) => {
      const updated = racks.map((r) => {
        if (r.id !== rackId) return r;
        const remaining = r.slots.filter((s) => s.id !== slotId);
        return { ...r, slots: remaining.map((s, i) => ({ ...s, position: i })) };
      });
      persist(updated);
    },
    [racks, persist]
  );

  // iPhone-style move: remove slot from source index, insert at destination index,
  // slots between the two positions shift to fill the gap (no swap, no jump).
  const moveSlot = useCallback(
    (rackId: string, fromId: string, toId: string) => {
      const updated = racks.map((r) => {
        if (r.id !== rackId) return r;
        const sorted = [...r.slots].sort((a, b) => a.position - b.position);
        const fromIdx = sorted.findIndex((s) => s.id === fromId);
        const toIdx = sorted.findIndex((s) => s.id === toId);
        if (fromIdx === -1 || toIdx === -1 || fromIdx === toIdx) return r;
        const [moved] = sorted.splice(fromIdx, 1);
        sorted.splice(toIdx, 0, moved);
        return { ...r, slots: sorted.map((s, i) => ({ ...s, position: i })) };
      });
      persist(updated);
    },
    [racks, persist]
  );

  return { racks, addRack, removeRack, assignMotherboard, clearSlot, expandRack, removeRow, removeSlot, moveSlot };
}
