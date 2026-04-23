import { useState, useCallback, useEffect } from 'react';
import * as SUS from '../services/SavedUrlsService';

// Module-level singleton: all hook instances share the same in-memory state.
// When any screen saves/removes a URL, every other screen is notified instantly.
let _cache: Record<string, string> = {};
let _loaded = false;
const _listeners = new Set<(urls: Record<string, string>) => void>();

function broadcast(urls: Record<string, string>) {
  _cache = urls;
  _listeners.forEach((fn) => fn({ ...urls }));
}

export function useSavedUrls() {
  const [savedUrls, setSavedUrls] = useState<Record<string, string>>(_cache);

  useEffect(() => {
    _listeners.add(setSavedUrls);
    if (!_loaded) {
      _loaded = true;
      SUS.getSavedUrls().then(broadcast);
    } else {
      setSavedUrls({ ..._cache });
    }
    return () => { _listeners.delete(setSavedUrls); };
  }, []);

  const saveUrl = useCallback(async (boardId: string, url: string) => {
    await SUS.saveUrl(boardId, url);
    broadcast({ ..._cache, [boardId]: url });
  }, []);

  const removeUrl = useCallback(async (boardId: string) => {
    await SUS.removeUrl(boardId);
    const next = { ..._cache };
    delete next[boardId];
    broadcast(next);
  }, []);

  return { savedUrls, saveUrl, removeUrl };
}
