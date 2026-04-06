import { Motherboard } from '../models/Motherboard';
import { fetchOfficialUrl } from './ScrapingEngine';

function toSupportUrl(url: string): string {
  // Try to redirect known brand home pages to their support/product pages
  if (url.includes('asus.com') && !url.includes('/support')) {
    return url.replace('asus.com', 'asus.com/support');
  }
  return url;
}

function googleFallback(board: Motherboard): string {
  const q = encodeURIComponent(
    `${board.brand} ${board.fullModelName} official support site`
  );
  return `https://www.google.com/search?q=${q}`;
}

export async function resolve(board: Motherboard): Promise<string> {
  // 1. Already have an official URL cached on the object
  if (board.officialSupportUrl) {
    return toSupportUrl(board.officialSupportUrl);
  }

  // 2. Stage-2 scrape: visit TPU detail page and look for manufacturer link
  const scraped = await fetchOfficialUrl(board);
  if (scraped) {
    return toSupportUrl(scraped);
  }

  // 3. Google fallback — always succeeds
  return googleFallback(board);
}
