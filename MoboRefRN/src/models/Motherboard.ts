export interface DramCompatRule {
  cpuMatch: {
    socket?: string;
    gen?: string;
    isKSku?: boolean;
    minDDRSpeed?: number;
  };
  maxDDRSpeed: number;
  modes?: ('XMP' | 'EXPO' | 'JEDEC')[];
  dimmsFilled?: 1 | 2 | 4;
  notes?: string;
}

export interface Motherboard {
  id: string;
  brand: string;
  chipset: string;
  fullModelName: string;
  tpuDetailUrl?: string;
  officialSupportUrl?: string;
  isCustom?: boolean;
  socket?: string;
  dramCompat?: DramCompatRule[];
}
