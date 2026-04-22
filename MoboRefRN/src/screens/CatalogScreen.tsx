import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
  Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
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
  const [saveModalTarget, setSaveModalTarget] = useState<Motherboard | null>(null);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const hasSavedUrls = Object.keys(savedUrls).length > 0;

  const handleLongPress = (item: Motherboard) => {
    const hasSaved = !!savedUrls[item.id];
    const options: { text: string; onPress?: () => void; style?: 'cancel' | 'destructive' }[] = [
      {
        text: hasSaved ? 'Edit Saved URL' : 'Save Official URL',
        onPress: () => setSaveModalTarget(item),
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
          Alert.alert(
            'Remove Custom Board',
            `Remove "${item.fullModelName}" from your catalog?`,
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Remove', style: 'destructive', onPress: () => removeCustomBoard(item.id) },
            ]
          ),
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
        onPress={() => (editMode ? null : openOfficialPage(item))}
        onLongPress={() => handleLongPress(item)}
        activeOpacity={editMode ? 1 : 0.7}
      >
        <View style={styles.rowLeft}>
          <View style={styles.nameRow}>
            <Text style={styles.modelName} numberOfLines={2}>
              {item.fullModelName}
            </Text>
            {item.isCustom && (
              <View style={styles.customBadge}>
                <Text style={styles.customBadgeTxt}>Custom</Text>
              </View>
            )}
            {hasSaved && (
              <View style={styles.savedBadge}>
                <Text style={styles.savedBadgeTxt}>URL</Text>
              </View>
            )}
          </View>
          <Text style={styles.brand}>{item.brand}</Text>
        </View>

        {editMode && hasSaved ? (
          <TouchableOpacity
            style={styles.deleteBtn}
            onPress={() =>
              Alert.alert(
                'Remove saved URL',
                `Remove the saved URL for "${item.fullModelName}"?`,
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Remove', style: 'destructive', onPress: () => removeSavedUrl(item.id) },
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
      <LoadingOverlay visible={isLoading} message="Loading motherboard catalog..." />
      <LoadingOverlay visible={isResolvingUrl} message="Opening page..." />

      {/* Filter card */}
      <View style={styles.filtersCard}>
        <View style={styles.filterCol}>
          <Text style={styles.filterLabel}>BRAND</Text>
          <Picker
            selectedValue={selectedBrand}
            onValueChange={setSelectedBrand}
            style={styles.picker}
            itemStyle={styles.pickerItem}
          >
            {brands.map((b) => (
              <Picker.Item key={b} label={b} value={b} />
            ))}
          </Picker>
        </View>

        <View style={styles.filterDivider} />

        <View style={styles.filterCol}>
          <Text style={styles.filterLabel}>CHIPSET</Text>
          <Picker
            selectedValue={selectedChipset}
            onValueChange={setSelectedChipset}
            style={styles.picker}
            itemStyle={styles.pickerItem}
          >
            {chipsets.map((c) => (
              <Picker.Item key={c} label={c} value={c} />
            ))}
          </Picker>
        </View>
      </View>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={refresh} style={styles.retryBtn}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {/* Count row + edit toggle */}
      <View style={styles.countRow}>
        <Text style={styles.count}>{filteredModels.length} models</Text>
        <View style={styles.countRowRight}>
          {(selectedBrand !== 'ALL' || selectedChipset !== 'ALL') && (
            <TouchableOpacity
              onPress={() => { setSelectedBrand('ALL'); setSelectedChipset('ALL'); }}
            >
              <Text style={styles.clearFilter}>Clear filters ×</Text>
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
            Tap "Remove" to delete a saved URL. Long-press any board to save or edit its URL.
          </Text>
        </View>
      )}

      <FlatList
        data={filteredModels}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={false} onRefresh={refresh} />
        }
        ListEmptyComponent={
          !isLoading ? (
            <Text style={styles.emptyText}>No models found.</Text>
          ) : null
        }
      />

      <SaveUrlModal
        visible={saveModalTarget !== null}
        boardName={saveModalTarget?.fullModelName ?? ''}
        existingUrl={saveModalTarget ? savedUrls[saveModalTarget.id] : undefined}
        onSave={(url) => {
          if (saveModalTarget) saveUrl(saveModalTarget.id, url);
        }}
        onClose={() => setSaveModalTarget(null)}
      />
    </View>
  );
}

const PICKER_H = Platform.OS === 'ios' ? 120 : 48;
const PICKER_OFFSET = Platform.OS === 'ios' ? -28 : 0;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },

  filtersCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 4,
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  filterCol: { flex: 1, paddingTop: 10, paddingHorizontal: 4, overflow: 'hidden' },
  filterLabel: {
    fontSize: 11, color: '#8E8E93', fontWeight: '700',
    textTransform: 'uppercase', letterSpacing: 0.6, paddingHorizontal: 8,
  },
  filterDivider: { width: StyleSheet.hairlineWidth, backgroundColor: '#E5E5EA', marginVertical: 12 },
  picker: { height: PICKER_H, marginTop: PICKER_OFFSET },
  pickerItem: { fontSize: 14, color: '#1C1C1E' },

  countRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 6,
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
  editBannerTxt: { fontSize: 12, color: '#856404', textAlign: 'center' },

  list: { paddingHorizontal: 16, paddingBottom: 24 },
  row: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 12, paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#E5E5EA',
    gap: 12, backgroundColor: '#fff',
    marginBottom: StyleSheet.hairlineWidth,
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

  deleteBtn: {
    backgroundColor: '#FEE2E2', borderRadius: 7,
    paddingHorizontal: 10, paddingVertical: 5,
  },
  deleteBtnTxt: { fontSize: 12, color: '#DC2626', fontWeight: '700' },

  errorBox: { margin: 16, padding: 14, backgroundColor: '#FEF2F2', borderRadius: 10, alignItems: 'center', gap: 10 },
  errorText: { color: '#DC2626', fontSize: 14, textAlign: 'center' },
  retryBtn: { backgroundColor: '#DC2626', paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '600' },

  emptyText: { textAlign: 'center', color: '#aaa', marginTop: 40, fontSize: 15 },
});
