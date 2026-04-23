import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { Motherboard } from '../models/Motherboard';

const RAW_URL =
  'https://raw.githubusercontent.com/gt01866xa61/iOS9-SpringBoard-Headers/claude/build-iphone-app-3HKVs/MoboRefRN/boards.json';

const CACHE_KEY = 'remote_boards_v2';
const TTL = 24 * 60 * 60 * 1000; // 24h

interface BoardsFile {
  version: string;
  count: number;
  boards: Motherboard[];
}

interface CacheEntry {
  fetchedAt: number;
  data: BoardsFile;
}

export interface FetchResult {
  boards: Motherboard[];
  version: string;
  newCount: number;
  fromCache: boolean;
}

async function readCache(): Promise<CacheEntry | null> {
  try {
    const raw = await AsyncStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function writeCache(data: BoardsFile): Promise<void> {
  const entry: CacheEntry = { fetchedAt: Date.now(), data };
  await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(entry));
}

export async function fetchBoards(forceRefresh = false): Promise<FetchResult> {
  const cache = await readCache();
  const now = Date.now();
  const isFresh = cache && now - cache.fetchedAt < TTL;

  if (!forceRefresh && isFresh && cache) {
    return { boards: cache.data.boards, version: cache.data.version, newCount: 0, fromCache: true };
  }

  try {
    const res = await axios.get<BoardsFile>(RAW_URL, { timeout: 10000 });
    const fresh = res.data;
    const prevCount = cache?.data.boards.length ?? 0;
    const newCount = Math.max(0, fresh.boards.length - prevCount);
    await writeCache(fresh);
    return { boards: fresh.boards, version: fresh.version, newCount, fromCache: false };
  } catch (err) {
    if (cache) {
      return { boards: cache.data.boards, version: cache.data.version, newCount: 0, fromCache: true };
    }
    throw err;
  }
}
