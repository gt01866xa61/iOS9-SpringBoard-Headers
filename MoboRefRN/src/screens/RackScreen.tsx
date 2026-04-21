import React, { useState, useCallback, useLayoutEffect } from 'react';
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
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useRacks } from '../hooks/useRacks';
import { useCatalog } from '../hooks/useCatalog';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { Rack, RackSlot } from '../models/Rack';
import { Motherboard } from '../models/Motherboard';

const COLS = 3;
const GAP = 8;
const PADDING = 12;
const ROW_DEL_W = 36;
const SLOT_SIZE = (Dimensions.get('window').width - PADDING * 2 - GAP * COLS - ROW_DEL_W) / COLS;

function GridSlot({
  slot,
  isEditing,
  isSelected,
  onAssign,
  onClear,
  onOpenUrl,
  onTap,
}: {
  slot: RackSlot;
  isEditing: boolean;
  isSelected: boolean;
  onAssign: (s: RackSlot) => void;
  onClear: (s: RackSlot) => void;
  onOpenUrl: (s: RackSlot) => void;
  onTap: (s: RackSlot) => void;
}) {
  const board = slot.motherboard;
  const selectedStyle = isSelected ? styles.slotSelected : null;

  if (isEditing) {
    return (
      <TouchableOpacity
        style={[styles.slot, { width: SLOT_SIZE, height: SLOT_SIZE }, selectedStyle]}
        activeOpacity={0.7}
        onPress={() => onTap(slot)}
      >
        <Text style={styles.slotNum}>{slot.position + 1}</Text>
        {board ? (
          <>
            <Text style={styles.slotModel} numberOfLines={3}>{board.fullModelName}</Text>
            <Text style={styles.slotChipset}>{board.chipset}</Text>
            {isSelected && (
              <View style={styles.selectedBadge}>
                <Text style={styles.selectedBadgeTxt}>✓</Text>
              </View>
            )}
          </>
        ) : (
          <View style={styles.emptySlotHint}>
            <Text style={styles.emptySlotTxt}>{isSelected ? '✓' : '—'}</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  }

  return (
    <View style={[styles.slot, { width: SLOT_SIZE, height: SLOT_SIZE }]}>
      <Text style={styles.slotNum}>{slot.position + 1}</Text>
      {board ? (
        <>
          <Text style={styles.slotModel} numberOfLines={3}>{board.fullModelName}</Text>
          <Text style={styles.slotChipset}>{board.chipset}</Text>
          <View style={styles.slotBtns}>
            <TouchableOpacity style={styles.btnPage} onPress={() => onOpenUrl(slot)}>
              <Text style={styles.btnPageTxt}>🔗</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.btnRemove} onPress={() => onClear(slot)}>
              <Text style={styles.btnRemoveTxt}>✕</Text>
            </TouchableOpacity>
          </View>
        </>
      ) : (
        <TouchableOpacity style={styles.assignBtn} onPress={() => onAssign(slot)}>
          <Text style={styles.assignTxt}>+</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

export function RackScreen() {
  const navigation = useNavigation();
  const { racks, addRack, removeRack, assignMotherboard, clearSlot, expandRack, removeRow, swapSlots } = useRacks();
  const { filteredModels, isResolvingUrl, openOfficialPage } = useCatalog();

  const [selectedRackId, setSelectedRackId] = useState<string | null>(null);
  const [addRackVisible, setAddRackVisible] = useState(false);
  const [rackName, setRackName] = useState('');
  const [assignModalVisible, setAssignModalVisible] = useState(false);
  const [pendingSlot, setPendingSlot] = useState<{ rackId: string; slot: RackSlot } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [isEditing, setIsEditing] = useState(false);
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);

  const selectedRack = racks.find((r) => r.id === selectedRackId) ?? racks[0] ?? null;

  const searchedModels = filteredModels.filter((b) =>
    searchQuery.trim() === '' ||
    b.fullModelName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    b.chipset.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () =>
        selectedRack ? (
          <TouchableOpacity
            onPress={() => {
              setIsEditing((v) => !v);
              setSelectedSlotId(null);
            }}
            style={styles.editBtn}
          >
            <Text style={styles.editBtnTxt}>{isEditing ? 'Done' : 'Edit'}</Text>
          </TouchableOpacity>
        ) : null,
    });
  }, [navigation, isEditing, selectedRack]);

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
    setSearchQuery('');
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
      if (slot.motherboard) await openOfficialPage(slot.motherboard);
    },
    [openOfficialPage]
  );

  const handleSlotTap = useCallback(
    (slot: RackSlot) => {
      if (!selectedRack) return;
      if (!selectedSlotId) {
        setSelectedSlotId(slot.id);
        return;
      }
      if (selectedSlotId === slot.id) {
        setSelectedSlotId(null);
        return;
      }
      swapSlots(selectedRack.id, selectedSlotId, slot.id);
      setSelectedSlotId(null);
    },
    [selectedRack, selectedSlotId, swapSlots]
  );

  const handleRemoveRow = useCallback(
    (rackId: string, row: number) => {
      Alert.alert('Delete Row', 'Delete this row?', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: () => removeRow(rackId, row) },
      ]);
    },
    [removeRow]
  );

  const slots = selectedRack?.slots ?? [];

  return (
    <View style={styles.container}>
      <LoadingOverlay visible={isResolvingUrl} message="Finding official page..." />

      {/* Rack selector strip */}
      <ScrollView
        horizontal
        style={styles.strip}
        contentContainerStyle={styles.stripContent}
        showsHorizontalScrollIndicator={false}
      >
        {racks.map((r) => (
          <TouchableOpacity
            key={r.id}
            style={[styles.tab, selectedRack?.id === r.id && styles.tabActive]}
            onPress={() => setSelectedRackId(r.id)}
            onLongPress={() => handleDeleteRack(r)}
          >
            <Text style={[styles.tabTxt, selectedRack?.id === r.id && styles.tabTxtActive]}>
              {r.name}
            </Text>
          </TouchableOpacity>
        ))}
        <TouchableOpacity style={styles.newBtn} onPress={() => setAddRackVisible(true)}>
          <Text style={styles.newBtnTxt}>+ New Rack</Text>
        </TouchableOpacity>
      </ScrollView>

      {isEditing && (
        <View style={styles.editHint}>
          <Text style={styles.editHintTxt}>
            {selectedSlotId
              ? 'Now tap another slot to swap'
              : 'Tap a slot to select it, then tap another to swap'}
          </Text>
        </View>
      )}

      {/* Grid */}
      {selectedRack ? (
        <ScrollView contentContainerStyle={styles.grid}>
          {Array.from({ length: Math.ceil(slots.length / COLS) }, (_, row) => (
            <View key={row} style={styles.gridRow}>
              {slots.slice(row * COLS, row * COLS + COLS).map((slot) => (
                <GridSlot
                  key={slot.id}
                  slot={slot}
                  isEditing={isEditing}
                  isSelected={slot.id === selectedSlotId}
                  onAssign={(s) => handleAssign(selectedRack.id, s)}
                  onClear={(s) => clearSlot(selectedRack.id, s.id)}
                  onOpenUrl={handleOpenUrl}
                  onTap={handleSlotTap}
                />
              ))}
              {isEditing && (
                <TouchableOpacity
                  style={styles.rowDelBtn}
                  onPress={() => handleRemoveRow(selectedRack.id, row)}
                >
                  <Text style={styles.rowDelTxt}>−</Text>
                </TouchableOpacity>
              )}
            </View>
          ))}
          <TouchableOpacity
            style={styles.addRowBtn}
            onPress={() => expandRack(selectedRack.id)}
          >
            <Text style={styles.addRowTxt}>+ Add Row</Text>
          </TouchableOpacity>
        </ScrollView>
      ) : (
        <View style={styles.empty}>
          <Text style={styles.emptyTxt}>No racks yet.</Text>
          <Text style={styles.emptyHint}>Tap "+ New Rack" to create one.</Text>
        </View>
      )}

      {/* Add rack modal */}
      <Modal visible={addRackVisible} transparent animationType="slide">
        <KeyboardAvoidingView
          style={styles.modalBg}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <TouchableOpacity style={StyleSheet.absoluteFill} onPress={() => setAddRackVisible(false)} />
          <View style={styles.modalBox}>
            <Text style={styles.modalTitle}>New Rack</Text>
            <TextInput
              style={styles.input}
              placeholder="Rack name (e.g. Lab Shelf A)"
              value={rackName}
              onChangeText={setRackName}
              autoFocus
              returnKeyType="done"
              onSubmitEditing={handleAddRack}
            />
            <View style={styles.modalRow}>
              <TouchableOpacity
                onPress={() => setAddRackVisible(false)}
                style={[styles.modalBtn, styles.modalBtnCancel]}
              >
                <Text style={styles.cancelTxt}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={handleAddRack} style={[styles.modalBtn, styles.modalBtnOk]}>
                <Text style={styles.okTxt}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Assign modal */}
      <Modal visible={assignModalVisible} animationType="slide">
        <SafeAreaView style={styles.assignModal} edges={['top', 'left', 'right']}>
          <View style={styles.assignHeader}>
            <Text style={styles.assignTitle}>Select Motherboard</Text>
            <TouchableOpacity onPress={() => setAssignModalVisible(false)}>
              <Text style={styles.cancelLink}>Cancel</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.searchBox}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search model or chipset..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              clearButtonMode="while-editing"
              autoCorrect={false}
              autoFocus={false}
            />
          </View>
          <FlatList
            data={searchedModels}
            keyExtractor={(item) => item.id}
            keyboardShouldPersistTaps="handled"
            renderItem={({ item }) => (
              <TouchableOpacity style={styles.assignRow} onPress={() => handleSelectBoard(item)}>
                <Text style={styles.assignModel}>{item.fullModelName}</Text>
                <Text style={styles.assignChipset}>{item.chipset}</Text>
              </TouchableOpacity>
            )}
            contentContainerStyle={{ paddingBottom: 24 }}
          />
        </SafeAreaView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  strip: { maxHeight: 52, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#ddd' },
  stripContent: { paddingHorizontal: 12, paddingVertical: 8, gap: 8, alignItems: 'center' },
  tab: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, backgroundColor: '#f0f0f0' },
  tabActive: { backgroundColor: '#007AFF' },
  tabTxt: { fontSize: 14, color: '#333', fontWeight: '500' },
  tabTxtActive: { color: '#fff' },
  newBtn: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: '#007AFF' },
  newBtnTxt: { color: '#007AFF', fontSize: 14, fontWeight: '500' },

  editBtn: { marginRight: 12 },
  editBtnTxt: { color: '#007AFF', fontSize: 16, fontWeight: '600' },

  editHint: {
    backgroundColor: '#FFF9E6',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#F0C040',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  editHintTxt: { fontSize: 13, color: '#7A5F00', textAlign: 'center' },

  grid: { padding: PADDING, gap: GAP },
  gridRow: { flexDirection: 'row', gap: GAP },

  slot: {
    backgroundColor: '#f8f9ff',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#e0e4f0',
    padding: 8,
    justifyContent: 'space-between',
  },
  slotSelected: {
    borderColor: '#007AFF',
    borderWidth: 2,
    backgroundColor: '#EEF5FF',
  },
  slotNum: { fontSize: 10, color: '#999', fontWeight: '700', textTransform: 'uppercase' },
  slotModel: { fontSize: 11, fontWeight: '600', color: '#111', flex: 1, marginTop: 2 },
  slotChipset: {
    fontSize: 10, color: '#2563EB', fontWeight: '600',
    backgroundColor: '#EFF6FF', alignSelf: 'flex-start',
    paddingHorizontal: 5, paddingVertical: 2, borderRadius: 4, marginTop: 2,
  },
  slotBtns: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  btnPage: { backgroundColor: '#007AFF', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 },
  btnPageTxt: { fontSize: 12 },
  btnRemove: { backgroundColor: '#FEE2E2', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 },
  btnRemoveTxt: { fontSize: 12, color: '#DC2626' },

  assignBtn: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  assignTxt: { fontSize: 28, color: '#007AFF', fontWeight: '300' },

  emptySlotHint: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptySlotTxt: { fontSize: 20, color: '#ccc' },

  selectedBadge: {
    position: 'absolute', top: 4, right: 4,
    backgroundColor: '#007AFF', borderRadius: 10,
    width: 18, height: 18, justifyContent: 'center', alignItems: 'center',
  },
  selectedBadgeTxt: { color: '#fff', fontSize: 11, fontWeight: '700' },

  rowDelBtn: {
    width: ROW_DEL_W,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'stretch',
  },
  rowDelTxt: { fontSize: 22, color: '#DC2626', fontWeight: '300' },
  addRowBtn: {
    marginTop: 4,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
    alignItems: 'center',
  },
  addRowTxt: { color: '#007AFF', fontSize: 14, fontWeight: '600' },

  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 8 },
  emptyTxt: { fontSize: 17, color: '#555', fontWeight: '500' },
  emptyHint: { fontSize: 14, color: '#aaa' },

  modalBg: { flex: 1, justifyContent: 'flex-end' },
  modalBox: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 24, gap: 16 },
  modalTitle: { fontSize: 18, fontWeight: '700' },
  input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 10, padding: 12, fontSize: 15 },
  modalRow: { flexDirection: 'row', gap: 12 },
  modalBtn: { flex: 1, paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  modalBtnCancel: { backgroundColor: '#f0f0f0' },
  modalBtnOk: { backgroundColor: '#007AFF' },
  cancelTxt: { color: '#333', fontWeight: '600' },
  okTxt: { color: '#fff', fontWeight: '600' },

  assignModal: { flex: 1, backgroundColor: '#fff' },
  assignHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#ddd' },
  assignTitle: { fontSize: 18, fontWeight: '700' },
  cancelLink: { color: '#007AFF', fontSize: 16 },
  searchBox: { paddingHorizontal: 16, paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#eee' },
  searchInput: { backgroundColor: '#f2f2f7', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, fontSize: 15 },
  assignRow: { paddingHorizontal: 16, paddingVertical: 13, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#eee' },
  assignModel: { fontSize: 15, fontWeight: '500', color: '#111' },
  assignChipset: { fontSize: 13, color: '#888', marginTop: 2 },
});
