import { useState, useCallback, useMemo, useEffect } from 'react';
import { Motherboard } from '../models/Motherboard';
import { STATIC_BOARDS } from '../data/StaticBoardData';
import { resolve } from '../services/URLResolverService';
import { fetchBoards } from '../services/RemoteBoardsService';
import { useCustomBoards } from './useCustomBoards';
import { useSavedUrls } from './useSavedUrls';
import { useVisitedBoards } from './useVisitedBoards';

const BRAND_ORDER = ['ASUS', 'GIGABYTE', 'MSI', 'ASRock'];

function sortBrands(arr: string[]): string[] {
  return arr.sort((a, b) => {
    const ia = BRAND_ORDER.indexOf(a);
    const ib = BRAND_ORDER.indexOf(b);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return a.localeCompare(b);
  });
}

function chipsetNum(cs: string): number {
  return parseInt(cs.replace(/\D/g, ''), 10) || 0;
}

export function useCatalog() {
  const { customBoards, addCustomBoard, removeCustomBoard } = useCustomBoards();
  const { savedUrls, saveUrl, removeUrl: removeSavedUrl, clearAll: clearAllUrls } = useSavedUrls();
  const { visitRecord, markConfirmed, markWrong, clearStatus, clearAll: clearAllVisited } = useVisitedBoards();
  const [selectedBrand, setSelectedBrand] = useState<string>('ALL');
  const [selectedChipset, setSelectedChipset] = useState<string>('ALL');
  // Remote boards state
  const [remoteBoards, setRemoteBoards] = useState<Motherboard[]>(STATIC_BOARDS);
  const [version, setVersion] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [newBoardsCount, setNewBoardsCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (forceRefresh = false) => {
    setIsRefreshing(true);
    setError(null);
    try {
      const res = await fetchBoards(forceRefresh);
      setRemoteBoards(res.boards);
      setVersion(res.version);
      setNewBoardsCount(res.newCount);
    } catch (e: any) {
      setError('Offline — using built-in catalog');
      // keep STATIC_BOARDS as the fallback (initial state)
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const refresh = useCallback(() => loadData(true), [loadData]);

  useEffect(() => {
    loadData(false);
  }, [loadData]);

  const allBoards = useMemo(
    () => [...customBoards, ...remoteBoards],
    [customBoards, remoteBoards]
  );

  const brands = useMemo(() => {
    const set = new Set(allBoards.map((b) => b.brand));
    return ['ALL', ...sortBrands(Array.from(set))];
  }, [allBoards]);

  const chipsets = useMemo(() => {
    const filtered =
      selectedBrand === 'ALL'
        ? allBoards
        : allBoards.filter((b) => b.brand === selectedBrand);
    const set = new Set(filtered.map((b) => b.chipset));
    return ['ALL', ...Array.from(set).sort((a, b) => chipsetNum(b) - chipsetNum(a))];
  }, [allBoards, selectedBrand]);

  const filteredModels = useMemo(() => {
    return allBoards.filter((b) => {
      const brandMatch = selectedBrand === 'ALL' || b.brand === selectedBrand;
      const chipsetMatch =
        selectedChipset === 'ALL' || b.chipset === selectedChipset;
      return brandMatch && chipsetMatch;
    });
  }, [allBoards, selectedBrand, selectedChipset]);

  const resolvePageUrl = useCallback(
    async (board: Motherboard): Promise<string> => {
      return savedUrls[board.id] ?? (await resolve(board));
    },
    [savedUrls]
  );

  const selectBrand = useCallback((brand: string) => {
    setSelectedBrand(brand);
    setSelectedChipset('ALL');
  }, []);

  const clearNewBoardsCount = useCallback(() => setNewBoardsCount(0), []);

  // Reset everything we know about a board's URL — used by the Edit Status flow
  // to take a board back to "not yet confirmed" regardless of which badge it had.
  const resetBoardState = useCallback(
    (id: string) => {
      removeSavedUrl(id);
      clearStatus(id);
    },
    [removeSavedUrl, clearStatus]
  );

  const clearAllState = useCallback(() => {
    clearAllUrls();
    clearAllVisited();
  }, [clearAllUrls, clearAllVisited]);

  return {
    brands,
    chipsets,
    filteredModels,
    selectedBrand,
    selectedChipset,
    isLoading: false,
    isRefreshing,
    version,
    newBoardsCount,
    error,
    loadData,
    refresh,
    resolvePageUrl,
    setSelectedBrand: selectBrand,
    setSelectedChipset,
    addCustomBoard,
    removeCustomBoard,
    savedUrls,
    saveUrl,
    removeSavedUrl,
    visitRecord,
    markConfirmed,
    markWrong,
    resetBoardState,
    clearAllState,
    clearNewBoardsCount,
  };
}
