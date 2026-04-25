import { useState, useCallback, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Rack, RackSlot } from '../models/Rack';
import { Motherboard } from '../models/Motherboard';

const KEY_V1 = 'racks_v1';
const KEY_V2 = 'racks_v2';
const COLS = 3;

function uuid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function migrateV1(raw: any[]): Rack[] {
  return raw.map((r) => {
    const sorted = [...(r.slots ?? [])].sort(
      (a: any, b: any) => (a.position ?? a.space ?? 0) - (b.position ?? b.space ?? 0)
    );
    const slots: RackSlot[] = sorted.map((s: any, i: number) => ({
      id: s.id,
      space: i,
      motherboard: s.motherboard,
    }));
    const totalSpaces = slots.length === 0 ? 9 : Math.ceil(slots.length / COLS) * COLS;
    return { id: r.id, name: r.name, totalSpaces, slots, createdAt: r.createdAt ?? Date.now() };
  });
}

export function useRacks() {
  const [racks, setRacks] = useState<Rack[]>([]);

  useEffect(() => {
    (async () => {
      const v2 = await AsyncStorage.getItem(KEY_V2);
      if (v2) {
        try { setRacks(JSON.parse(v2)); return; } catch { /* fallthrough */ }
      }
      const v1 = await AsyncStorage.getItem(KEY_V1);
      if (v1) {
        try {
          const migrated = migrateV1(JSON.parse(v1));
          setRacks(migrated);
          await AsyncStorage.setItem(KEY_V2, JSON.stringify(migrated));
        } catch { /* ignore */ }
      }
    })();
  }, []);

  const persist = useCallback(async (updated: Rack[]) => {
    setRacks(updated);
    await AsyncStorage.setItem(KEY_V2, JSON.stringify(updated));
  }, []);

  const addRack = useCallback(
    (name: string) => {
      const slots: RackSlot[] = Array.from({ length: 9 }, (_, i) => ({ id: uuid(), space: i }));
      persist([...racks, { id: uuid(), name, slots, totalSpaces: 9, createdAt: Date.now() }]);
    },
    [racks, persist]
  );

  const removeRack = useCallback(
    (rackId: string) => persist(racks.filter((r) => r.id !== rackId)),
    [racks, persist]
  );

  const assignMotherboard = useCallback(
    (rackId: string, slotId: string, board: Motherboard) => {
      persist(
        racks.map((r) =>
          r.id !== rackId
            ? r
            : { ...r, slots: r.slots.map((s) => (s.id === slotId ? { ...s, motherboard: board } : s)) }
        )
      );
    },
    [racks, persist]
  );

  // Red ×: remove board info from slot; slot framework stays in place.
  const clearSlot = useCallback(
    (rackId: string, slotId: string) => {
      persist(
        racks.map((r) =>
          r.id !== rackId
            ? r
            : { ...r, slots: r.slots.map((s) => (s.id === slotId ? { ...s, motherboard: undefined } : s)) }
        )
      );
    },
    [racks, persist]
  );

  // Gray ×: delete the slot framework and compact — every slot after it shifts one space forward.
  const deleteSlot = useCallback(
    (rackId: string, slotId: string) => {
      persist(
        racks.map((r) => {
          if (r.id !== rackId) return r;
          const slot = r.slots.find((s) => s.id === slotId);
          if (!slot) return r;
          const S = slot.space;
          const remaining = r.slots
            .filter((s) => s.id !== slotId)
            .map((s) => (s.space > S ? { ...s, space: s.space - 1 } : s));
          return { ...r, slots: remaining };
        })
      );
    },
    [racks, persist]
  );

  // "+" on empty space: restore a slot at that coordinate.
  const addSlotAtSpace = useCallback(
    (rackId: string, space: number) => {
      persist(
        racks.map((r) => {
          if (r.id !== rackId) return r;
          if (space >= r.totalSpaces) return r;
          if (r.slots.some((s) => s.space === space)) return r;
          return { ...r, slots: [...r.slots, { id: uuid(), space }] };
        })
      );
    },
    [racks, persist]
  );

  // Add row: 3 more spaces + 3 new empty slots.
  const expandRack = useCallback(
    (rackId: string) => {
      persist(
        racks.map((r) => {
          if (r.id !== rackId) return r;
          const start = r.totalSpaces;
          const newSlots: RackSlot[] = Array.from({ length: 3 }, (_, i) => ({ id: uuid(), space: start + i }));
          return { ...r, slots: [...r.slots, ...newSlots], totalSpaces: r.totalSpaces + 3 };
        })
      );
    },
    [racks, persist]
  );

  // Remove an entire row: delete its spaces + compact remaining.
  const removeRow = useCallback(
    (rackId: string, rowIndex: number) => {
      persist(
        racks.map((r) => {
          if (r.id !== rackId) return r;
          const start = rowIndex * COLS;
          const end = start + COLS;
          const remaining = r.slots
            .filter((s) => s.space < start || s.space >= end)
            .map((s) => (s.space >= end ? { ...s, space: s.space - COLS } : s));
          return { ...r, slots: remaining, totalSpaces: r.totalSpaces - COLS };
        })
      );
    },
    [racks, persist]
  );

  // Move a slot to toSpace.
  // Empty target → direct move (only dragged slot changes space).
  // Occupied target → iPhone-style insert: treat all existing slots as a sorted list,
  //   splice-insert, then re-assign back to the same set of occupied spaces.
  const moveSlot = useCallback(
    (rackId: string, fromId: string, toSpace: number) => {
      persist(
        racks.map((r) => {
          if (r.id !== rackId) return r;
          const fromSlot = r.slots.find((s) => s.id === fromId);
          if (!fromSlot || fromSlot.space === toSpace) return r;

          const targetSlot = r.slots.find((s) => s.space === toSpace);
          if (!targetSlot) {
            // Empty space: just relocate
            return { ...r, slots: r.slots.map((s) => (s.id === fromId ? { ...s, space: toSpace } : s)) };
          }

          // Occupied: splice-insert over the existing occupied spaces
          const sorted = [...r.slots].sort((a, b) => a.space - b.space);
          const fromIdx = sorted.findIndex((s) => s.id === fromId);
          const toIdx = sorted.findIndex((s) => s.id === targetSlot.id);
          const occupiedSpaces = sorted.map((s) => s.space);
          const [moved] = sorted.splice(fromIdx, 1);
          sorted.splice(toIdx, 0, moved);
          return { ...r, slots: sorted.map((s, i) => ({ ...s, space: occupiedSpaces[i] })) };
        })
      );
    },
    [racks, persist]
  );

  return {
    racks,
    addRack,
    removeRack,
    assignMotherboard,
    clearSlot,
    deleteSlot,
    addSlotAtSpace,
    expandRack,
    removeRow,
    moveSlot,
  };
}
