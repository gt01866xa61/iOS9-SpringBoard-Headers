import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  ScrollView,
  Keyboard,
} from 'react-native';
import { useCatalog } from '../hooks/useCatalog';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { SaveUrlModal } from '../components/SaveUrlModal';
import { BoardBadges } from '../components/BoardBadges';
import { Motherboard } from '../models/Motherboard';

export function CatalogScreen() {
  const {
    brands,
    chipsets,
    filteredModels,
    selectedBrand,
    selectedChipset,
    isLoading,
    isResolvingUrl,
    isRefreshing,
    version,
    newBoardsCount,
    error,
    refresh,
    openOfficialPage,
    setSelectedBrand,
    setSelectedChipset,
    removeCustomBoard,
    savedUrls,
    saveUrl,
    visitRecord,
    markConfirmed,
    markWrong,
    resetBoardState,
    clearAllState,
    clearNewBoardsCount,
  } = useCatalog();

  const [editMode, setEditMode] = useState(false);
  const [editUrlTarget, setEditUrlTarget] = useState<Motherboard | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // AND search: every space-separated token must appear in model+chipset+brand.
  const searchedModels = useMemo(() => {
    const tokens = searchQuery.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (tokens.length === 0) return filteredModels;
    return filteredModels.filter((b) => {
      const haystack = (b.fullModelName + ' ' + b.chipset + ' ' + b.brand).toLowerCase();
      return tokens.every((t) => haystack.includes(t));
    });
  }, [filteredModels, searchQuery]);

  // In edit mode, only show boards that have any label state.
  const displayedModels = useMemo(() => {
    if (!editMode) return searchedModels;
    return searchedModels.filter((b) => !!savedUrls[b.id] || !!visitRecord[b.id]);
  }, [editMode, searchedModels, savedUrls, visitRecord]);

  useEffect(() => {
    if (newBoardsCount > 0) {
      const t = setTimeout(() => clearNewBoardsCount(), 3000);
      return () => clearTimeout(t);
    }
  }, [newBoardsCount, clearNewBoardsCount]);

  const hasAnyState = Object.keys(savedUrls).length > 0 || Object.keys(visitRecord).length > 0;

  useEffect(() => {
    if (!hasAnyState) setEditMode(false);
  }, [hasAnyState]);

  const handleClearAll = () => {
    const total = Object.keys(savedUrls).length + Object.keys(visitRecord).length;
    Alert.alert(
      'Clear All Status',
      `Remove ALL saved URLs and visit marks for every board (${total} record${total !== 1 ? 's' : ''})?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear Everything',
          style: 'destructive',
          onPress: () =>
            Alert.alert(
              'Confirm Delete',
              'All board status data will be permanently deleted. This cannot be undone.',
              [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Delete All', style: 'destructive', onPress: clearAllState },
              ]
            ),
        },
      ]
    );
  };

  const handlePress = async (item: Motherboard) => {
    if (editMode) return;
    const result = await openOfficialPage(item);

    // Custom boards: auto-prompt to save the verified URL (their URLs are always guessed)
    if (item.isCustom && result.shouldPrompt) {
      setEditUrlTarget(item);
      return;
    }

    // Non-custom: ask on first visit OR when WRONG (re-confirm every time)
    if (!item.isCustom && result.isFirstVisit) {
      Alert.alert(
        item.fullModelName,
        'Did the URL open the correct tech spec page?',
        [
          {
            text: 'Yes, correct ✓',
            onPress: () => {
              markConfirmed(item.id);
              saveUrl(item.id, result.openedUrl); // auto-save so future taps skip the dialog
            },
          },
          {
            text: 'No, URL was wrong ✗',
            style: 'destructive',
            onPress: () => markWrong(item.id),
          },
        ]
      );
    }
  };

  const handleLongPress = (item: Motherboard) => {
    const hasSaved = !!savedUrls[item.id];
    const hasState = hasSaved || !!visitRecord[item.id];
    const options: { text: string; onPress?: () => void; style?: 'cancel' | 'destructive' }[] = [
      {
        text: hasSaved ? 'Edit Saved URL' : 'Enter URL manually',
        onPress: () => setEditUrlTarget(item),
      },
    ];
    if (hasState) {
      options.push({
        text: 'Reset Status',
        style: 'destructive',
        onPress: () => resetBoardState(item.id),
      });
    }
    if (item.isCustom) {
      options.push({
        text: 'Remove Custom Board',
        style: 'destructive',
        onPress: () =>
          Alert.alert('Remove Custom Board', `Remove "${item.fullModelName}"?`, [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Remove', style: 'destructive', onPress: () => removeCustomBoard(item.id) },
          ]),
      });
    }
    options.push({ text: 'Cancel', style: 'cancel' });
    Alert.alert(item.fullModelName, undefined, options);
  };

  const renderItem = ({ item }: { item: Motherboard }) => {
    const hasSaved = !!savedUrls[item.id];
    const visitStatus = visitRecord[item.id];
    return (
      <TouchableOpacity
        style={styles.row}
        onPress={() => handlePress(item)}
        onLongPress={() => handleLongPress(item)}
        activeOpacity={editMode ? 1 : 0.7}
      >
        <View style={styles.rowLeft}>
          <View style={styles.nameRow}>
            <Text style={styles.modelName} numberOfLines={2}>{item.fullModelName}</Text>
            <BoardBadges board={item} hasSaved={hasSaved} visitStatus={visitStatus} />
          </View>
          <Text style={styles.brand}>{item.brand}</Text>
        </View>

        {editMode ? (
          <TouchableOpacity
            style={styles.deleteBtn}
            onPress={() =>
              Alert.alert(
                'Reset status?',
                `Clear all marks for "${item.fullModelName}"? Saved URL and visit confirmation will be removed.`,
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Reset', style: 'destructive', onPress: () => resetBoardState(item.id) },
                ]
              )
            }
          >
            <Text style={styles.deleteBtnTxt}>Remove</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.chipsetBadge}>
            <Text style={styles.chipsetText}>{item.chipset}</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <LoadingOverlay visible={isLoading} message="Loading catalog..." />
      <LoadingOverlay visible={isResolvingUrl} message="Opening page..." />

      {/* Brand pills */}
      <View style={styles.filterSection}>
        <Text style={styles.filterLabel}>BRAND</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
          {brands.map((b) => (
            <TouchableOpacity
              key={b}
              style={[styles.pill, selectedBrand === b && styles.pillActiveDark]}
              onPress={() => setSelectedBrand(b)}
            >
              <Text style={[styles.pillTxt, selectedBrand === b && styles.pillTxtActive]}>{b}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Chipset pills */}
      <View style={[styles.filterSection, { borderBottomWidth: StyleSheet.hairlineWidth }]}>
        <Text style={styles.filterLabel}>CHIPSET</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
          {chipsets.map((c) => (
            <TouchableOpacity
              key={c}
              style={[styles.pill, selectedChipset === c && styles.pillActiveBlue]}
              onPress={() => setSelectedChipset(c)}
            >
              <Text style={[styles.pillTxt, selectedChipset === c && styles.pillTxtActive]}>{c}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Search box — AND-combined with brand/chipset pills */}
      <View style={styles.searchBox}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search (use spaces for AND, e.g. '650 wifi')"
          value={searchQuery}
          onChangeText={setSearchQuery}
          clearButtonMode="while-editing"
          autoCorrect={false}
          autoCapitalize="none"
          returnKeyType="done"
          onSubmitEditing={Keyboard.dismiss}
          blurOnSubmit
        />
      </View>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={refresh} style={styles.retryBtn}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {/* Count + controls */}
      <View style={styles.countRow}>
        <View style={styles.countLeft}>
          <Text style={styles.count}>
            {editMode ? `${displayedModels.length} labeled` : `${searchedModels.length} models`}
          </Text>
          {!editMode && version ? <Text style={styles.versionTxt}>· {version}</Text> : null}
        </View>
        <View style={styles.countRowRight}>
          {!editMode && (selectedBrand !== 'ALL' || selectedChipset !== 'ALL' || searchQuery !== '') && (
            <TouchableOpacity onPress={() => { setSelectedBrand('ALL'); setSelectedChipset('ALL'); setSearchQuery(''); }}>
              <Text style={styles.clearFilter}>Clear ×</Text>
            </TouchableOpacity>
          )}
          {(hasAnyState || editMode) && (
            <TouchableOpacity onPress={() => setEditMode((e) => !e)}>
              <Text style={[styles.editBtn, editMode && styles.editBtnActive]}>
                {editMode ? 'Done' : 'Edit Status'}
              </Text>
            </TouchableOpacity>
          )}
          {!editMode && (
            <TouchableOpacity onPress={refresh} disabled={isRefreshing}>
              <Text style={[styles.refreshBtn, isRefreshing && styles.refreshBtnActive]}>
                {isRefreshing ? '⟳' : '↻'}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {newBoardsCount > 0 && (
        <View style={styles.toastBanner}>
          <Text style={styles.toastTxt}>✨ {newBoardsCount} new board{newBoardsCount > 1 ? 's' : ''} added</Text>
        </View>
      )}

      {editMode && (
        <View style={styles.editBanner}>
          <Text style={styles.editBannerTxt}>
            Tap "Remove" to reset a board's status (clears URL + all marks)
          </Text>
          <TouchableOpacity onPress={handleClearAll} style={styles.clearAllBtn}>
            <Text style={styles.clearAllBtnTxt}>Clear All</Text>
          </TouchableOpacity>
        </View>
      )}

      <FlatList
        data={displayedModels}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
        refreshControl={<RefreshControl refreshing={false} onRefresh={refresh} />}
        ListEmptyComponent={
          !isLoading ? (
            <Text style={styles.emptyText}>
              {editMode ? 'No boards with status labels.' : 'No models found.'}
            </Text>
          ) : null
        }
      />

      <SaveUrlModal
        visible={editUrlTarget !== null}
        boardName={editUrlTarget?.fullModelName ?? ''}
        existingUrl={editUrlTarget ? savedUrls[editUrlTarget.id] : undefined}
        onSave={(url) => { if (editUrlTarget) saveUrl(editUrlTarget.id, url); }}
        onClose={() => setEditUrlTarget(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },

  filterSection: {
    backgroundColor: '#fff',
    paddingTop: 10,
    paddingBottom: 6,
    borderColor: '#E5E5EA',
  },
  filterLabel: {
    fontSize: 10, color: '#8E8E93', fontWeight: '700',
    textTransform: 'uppercase', letterSpacing: 0.8,
    paddingHorizontal: 16, marginBottom: 6,
  },
  pillRow: { paddingHorizontal: 12, gap: 6, paddingBottom: 2 },
  pill: {
    paddingHorizontal: 14, paddingVertical: 6,
    borderRadius: 20, backgroundColor: '#F2F2F7',
    borderWidth: 1, borderColor: '#E5E5EA',
  },
  pillActiveDark: { backgroundColor: '#1C1C1E', borderColor: '#1C1C1E' },
  pillActiveBlue: { backgroundColor: '#007AFF', borderColor: '#007AFF' },
  pillTxt: { fontSize: 13, color: '#3C3C43', fontWeight: '500' },
  pillTxtActive: { color: '#fff' },

  searchBox: {
    backgroundColor: '#fff',
    paddingHorizontal: 16, paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#E5E5EA',
  },
  searchInput: {
    backgroundColor: '#F2F2F7', borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 8, fontSize: 15,
  },

  countRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 8,
  },
  countRowRight: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  countLeft: { flexDirection: 'row', alignItems: 'baseline', gap: 4 },
  count: { fontSize: 12, color: '#8E8E93', fontWeight: '500' },
  versionTxt: { fontSize: 11, color: '#C7C7CC' },
  clearFilter: { fontSize: 12, color: '#007AFF', fontWeight: '500' },
  editBtn: { fontSize: 12, color: '#8E8E93', fontWeight: '500' },
  editBtnActive: { color: '#007AFF', fontWeight: '600' },
  refreshBtn: { fontSize: 18, color: '#007AFF', fontWeight: '500' },
  refreshBtnActive: { color: '#A8C7F0' },
  toastBanner: {
    marginHorizontal: 16, marginBottom: 6,
    backgroundColor: '#E8F5E9', borderRadius: 8,
    paddingVertical: 8, paddingHorizontal: 12,
  },
  toastTxt: { fontSize: 12, color: '#2E7D32', fontWeight: '600', textAlign: 'center' },

  editBanner: {
    marginHorizontal: 16, marginBottom: 4,
    backgroundColor: '#FFF9E6', borderRadius: 8, padding: 10,
    gap: 8,
  },
  editBannerTxt: { fontSize: 11, color: '#856404', textAlign: 'center' },
  clearAllBtn: {
    alignSelf: 'center',
    backgroundColor: '#FEE2E2', borderRadius: 6,
    paddingHorizontal: 14, paddingVertical: 5,
  },
  clearAllBtnTxt: { fontSize: 12, color: '#DC2626', fontWeight: '700' },

  list: { paddingHorizontal: 16, paddingBottom: 100 },
  row: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 12, paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#E5E5EA',
    gap: 12, backgroundColor: '#fff', marginBottom: StyleSheet.hairlineWidth,
  },
  rowLeft: { flex: 1 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  modelName: { fontSize: 15, fontWeight: '500', color: '#1C1C1E', flexShrink: 1 },
  brand: { fontSize: 12, color: '#8E8E93', marginTop: 2 },

  chipsetBadge: { backgroundColor: '#EFF6FF', borderRadius: 7, paddingHorizontal: 9, paddingVertical: 5 },
  chipsetText: { fontSize: 12, color: '#2563EB', fontWeight: '700' },

  deleteBtn: { backgroundColor: '#FEE2E2', borderRadius: 7, paddingHorizontal: 10, paddingVertical: 5 },
  deleteBtnTxt: { fontSize: 12, color: '#DC2626', fontWeight: '700' },

  errorBox: { margin: 16, padding: 14, backgroundColor: '#FEF2F2', borderRadius: 10, alignItems: 'center', gap: 10 },
  errorText: { color: '#DC2626', fontSize: 14, textAlign: 'center' },
  retryBtn: { backgroundColor: '#DC2626', paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '600' },
  emptyText: { textAlign: 'center', color: '#aaa', marginTop: 40, fontSize: 15 },
});
