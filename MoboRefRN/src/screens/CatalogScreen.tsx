import React, { useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
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
      <LoadingOverlay
        visible={isLoading}
        message="Loading motherboard catalog..."
      />
      <LoadingOverlay
        visible={isResolvingUrl}
        message="Finding official page..."
      />

      {/* Brand filter */}
      <View style={styles.pickerWrapper}>
        <Text style={styles.pickerLabel}>Brand</Text>
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

      {/* Chipset filter */}
      <View style={styles.pickerWrapper}>
        <Text style={styles.pickerLabel}>Chipset</Text>
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

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={refresh} style={styles.retryBtn}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      <Text style={styles.count}>{filteredModels.length} models</Text>

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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  pickerWrapper: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#ddd',
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  pickerLabel: {
    fontSize: 12,
    color: '#888',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  picker: {
    height: Platform.OS === 'ios' ? 120 : 48,
    marginTop: Platform.OS === 'ios' ? -30 : 0,
  },
  pickerItem: {
    fontSize: 15,
  },
  count: {
    fontSize: 12,
    color: '#999',
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#eee',
    gap: 12,
  },
  rowLeft: {
    flex: 1,
  },
  modelName: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111',
  },
  brand: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  chipsetBadge: {
    backgroundColor: '#EFF6FF',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  chipsetText: {
    fontSize: 12,
    color: '#2563EB',
    fontWeight: '600',
  },
  errorBox: {
    margin: 16,
    padding: 14,
    backgroundColor: '#FEF2F2',
    borderRadius: 10,
    alignItems: 'center',
    gap: 10,
  },
  errorText: {
    color: '#DC2626',
    fontSize: 14,
    textAlign: 'center',
  },
  retryBtn: {
    backgroundColor: '#DC2626',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryText: {
    color: '#fff',
    fontWeight: '600',
  },
  emptyText: {
    textAlign: 'center',
    color: '#aaa',
    marginTop: 40,
    fontSize: 15,
  },
});
