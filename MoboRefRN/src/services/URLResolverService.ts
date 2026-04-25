import { Motherboard } from '../models/Motherboard';

const INTEL_CHIPSETS = new Set([
  'Z890','B860','Z790','B760','Z690','B660','H610',
  'Z590','B560','H510','H570','Z490','B460','H470','H410',
  'Z390','Z370','B365','H370','B360','H310',
]);

function getArch(chipset: string): 'Intel' | 'AMD' {
  return INTEL_CHIPSETS.has(chipset.toUpperCase()) ? 'Intel' : 'AMD';
}

// Convert model name to a URL-safe hyphenated slug.
// Handles GIGABYTE rev notation: "(rev. 1.0)" → "-rev-10"
function hyphenate(s: string): string {
  return s
    .replace(/\s*\(rev\.\s*([\d.]+)\)/i, (_, v) => '-rev-' + v.replace(/\./g, ''))
    .replace(/[()]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '');
}

export function buildDirectProductUrl(board: Motherboard): string {
  const model = board.fullModelName;

  switch (board.brand) {
    case 'GIGABYTE':
      return `https://www.gigabyte.com/Motherboard/${hyphenate(model)}`;

    case 'MSI':
      return `https://www.msi.com/Motherboard/${hyphenate(model)}`;

    case 'ASUS': {
      const slug = hyphenate(model).toLowerCase();
      const category =
          /^rog\s+strix/i.test(model)    ? 'rog-strix'
        : /^rog\s+maximus/i.test(model)  ? 'rog-maximus'
        : /^rog\s+crosshair/i.test(model) ? 'rog-crosshair'
        : /^rog/i.test(model)            ? 'rog'
        : /^tuf/i.test(model)            ? 'tuf-gaming'
        : /^proart/i.test(model)         ? 'proart'
        : /^prime/i.test(model)          ? 'prime'
        :                                  'all-series';
      return `https://www.asus.com/motherboards-components/motherboards/${category}/${slug}/`;
    }

    case 'ASRock': {
      const arch = getArch(board.chipset);
      return `https://www.asrock.com/mb/${arch}/${encodeURIComponent(model)}/index.asp`;
    }

    default: {
      const domain = `${board.brand.toLowerCase()}.com`;
      const q = `"${model}" site:${domain}`;
      return `https://www.google.com/search?q=${encodeURIComponent(q)}`;
    }
  }
}

export function buildBrandSearchUrl(board: Motherboard): string {
  const domains: Record<string, string> = {
    ASUS: 'asus.com',
    GIGABYTE: 'gigabyte.com',
    MSI: 'msi.com',
    ASRock: 'asrock.com',
  };
  const domain = domains[board.brand] ?? `${board.brand.toLowerCase()}.com`;
  const q = `"${board.fullModelName}" site:${domain}`;
  return `https://www.google.com/search?q=${encodeURIComponent(q)}`;
}

export async function resolve(board: Motherboard): Promise<string> {
  if (board.officialSupportUrl) return board.officialSupportUrl;
  return buildDirectProductUrl(board);
}
