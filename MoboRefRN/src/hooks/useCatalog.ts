import { useState, useCallback, useMemo } from 'react';
import * as Linking from 'expo-linking';
import { Motherboard } from '../models/Motherboard';
import { STATIC_BOARDS } from '../data/StaticBoardData';
import { resolve } from '../services/URLResolverService';
import { useCustomBoards } from './useCustomBoards';
import { useSavedUrls } from './useSavedUrls';

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
    return ['ALL', ...Array.from(set).sort()];
  }, [allBoards]);

  const chipsets = useMemo(() => {
    const filtered =
      selectedBrand === 'ALL'
        ? allBoards
        : allBoards.filter((b) => b.brand === selectedBrand);
    const set = new Set(filtered.map((b) => b.chipset));
    return ['ALL', ...Array.from(set).sort()];
  }, [allBoards, selectedBrand]);

  const filteredModels = useMemo(() => {
    return allBoards.filter((b) => {
      const brandMatch = selectedBrand === 'ALL' || b.brand === selectedBrand;
      const chipsetMatch =
        selectedChipset === 'ALL' || b.chipset === selectedChipset;
      return brandMatch && chipsetMatch;
    });
  }, [allBoards, selectedBrand, selectedChipset]);

  const openOfficialPage = useCallback(
    async (board: Motherboard) => {
      setIsResolvingUrl(true);
      try {
        // Priority: user-saved URL → custom board URL → Google site: search
        const url = savedUrls[board.id] ?? (await resolve(board));
        await Linking.openURL(url);
      } finally {
        setIsResolvingUrl(false);
      }
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
