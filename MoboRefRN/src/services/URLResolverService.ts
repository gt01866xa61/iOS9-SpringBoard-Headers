import { Motherboard } from '../models/Motherboard';

const BRAND_DOMAINS: Record<string, string> = {
  ASUS: 'asus.com',
  GIGABYTE: 'gigabyte.com',
  MSI: 'msi.com',
  ASRock: 'asrock.com',
};

export function buildBrandSearchUrl(board: Motherboard): string {
  const domain = BRAND_DOMAINS[board.brand] ?? `${board.brand.toLowerCase()}.com`;

  // Google site: search reliably surfaces the official product page as the
  // first result. Brand-specific search pages all use JS-driven routing that
  // breaks when opened from external links, and direct product slug guessing
  // is fragile (rev numbers, casing, prefix variations).
  const query = `"${board.fullModelName}" site:${domain}`;
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

export async function resolve(board: Motherboard): Promise<string> {
  // Custom board with user-confirmed URL — go directly
  if (board.officialSupportUrl) {
    return board.officialSupportUrl;
  }

  return buildBrandSearchUrl(board);
}
