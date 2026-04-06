import { Motherboard } from './Motherboard';

export interface RackSlot {
  id: string;
  position: number;
  motherboard?: Motherboard;
}

export interface Rack {
  id: string;
  name: string;
  slots: RackSlot[];
  createdAt: number;
}
