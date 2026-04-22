import { useState, useCallback, useEffect } from 'react';
import * as SUS from '../services/SavedUrlsService';

export function useSavedUrls() {
  const [savedUrls, setSavedUrls] = useState<Record<string, string>>({});

  useEffect(() => {
    SUS.getSavedUrls().then(setSavedUrls);
  }, []);

  const saveUrl = useCallback(async (boardId: string, url: string) => {
    await SUS.saveUrl(boardId, url);
    setSavedUrls((prev) => ({ ...prev, [boardId]: url }));
  }, []);

  const removeUrl = useCallback(async (boardId: string) => {
    await SUS.removeUrl(boardId);
    setSavedUrls((prev) => {
      const next = { ...prev };
      delete next[boardId];
      return next;
    });
  }, []);

  return { savedUrls, saveUrl, removeUrl };
}
