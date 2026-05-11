export type CPUBrand = 'INTEL' | 'AMD';

export interface CPU {
  id: string;
  brand: CPUBrand;
  gen: string;
  socket: string;
  codename?: string;
  fullModelName: string;
  isKSku?: boolean;
  maxOfficialDDRSpeed?: number;
  channels?: number;
  officialUrl?: string;
}
