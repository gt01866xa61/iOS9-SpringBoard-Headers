import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  TextInput,
  ScrollView,
} from 'react-native';
import { useRacks } from '../hooks/useRacks';
import { useCatalog } from '../hooks/useCatalog';
import { SlotItem } from '../components/SlotItem';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { Rack, RackSlot } from '../models/Rack';
import { Motherboard } from '../models/Motherboard';

export function RackScreen() {
  const { racks, addRack, removeRack, assignMotherboard, clearSlot } = useRacks();
  const {
    filteredModels,
    isLoading,
    isResolvingUrl,
    loadData,
    openOfficialPage,
    brands,
    chipsets,
    selectedBrand,
    selectedChipset,
    setSelectedBrand,
    setSelectedChipset,
  } = useCatalog();

  const [selectedRackId, setSelectedRackId] = useState<string | null>(null);
  const [addRackVisible, setAddRackVisible] = useState(false);
  const [rackName, setRackName] = useState('');
  const [assignModalVisible, setAssignModalVisible] = useState(false);
  const [pendingSlot, setPendingSlot] = useState<{ rackId: string; slot: RackSlot } | null>(null);

  const selectedRack = racks.find((r) => r.id === selectedRackId) ?? racks[0] ?? null;

  const handleAddRack = () => {
    const name = rackName.trim();
    if (!name) return;
    addRack(name);
    setRackName('');
    setAddRackVisible(false);
  };

  const handleDeleteRack = (rack: Rack) => {
    Alert.alert('Delete Rack', `Delete "${rack.name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => {
          if (selectedRackId === rack.id) setSelectedRackId(null);
          removeRack(rack.id);
        },
      },
    ]);
  };

  const handleAssign = (rackId: string, slot: RackSlot) => {
    setPendingSlot({ rackId, slot });
    loadData();
    setAssignModalVisible(true);
  };

  const handleSelectBoard = (board: Motherboard) => {
    if (!pendingSlot) return;
    assignMotherboard(pendingSlot.rackId, pendingSlot.slot.id, board);
    setAssignModalVisible(false);
    setPendingSlot(null);
  };

  const handleOpenUrl = useCallback(
    async (slot: RackSlot) => {
      if (slot.motherboard) {
        await openOfficialPage(slot.motherboard);
      }
    },
    [openOfficialPage]
  );

  return (
    <View style={styles.container}>
      <LoadingOverlay visible={isResolvingUrl} message="Finding official page..." />

      {/* Rack selector strip */}
      <ScrollView
        horizontal
        style={styles.rackStrip}
        contentContainerStyle={styles.rackStripContent}
        showsHorizontalScrollIndicator={false}
      >
        {racks.map((r) => (
          <TouchableOpacity
            key={r.id}
            style={[
              styles.rackTab,
              selectedRack?.id === r.id && styles.rackTabActive,
            ]}
            onPress={() => setSelectedRackId(r.id)}
            onLongPress={() => handleDeleteRack(r)}
          >
            <Text
              style={[
                styles.rackTabText,
                selectedRack?.id === r.id && styles.rackTabTextActive,
              ]}
            >
              {r.name}
            </Text>
          </TouchableOpacity>
        ))}
        <TouchableOpacity
          style={styles.addRackBtn}
          onPress={() => setAddRackVisible(true)}
        >
          <Text style={styles.addRackText}>+ New Rack</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Slots */}
      {selectedRack ? (
        <FlatList
          data={selectedRack.slots}
          keyExtractor={(s) => s.id}
          renderItem={({ item }) => (
            <SlotItem
              slot={item}
              onAssign={(s) => handleAssign(selectedRack.id, s)}
              onClear={(s) => clearSlot(selectedRack.id, s.id)}
              onOpenUrl={handleOpenUrl}
            />
          )}
          contentContainerStyle={styles.slotList}
        />
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No racks yet.</Text>
          <Text style={styles.emptyHint}>Tap "+ New Rack" to create one.</Text>
        </View>
      )}

      {/* Add rack modal */}
      <Modal visible={addRackVisible} transparent animationType="slide">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalBox}>
            <Text style={styles.modalTitle}>New Rack</Text>
            <TextInput
              style={styles.input}
              placeholder="Rack name (e.g. Lab Shelf A)"
              value={rackName}
              onChangeText={setRackName}
              autoFocus
              onSubmitEditing={handleAddRack}
            />
            <View style={styles.modalActions}>
              <TouchableOpacity
                onPress={() => setAddRackVisible(false)}
                style={[styles.modalBtn, styles.modalBtnCancel]}
              >
                <Text style={styles.modalBtnCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={handleAddRack}
                style={[styles.modalBtn, styles.modalBtnConfirm]}
              >
                <Text style={styles.modalBtnConfirmText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Assign board modal */}
      <Modal visible={assignModalVisible} animationType="slide">
        <View style={styles.assignModal}>
          <View style={styles.assignHeader}>
            <Text style={styles.assignTitle}>Select Motherboard</Text>
            <TouchableOpacity
              onPress={() => setAssignModalVisible(false)}
              style={styles.closeBtn}
            >
              <Text style={styles.closeBtnText}>Cancel</Text>
            </TouchableOpacity>
          </View>
          <LoadingOverlay visible={isLoading} message="Loading catalog..." />
          <FlatList
            data={filteredModels}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.assignRow}
                onPress={() => handleSelectBoard(item)}
              >
                <Text style={styles.assignModel}>{item.fullModelName}</Text>
                <Text style={styles.assignChipset}>{item.chipset}</Text>
              </TouchableOpacity>
            )}
            contentContainerStyle={{ paddingBottom: 24 }}
          />
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  rackStrip: {
    maxHeight: 52,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#ddd',
  },
  rackStripContent: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  rackTab: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
  },
  rackTabActive: { backgroundColor: '#007AFF' },
  rackTabText: { fontSize: 14, color: '#333', fontWeight: '500' },
  rackTabTextActive: { color: '#fff' },
  addRackBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  addRackText: { color: '#007AFF', fontSize: 14, fontWeight: '500' },
  slotList: { padding: 16 },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 8 },
  emptyText: { fontSize: 17, color: '#555', fontWeight: '500' },
  emptyHint: { fontSize: 14, color: '#aaa' },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modalBox: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 24,
    gap: 16,
  },
  modalTitle: { fontSize: 18, fontWeight: '700', color: '#111' },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
  },
  modalActions: { flexDirection: 'row', gap: 12 },
  modalBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  modalBtnCancel: { backgroundColor: '#f0f0f0' },
  modalBtnConfirm: { backgroundColor: '#007AFF' },
  modalBtnCancelText: { color: '#333', fontWeight: '600' },
  modalBtnConfirmText: { color: '#fff', fontWeight: '600' },
  assignModal: { flex: 1, backgroundColor: '#fff' },
  assignHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#ddd',
  },
  assignTitle: { fontSize: 18, fontWeight: '700' },
  closeBtn: { padding: 4 },
  closeBtnText: { color: '#007AFF', fontSize: 16 },
  assignRow: {
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#eee',
  },
  assignModel: { fontSize: 15, fontWeight: '500', color: '#111' },
  assignChipset: { fontSize: 13, color: '#888', marginTop: 2 },
});
