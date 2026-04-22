import { Motherboard } from '../models/Motherboard';

const BRAND_DOMAINS: Record<string, string> = {
  ASUS: 'asus.com',
  GIGABYTE: 'gigabyte.com',
  MSI: 'msi.com',
  ASRock: 'asrock.com',
};

export function buildBrandSearchUrl(board: Motherboard): string {
  const model = board.fullModelName;
  const enc = encodeURIComponent(model);

  switch (board.brand) {
    case 'ASUS':
      return `https://www.asus.com/motherboards-components/motherboards/search/?q=${enc}`;
    case 'GIGABYTE':
      return `https://www.gigabyte.com/Search/Keyword#2700-${enc}`;
    case 'MSI':
      return `https://www.msi.com/search?keyword=${enc}&category=Motherboard`;
    case 'ASRock':
      return `https://www.asrock.com/mb/index.asp?s=${encodeURIComponent(board.chipset)}`;
    default: {
      const domain = BRAND_DOMAINS[board.brand] ?? `${board.brand.toLowerCase()}.com`;
      const q = encodeURIComponent(`site:${domain} "${model}" specifications`);
      return `https://www.google.com/search?q=${q}`;
    }
  }
}

export async function resolve(board: Motherboard): Promise<string> {
  // 1. Custom board with a user-confirmed URL — go directly
  if (board.officialSupportUrl) {
    return board.officialSupportUrl;
  }

  // 2. Brand-specific search page — much closer to the product than a Google query
  return buildBrandSearchUrl(board);
}
