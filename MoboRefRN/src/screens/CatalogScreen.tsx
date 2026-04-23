import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  ScrollView,
  Animated,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { useCatalog } from '../hooks/useCatalog';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { SaveUrlModal } from '../components/SaveUrlModal';
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
    error,
    loadData,
    refresh,
    openOfficialPage,
    setSelectedBrand,
    setSelectedChipset,
    removeCustomBoard,
    savedUrls,
    saveUrl,
    removeSavedUrl,
  } = useCatalog();

  const [editMode, setEditMode] = useState(false);
  // Clipboard save banner (appears after closing browser)
  const [clipTarget, setClipTarget] = useState<Motherboard | null>(null);
  const [clipSuccess, setClipSuccess] = useState(false);
  // Long-press manual URL edit modal
  const [editUrlTarget, setEditUrlTarget] = useState<Motherboard | null>(null);

  useEffect(() => { loadData(); }, [loadData]);

  const hasSavedUrls = Object.keys(savedUrls).length > 0;

  const handlePress = async (item: Motherboard) => {
    if (editMode) return;
    const shouldPrompt = await openOfficialPage(item);
    if (shouldPrompt) {
      setClipTarget(item);
      setClipSuccess(false);
    }
  };

  const handleClipSave = async () => {
    if (!clipTarget) return;
    const text = (await Clipboard.getStringAsync()).trim();
    if (text.startsWith('http')) {
      saveUrl(clipTarget.id, text);
      setClipSuccess(true);
      setTimeout(() => { setClipTarget(null); setClipSuccess(false); }, 1500);
    } else {
      Alert.alert('No URL found', 'Copy the page URL from the address bar first, then tap Save.');
    }
  };

  const handleLongPress = (item: Motherboard) => {
    const hasSaved = !!savedUrls[item.id];
    const options: { text: string; onPress?: () => void; style?: 'cancel' | 'destructive' }[] = [
      {
        text: hasSaved ? 'Edit Saved URL' : 'Enter URL manually',
        onPress: () => setEditUrlTarget(item),
      },
    ];
    if (hasSaved) {
      options.push({
        text: 'Remove Saved URL',
        style: 'destructive',
        onPress: () => removeSavedUrl(item.id),
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
            {item.isCustom && (
              <View style={styles.customBadge}><Text style={styles.customBadgeTxt}>Custom</Text></View>
            )}
            {hasSaved && (
              <View style={styles.savedBadge}><Text style={styles.savedBadgeTxt}>URL</Text></View>
            )}
          </View>
          <Text style={styles.brand}>{item.brand}</Text>
        </View>

        {editMode && hasSaved ? (
          <TouchableOpacity
            style={styles.deleteBtn}
            onPress={() =>
              Alert.alert('Remove saved URL', `Remove saved URL for "${item.fullModelName}"?`, [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Remove', style: 'destructive', onPress: () => removeSavedUrl(item.id) },
              ])
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
        <Text style={styles.count}>{filteredModels.length} models</Text>
        <View style={styles.countRowRight}>
          {(selectedBrand !== 'ALL' || selectedChipset !== 'ALL') && (
            <TouchableOpacity onPress={() => { setSelectedBrand('ALL'); setSelectedChipset('ALL'); }}>
              <Text style={styles.clearFilter}>Clear ×</Text>
            </TouchableOpacity>
          )}
          {hasSavedUrls && (
            <TouchableOpacity onPress={() => setEditMode((e) => !e)}>
              <Text style={[styles.editBtn, editMode && styles.editBtnActive]}>
                {editMode ? 'Done' : 'Edit URLs'}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {editMode && (
        <View style={styles.editBanner}>
          <Text style={styles.editBannerTxt}>
            Tap "Remove" to delete · Long-press any board to edit URL manually
          </Text>
        </View>
      )}

      <FlatList
        data={filteredModels}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={false} onRefresh={refresh} />}
        ListEmptyComponent={!isLoading ? <Text style={styles.emptyText}>No models found.</Text> : null}
      />

      {/* Clipboard save banner — appears after browser closes */}
      {clipTarget && (
        <View style={styles.clipBanner}>
          <View style={styles.clipBannerLeft}>
            <Text style={styles.clipBannerTitle} numberOfLines={1}>{clipTarget.fullModelName}</Text>
            <Text style={styles.clipBannerHint}>Copy the URL from the address bar, then tap Save</Text>
          </View>
          <View style={styles.clipBannerBtns}>
            <TouchableOpacity
              style={[styles.clipSaveBtn, clipSuccess && styles.clipSaveBtnSuccess]}
              onPress={handleClipSave}
            >
              <Text style={styles.clipSaveBtnTxt}>{clipSuccess ? '✓ Saved' : '📋 Save'}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setClipTarget(null)}>
              <Text style={styles.clipSkipTxt}>Skip</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Manual URL editor (long-press only) */}
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

  countRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 8,
  },
  countRowRight: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  count: { fontSize: 12, color: '#8E8E93', fontWeight: '500' },
  clearFilter: { fontSize: 12, color: '#007AFF', fontWeight: '500' },
  editBtn: { fontSize: 12, color: '#8E8E93', fontWeight: '500' },
  editBtnActive: { color: '#007AFF', fontWeight: '600' },

  editBanner: {
    marginHorizontal: 16, marginBottom: 4,
    backgroundColor: '#FFF9E6', borderRadius: 8, padding: 10,
  },
  editBannerTxt: { fontSize: 11, color: '#856404', textAlign: 'center' },

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

  customBadge: { backgroundColor: '#FFF3CD', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  customBadgeTxt: { fontSize: 10, color: '#856404', fontWeight: '700' },
  savedBadge: { backgroundColor: '#E8F5E9', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  savedBadgeTxt: { fontSize: 10, color: '#2E7D32', fontWeight: '700' },

  chipsetBadge: { backgroundColor: '#EFF6FF', borderRadius: 7, paddingHorizontal: 9, paddingVertical: 5 },
  chipsetText: { fontSize: 12, color: '#2563EB', fontWeight: '700' },

  deleteBtn: { backgroundColor: '#FEE2E2', borderRadius: 7, paddingHorizontal: 10, paddingVertical: 5 },
  deleteBtnTxt: { fontSize: 12, color: '#DC2626', fontWeight: '700' },

  errorBox: { margin: 16, padding: 14, backgroundColor: '#FEF2F2', borderRadius: 10, alignItems: 'center', gap: 10 },
  errorText: { color: '#DC2626', fontSize: 14, textAlign: 'center' },
  retryBtn: { backgroundColor: '#DC2626', paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '600' },
  emptyText: { textAlign: 'center', color: '#aaa', marginTop: 40, fontSize: 15 },

  // Clipboard save banner
  clipBanner: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    backgroundColor: '#1C1C1E',
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 14,
    paddingBottom: 28, gap: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2, shadowRadius: 8, elevation: 10,
  },
  clipBannerLeft: { flex: 1 },
  clipBannerTitle: { fontSize: 13, fontWeight: '600', color: '#fff' },
  clipBannerHint: { fontSize: 11, color: '#8E8E93', marginTop: 2 },
  clipBannerBtns: { alignItems: 'center', gap: 6 },
  clipSaveBtn: {
    backgroundColor: '#30D158', borderRadius: 10,
    paddingHorizontal: 16, paddingVertical: 8,
  },
  clipSaveBtnSuccess: { backgroundColor: '#34C759' },
  clipSaveBtnTxt: { color: '#fff', fontSize: 14, fontWeight: '700' },
  clipSkipTxt: { fontSize: 12, color: '#8E8E93' },
});
