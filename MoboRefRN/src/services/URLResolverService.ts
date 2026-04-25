import { Motherboard } from '../models/Motherboard';

const INTEL_CHIPSETS = new Set([
  'Z890','B860','Z790','B760','Z690','B660','H610',
  'Z590','B560','H510','H570','Z490','B460','H470','H410',
  'Z390','Z370','B365','H370','B360','H310',
]);

function getArch(chipset: string): 'Intel' | 'AMD' {
  return INTEL_CHIPSETS.has(chipset.toUpperCase()) ? 'Intel' : 'AMD';
}

export function isIntelChipset(chipset: string): boolean {
  return INTEL_CHIPSETS.has(chipset.toUpperCase());
}

// Convert model name to a URL-safe hyphenated slug.
// Handles GIGABYTE rev notation: "(rev. 1.0)" → "-rev-10"
// Old-style ASUS "(WIFI)" in parens → treated as "(WI-FI)" so URL gets "wi-fi"
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
    case 'GIGABYTE': {
      const slug = hyphenate(model);
      // GIGABYTE URLs always include a revision suffix.
      // If not in the model name, default to rev 1.0 (the most common first revision).
      const hasRev = /-rev-\d/i.test(slug);
      return `https://www.gigabyte.com/Motherboard/${slug}${hasRev ? '' : '-rev-10'}`;
    }

    case 'MSI': {
      // Boards from A520/B450 era and older are commonly discontinued on MSI's site —
      // product pages 404. Fall back to Google with site: constraint instead.
      const MSI_OLD = new Set(['A520','B450','X470','B350','A320','H310','B365','B360','H370']);
      if (MSI_OLD.has(board.chipset.toUpperCase())) {
        const q = `"${model}" site:msi.com`;
        return `https://www.google.com/search?q=${encodeURIComponent(q)}`;
      }
      return `https://www.msi.com/Motherboard/${hyphenate(model)}`;
    }

    case 'ASUS': {
      // Old-style "(WIFI)" with parens → URL uses "wi-fi" (hyphenated).
      // New-style "WIFI" without parens → URL uses "wifi" (no hyphen).
      const normalized = model.replace(/\(wifi\)/i, '(WI-FI)');
      const slug = hyphenate(normalized).toLowerCase();

      // ROG slugs are inconsistent across eras — newest-gen omits -model, older
      // ones append it, WIFI II variants omit it again, and WIFI vs WI-FI varies
      // per product. We can only reliably build URLs for the newest gen. Older
      // ROG boards fall back to Google site:rog.asus.com (1 extra click, but
      // always reaches the right page; user can long-press to save direct URL).
      if (/^rog/i.test(model)) {
        const NEWEST = new Set(['Z890','B860','H810','X870E','X870','B850','B840']);
        if (NEWEST.has(board.chipset.toUpperCase())) {
          const subdir =
              /^rog\s+strix/i.test(model)     ? 'rog-strix'
            : /^rog\s+maximus/i.test(model)   ? 'rog-maximus'
            : /^rog\s+crosshair/i.test(model) ? 'rog-crosshair'
            :                                   '';
          const path = subdir ? `${subdir}/${slug}` : slug;
          return `https://rog.asus.com/motherboards/${path}/`;
        }
        const q = `"${model}" site:rog.asus.com`;
        return `https://www.google.com/search?q=${encodeURIComponent(q)}`;
      }

      // CSM (commercial-stable) variants live under /csm/ regardless of prefix
      if (/-csm$/i.test(model)) {
        return `https://www.asus.com/motherboards-components/motherboards/csm/${slug}/`;
      }

      const category =
          /^tuf/i.test(model)    ? 'tuf-gaming'
        : /^proart/i.test(model) ? 'proart'
        : /^prime/i.test(model)  ? 'prime'
        :                          'all-series';
      return `https://www.asus.com/motherboards-components/motherboards/${category}/${slug}/`;
    }

    case 'ASRock': {
      const arch = getArch(board.chipset);
      // Strip DDR-gen suffixes (D4/D5) — ASRock omits these from URL slugs.
      // Normalize leading all-caps product names (e.g. "PHANTOM GAMING" → "Phantom Gaming").
      const slug = model
        .replace(/\s+D[45]\b/i, '')
        .replace(/\/D[45]\b/i, '')
        .replace(/\b[A-Z]{4,}\b/g, (w) => w[0] + w.slice(1).toLowerCase());

      // "Phantom Gaming" line uses pg.asrock.com and drops the series prefix from the URL path.
      if (/^Phantom\s+Gaming\s+/i.test(slug)) {
        const modelPart = slug.replace(/^Phantom\s+Gaming\s+/i, '');
        return `https://pg.asrock.com/mb/${arch}/${encodeURIComponent(modelPart)}/index.asp`;
      }

      return `https://www.asrock.com/mb/${arch}/${encodeURIComponent(slug)}/index.asp`;
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
