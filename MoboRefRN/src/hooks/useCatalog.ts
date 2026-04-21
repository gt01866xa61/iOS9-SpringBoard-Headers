import { useState, useCallback, useMemo } from 'react';
import * as Linking from 'expo-linking';
import { Motherboard } from '../models/Motherboard';
import { fetchFullIndex } from '../services/ScrapingEngine';
import { resolve } from '../services/URLResolverService';

export function useCatalog() {
  const [allBoards, setAllBoards] = useState<Motherboard[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<string>('ALL');
  const [selectedChipset, setSelectedChipset] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(false);
  const [isResolvingUrl, setIsResolvingUrl] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const loadData = useCallback(async (forceRefresh = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchFullIndex(forceRefresh);
      console.log(`[useCatalog] fetchFullIndex returned ${data.length} boards`);
      if (data.length === 0) {
        setError('Fetched 0 results — check console for scraper logs');
      }
      setAllBoards(data);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error('[useCatalog] loadData error:', msg);
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refresh = useCallback(() => loadData(true), [loadData]);

  const openOfficialPage = useCallback(async (board: Motherboard) => {
    setIsResolvingUrl(true);
    try {
      const url = await resolve(board);
      await Linking.openURL(url);
    } finally {
      setIsResolvingUrl(false);
    }
  }, []);

  const selectBrand = useCallback(
    (brand: string) => {
      setSelectedBrand(brand);
      setSelectedChipset('ALL');
    },
    []
  );

  return {
    brands,
    chipsets,
    filteredModels,
    selectedBrand,
    selectedChipset,
    isLoading,
    isResolvingUrl,
    error,
    loadData,
    refresh,
    openOfficialPage,
    setSelectedBrand: selectBrand,
    setSelectedChipset,
  };
}
