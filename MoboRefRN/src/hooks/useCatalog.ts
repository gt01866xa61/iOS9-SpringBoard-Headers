import { useState, useCallback, useMemo } from 'react';
import * as WebBrowser from 'expo-web-browser';
import { Motherboard } from '../models/Motherboard';
import { STATIC_BOARDS } from '../data/StaticBoardData';
import { resolve } from '../services/URLResolverService';
import { useCustomBoards } from './useCustomBoards';
import { useSavedUrls } from './useSavedUrls';

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
  const { savedUrls, saveUrl, removeUrl: removeSavedUrl } = useSavedUrls();
  const [selectedBrand, setSelectedBrand] = useState<string>('ALL');
  const [selectedChipset, setSelectedChipset] = useState<string>('ALL');
  const [isResolvingUrl, setIsResolvingUrl] = useState(false);

  const allBoards = useMemo(
    () => [...customBoards, ...STATIC_BOARDS],
    [customBoards]
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
    // Descending by number (Z890 > Z790 > B860 ...)
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

  // Returns true if the caller should prompt the user to save a URL
  // (i.e. board had no saved URL and was opened via Google search)
  const openOfficialPage = useCallback(
    async (board: Motherboard): Promise<boolean> => {
      setIsResolvingUrl(true);
      const hasSaved = !!savedUrls[board.id];
      try {
        const url = savedUrls[board.id] ?? (await resolve(board));
        await WebBrowser.openBrowserAsync(url, {
          dismissButtonStyle: 'done',
          presentationStyle: WebBrowser.WebBrowserPresentationStyle.PAGE_SHEET,
        });
      } finally {
        setIsResolvingUrl(false);
      }
      return !hasSaved;
    },
    [savedUrls]
  );

  const selectBrand = useCallback((brand: string) => {
    setSelectedBrand(brand);
    setSelectedChipset('ALL');
  }, []);

  return {
    brands,
    chipsets,
    filteredModels,
    selectedBrand,
    selectedChipset,
    isLoading: false,
    isResolvingUrl,
    error: null,
    loadData: useCallback(() => Promise.resolve(), []),
    refresh: useCallback(() => Promise.resolve(), []),
    openOfficialPage,
    setSelectedBrand: selectBrand,
    setSelectedChipset,
    addCustomBoard,
    removeCustomBoard,
    savedUrls,
    saveUrl,
    removeSavedUrl,
  };
}
