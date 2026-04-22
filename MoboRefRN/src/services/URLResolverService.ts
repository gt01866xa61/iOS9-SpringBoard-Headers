import { Motherboard } from '../models/Motherboard';

// Convert model name to a URL-friendly slug (spaces → hyphens, strip parens for rev)
function toSlug(name: string): string {
  return name
    .replace(/\s*\(rev\.?\s*(\d+)\.?(\d*)\)/i, (_, major, minor) =>
      `-rev-${major}${minor || '0'}`)
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9\-]/g, '');
}

// Determine if a chipset is AMD or Intel based on known prefixes
function chipsetArch(chipset: string): 'AMD' | 'Intel' {
  const cs = chipset.toUpperCase();
  // Intel-only prefixes: Z (Z790/Z690...), H (H610/H570...), W (workstation)
  if (/^[ZHW]\d/.test(cs)) return 'Intel';
  // AMD-only chipsets that share B/X prefixes with Intel need special handling
  // AMD AM4/AM5: X870, X670, B650, B550, X570, B450, X470, A520, A320
  // Intel: B760, B660, B560, B460, X299 (HEDT)
  // Heuristic: 3-digit number starting with 4xx/5xx/6xx/7xx AMD vs Intel
  const num = parseInt(cs.replace(/\D/g, ''), 10);
  if (cs.startsWith('A')) return 'AMD'; // A520, A320 are AMD only
  if (cs.startsWith('B') || cs.startsWith('X')) {
    // B450, B550, B650 = AMD; B460, B560, B660, B760 = Intel
    // X570, X470, X670, X870 = AMD; X299 = Intel HEDT
    if (num >= 400 && num < 500) return num % 10 === 0 ? 'Intel' : 'AMD'; // B460=Intel, B450=AMD
    if (num >= 500 && num < 600) return num % 10 === 0 ? 'Intel' : 'AMD'; // B560=Intel, B550=AMD
    if (num >= 600 && num < 700) return num % 10 === 0 ? 'Intel' : 'AMD'; // B660=Intel, B650=AMD
    if (num >= 700) return num % 10 === 0 ? 'Intel' : 'AMD'; // B760=Intel, B650E/X670=AMD
    if (num < 400) return 'Intel'; // X299 HEDT
  }
  return 'Intel';
}

export function buildBrandSearchUrl(board: Motherboard): string {
  const model = board.fullModelName;
  const enc = encodeURIComponent(model);
  const slug = toSlug(model);

  switch (board.brand) {
    case 'ASUS':
      // Global ASUS search — the category-specific search URL is broken
      return `https://www.asus.com/search/?q=${enc}`;

    case 'GIGABYTE':
      // Direct product page — slug matches Gigabyte's URL convention
      return `https://www.gigabyte.com/Motherboard/${slug}`;

    case 'MSI':
      // Direct product page — MSI uses same slug pattern
      return `https://www.msi.com/Motherboard/${slug}`;

    case 'ASRock': {
      const arch = chipsetArch(board.chipset);
      return `https://www.asrock.com/mb/${arch}/${encodeURIComponent(model)}/`;
    }

    default: {
      const domain = `${board.brand.toLowerCase()}.com`;
      const q = encodeURIComponent(`"${model}" site:${domain}`);
      return `https://www.google.com/search?q=${q}`;
    }
  }
}

export async function resolve(board: Motherboard): Promise<string> {
  // Custom board with user-confirmed URL — go directly
  if (board.officialSupportUrl) {
    return board.officialSupportUrl;
  }

  return buildBrandSearchUrl(board);
}
