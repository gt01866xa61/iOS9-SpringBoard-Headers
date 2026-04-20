import axios from 'axios';
import { parse } from 'node-html-parser';
import { Motherboard } from '../models/Motherboard';
import { CacheService } from './CacheService';

const SCRAPING_CONFIG = {
  baseUrl: 'https://www.techpowerup.com',
  indexPath: '/review/?category=Motherboards&manufacturer=',
  indexRowSelector: 'table.reviewlist tbody tr',
  indexLinkSelector: 'td.name a',
  brands: ['ASUS', 'GIGABYTE', 'MSI', 'ASRock'],
  detailLinkPatterns: [
    'asus.com',
    'gigabyte.com',
    'msi.com',
    'asrock.com',
  ],
  knownChipsets: [
    // Intel
    'Z890', 'B860', 'H810',
    'Z790', 'B760', 'H770', 'H610',
    'Z690', 'B660', 'H670', 'H610',
    'Z590', 'B560', 'H570', 'H510',
    'Z490', 'B460', 'H470', 'H410',
    // AMD
    'X870E', 'X870', 'B850', 'B840',
    'X670E', 'X670', 'B650E', 'B650',
    'X570', 'B550', 'A520',
    'X470', 'B450', 'A320',
  ],
};

const CACHE_KEY_INDEX = 'cache:mobo_index';

function detectChipset(modelName: string): string {
  const upper = modelName.toUpperCase();
  for (const chipset of SCRAPING_CONFIG.knownChipsets) {
    if (upper.includes(chipset)) return chipset;
  }
  return 'Other';
}

function buildId(brand: string, model: string): string {
  return `${brand}::${model}`.toLowerCase().replace(/\s+/g, '_');
}

async function fetchBrandPage(brand: string): Promise<Motherboard[]> {
  const url = `${SCRAPING_CONFIG.baseUrl}${SCRAPING_CONFIG.indexPath}${encodeURIComponent(brand)}`;
  console.log(`[Scraper] Fetching ${brand}: ${url}`);
  try {
    const response = await axios.get<string>(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
      },
      timeout: 20000,
    });
    console.log(`[Scraper] ${brand} HTTP ${response.status}, HTML ${response.data.length} bytes`);
    const root = parse(response.data);
    const rows = root.querySelectorAll(SCRAPING_CONFIG.indexRowSelector);
    console.log(`[Scraper] ${brand} rows found: ${rows.length}`);
    const results: Motherboard[] = [];

    for (const row of rows) {
      const link = row.querySelector(SCRAPING_CONFIG.indexLinkSelector);
      if (!link) continue;
      const fullModelName = link.text.trim();
      if (!fullModelName) continue;
      const href = link.getAttribute('href') ?? '';
      const tpuDetailUrl = href.startsWith('http')
        ? href
        : `${SCRAPING_CONFIG.baseUrl}${href}`;

      results.push({
        id: buildId(brand, fullModelName),
        brand,
        chipset: detectChipset(fullModelName),
        fullModelName,
        tpuDetailUrl,
      });
    }
    console.log(`[Scraper] ${brand} parsed ${results.length} boards`);
    return results;
  } catch (err) {
    console.error(`[Scraper] ${brand} failed:`, err instanceof Error ? err.message : err);
    throw err;
  }
}

export async function fetchFullIndex(forceRefresh = false): Promise<Motherboard[]> {
  if (!forceRefresh) {
    const cached = await CacheService.get<Motherboard[]>(CACHE_KEY_INDEX);
    if (cached) return cached;
  }

  const results = await Promise.allSettled(
    SCRAPING_CONFIG.brands.map((b) => fetchBrandPage(b))
  );

  const all: Motherboard[] = [];
  const seen = new Set<string>();
  for (const r of results) {
    if (r.status === 'fulfilled') {
      for (const board of r.value) {
        if (!seen.has(board.id)) {
          seen.add(board.id);
          all.push(board);
        }
      }
    }
  }

  if (all.length > 0) {
    await CacheService.set(CACHE_KEY_INDEX, all);
  }
  return all;
}

export async function fetchOfficialUrl(board: Motherboard): Promise<string | null> {
  if (!board.tpuDetailUrl) return null;
  try {
    const response = await axios.get<string>(board.tpuDetailUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; MoboRefApp/1.0)' },
      timeout: 15000,
    });
    const root = parse(response.data);
    const links = root.querySelectorAll('a[href]');
    for (const link of links) {
      const href = link.getAttribute('href') ?? '';
      if (SCRAPING_CONFIG.detailLinkPatterns.some((p) => href.includes(p))) {
        return href;
      }
    }
  } catch {
    // swallow — caller will fall back to Google
  }
  return null;
}
