import React, { useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useCatalog } from '../hooks/useCatalog';
import { LoadingOverlay } from '../components/LoadingOverlay';
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
  } = useCatalog();

  useEffect(() => {
    loadData();
  }, [loadData]);

  const renderItem = ({ item }: { item: Motherboard }) => (
    <TouchableOpacity
      style={styles.row}
      onPress={() => openOfficialPage(item)}
      activeOpacity={0.7}
    >
      <View style={styles.rowLeft}>
        <Text style={styles.modelName} numberOfLines={2}>
          {item.fullModelName}
        </Text>
        <Text style={styles.brand}>{item.brand}</Text>
      </View>
      <View style={styles.chipsetBadge}>
        <Text style={styles.chipsetText}>{item.chipset}</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <LoadingOverlay visible={isLoading} message="Loading motherboard catalog..." />
      <LoadingOverlay visible={isResolvingUrl} message="Finding official page..." />

      {/* Filter card — two pickers side by side */}
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

      {/* Count + active filter summary */}
      <View style={styles.countRow}>
        <Text style={styles.count}>{filteredModels.length} models</Text>
        {(selectedBrand !== 'ALL' || selectedChipset !== 'ALL') && (
          <TouchableOpacity
            onPress={() => { setSelectedBrand('ALL'); setSelectedChipset('ALL'); }}
          >
            <Text style={styles.clearFilter}>Clear filters ×</Text>
          </TouchableOpacity>
        )}
      </View>

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
  filterCol: {
    flex: 1,
    paddingTop: 10,
    paddingHorizontal: 4,
    paddingBottom: 0,
    overflow: 'hidden',
  },
  filterLabel: {
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    paddingHorizontal: 8,
  },
  filterDivider: {
    width: StyleSheet.hairlineWidth,
    backgroundColor: '#E5E5EA',
    marginVertical: 12,
  },
  picker: {
    height: PICKER_H,
    marginTop: PICKER_OFFSET,
  },
  pickerItem: {
    fontSize: 14,
    color: '#1C1C1E',
  },

  countRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 6,
  },
  count: { fontSize: 12, color: '#8E8E93', fontWeight: '500' },
  clearFilter: { fontSize: 12, color: '#007AFF', fontWeight: '500' },

  list: { paddingHorizontal: 16, paddingBottom: 24 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#E5E5EA',
    gap: 12,
    backgroundColor: '#fff',
    marginBottom: StyleSheet.hairlineWidth,
  },
  rowLeft: { flex: 1 },
  modelName: { fontSize: 15, fontWeight: '500', color: '#1C1C1E' },
  brand: { fontSize: 12, color: '#8E8E93', marginTop: 2 },
  chipsetBadge: {
    backgroundColor: '#EFF6FF',
    borderRadius: 7,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  chipsetText: { fontSize: 12, color: '#2563EB', fontWeight: '700' },

  errorBox: {
    margin: 16, padding: 14, backgroundColor: '#FEF2F2',
    borderRadius: 10, alignItems: 'center', gap: 10,
  },
  errorText: { color: '#DC2626', fontSize: 14, textAlign: 'center' },
  retryBtn: { backgroundColor: '#DC2626', paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '600' },

  emptyText: { textAlign: 'center', color: '#aaa', marginTop: 40, fontSize: 15 },
});
