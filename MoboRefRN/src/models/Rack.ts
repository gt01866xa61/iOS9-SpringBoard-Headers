import { Motherboard } from './Motherboard';

export interface RackSlot {
  id: string;
  space: number;      // 0-indexed absolute grid coordinate — never changes unless compacted
  motherboard?: Motherboard;
}

export interface Rack {
  id: string;
  name: string;
  totalSpaces: number; // total grid positions (always a multiple of 3)
  slots: RackSlot[];   // slots that exist; length <= totalSpaces (sparse is allowed)
  createdAt: number;
}
