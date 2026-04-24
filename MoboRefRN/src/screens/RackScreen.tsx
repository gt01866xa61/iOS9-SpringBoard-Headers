import React, { useState, useCallback, useLayoutEffect, useRef } from 'react';
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
  Keyboard,
  Platform,
  Animated,
  PanResponder,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useRacks } from '../hooks/useRacks';
import { useCatalog } from '../hooks/useCatalog';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { AddCustomBoardModal } from '../components/AddCustomBoardModal';
import { SaveUrlModal } from '../components/SaveUrlModal';
import { Rack, RackSlot } from '../models/Rack';
import { Motherboard } from '../models/Motherboard';

const COLS = 3;
const GAP = 8;
const PADDING = 12;
const ROW_DEL_W = 36;
const WIN_W = Dimensions.get('window').width;

function slotSize(isEditing: boolean) {
  return (WIN_W - PADDING * 2 - GAP * COLS - (isEditing ? ROW_DEL_W : 0)) / COLS;
}

function GridSlot({
  slot,
  size,
  isEditing,
  isSelected,
  hasSavedUrl,
  onAssign,
  onClear,
  onOpenUrl,
  onTap,
}: {
  slot: RackSlot;
  size: number;
  isEditing: boolean;
  isSelected: boolean;
  hasSavedUrl: boolean;
  onAssign: (s: RackSlot) => void;
  onClear: (s: RackSlot) => void;
  onOpenUrl: (s: RackSlot) => void;
  onTap: (s: RackSlot) => void;
}) {
  const board = slot.motherboard;

  if (isEditing) {
    return (
      <View style={[styles.slot, { width: size, height: size }, isSelected && styles.slotSelected]}>
        <TouchableOpacity
          style={styles.slotTapArea}
          activeOpacity={0.7}
          onPress={() => onTap(slot)}
        >
          <Text style={styles.slotNum}>{slot.position + 1}</Text>
          {board ? (
            <>
              <Text style={styles.slotModel} numberOfLines={3}>{board.fullModelName}</Text>
              <Text style={styles.slotChipset}>{board.chipset}</Text>
            </>
          ) : (
            <View style={styles.emptySlotHint}>
              <Text style={styles.emptySlotTxt}>{isSelected ? '✓' : '—'}</Text>
            </View>
          )}
        </TouchableOpacity>
        {isSelected && (
          <View style={styles.selectedBadge}>
            <Text style={styles.selectedBadgeTxt}>✓</Text>
          </View>
        )}
        {board && (
          <TouchableOpacity style={styles.slotDeleteBadge} onPress={() => onClear(slot)}>
            <Text style={styles.slotDeleteBadgeTxt}>×</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  return (
    <View style={[styles.slot, { width: size, height: size }]}>
      <Text style={styles.slotNum}>{slot.position + 1}</Text>
      {board ? (
        <>
          <Text style={styles.slotModel} numberOfLines={3}>{board.fullModelName}</Text>
          <View style={styles.slotChipsetRow}>
            <Text style={styles.slotChipset}>{board.chipset}</Text>
            {hasSavedUrl && (
              <View style={styles.slotUrlBadge}><Text style={styles.slotUrlBadgeTxt}>URL</Text></View>
            )}
          </View>
          <View style={styles.slotBtns}>
            <TouchableOpacity style={styles.btnPage} onPress={() => onOpenUrl(slot)}>
              <Text style={styles.btnPageTxt}>🔗</Text>
            </TouchableOpacity>
            {/* ✕ only visible in edit mode */}
            {isEditing && (
              <TouchableOpacity style={styles.btnRemove} onPress={() => onClear(slot)}>
                <Text style={styles.btnRemoveTxt}>✕</Text>
              </TouchableOpacity>
            )}
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

const SWIPE_DELETE_W = 80;
const SWIPE_TRIGGER = 50;

function SwipeableCustomRow({
  children,
  onDelete,
}: {
  children: React.ReactNode;
  onDelete: () => void;
}) {
  const translateX = useRef(new Animated.Value(0)).current;
  const isOpen = useRef(false);

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, { dx, dy }) =>
        Math.abs(dx) > 6 && Math.abs(dx) > Math.abs(dy) * 1.5,
      onPanResponderMove: (_, { dx }) => {
        const base = isOpen.current ? -SWIPE_DELETE_W : 0;
        const next = Math.max(Math.min(base + dx, 0), -SWIPE_DELETE_W);
        translateX.setValue(next);
      },
      onPanResponderRelease: (_, { dx }) => {
        const base = isOpen.current ? -SWIPE_DELETE_W : 0;
        const delta = base + dx;
        if (!isOpen.current && delta < -SWIPE_TRIGGER) {
          isOpen.current = true;
          Animated.spring(translateX, { toValue: -SWIPE_DELETE_W, useNativeDriver: true }).start();
        } else if (isOpen.current && delta > -SWIPE_DELETE_W + SWIPE_TRIGGER) {
          isOpen.current = false;
          Animated.spring(translateX, { toValue: 0, useNativeDriver: true }).start();
        } else {
          Animated.spring(translateX, {
            toValue: isOpen.current ? -SWIPE_DELETE_W : 0,
            useNativeDriver: true,
          }).start();
        }
      },
    })
  ).current;

  const handleDelete = () => {
    Animated.timing(translateX, { toValue: 0, duration: 150, useNativeDriver: true }).start(() => {
      isOpen.current = false;
      onDelete();
    });
  };

  return (
    <View style={styles.swipeContainer}>
      <View style={[styles.deleteAction]}>
        <TouchableOpacity style={styles.deleteActionBtn} onPress={handleDelete}>
          <Text style={styles.deleteActionTxt}>Delete</Text>
        </TouchableOpacity>
      </View>
      <Animated.View style={{ transform: [{ translateX }] }} {...panResponder.panHandlers}>
        {children}
      </Animated.View>
    </View>
  );
}

export function RackScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { racks, addRack, removeRack, assignMotherboard, clearSlot, expandRack, removeRow, swapSlots } = useRacks();
  const { filteredModels, isResolvingUrl, openOfficialPage, addCustomBoard, removeCustomBoard, savedUrls, saveUrl } = useCatalog();

  const [selectedRackId, setSelectedRackId] = useState<string | null>(null);
  const [addRackVisible, setAddRackVisible] = useState(false);
  const [rackName, setRackName] = useState('');
  const [assignModalVisible, setAssignModalVisible] = useState(false);
  const [addCustomVisible, setAddCustomVisible] = useState(false);
  const [pendingSlot, setPendingSlot] = useState<{ rackId: string; slot: RackSlot } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);
  const [saveModalTarget, setSaveModalTarget] = useState<Motherboard | null>(null);
  const [saveModalInitialUrl, setSaveModalInitialUrl] = useState('');
  const [clipTarget, setClipTarget] = useState<Motherboard | null>(null);
  const [clipOpenedUrl, setClipOpenedUrl] = useState('');

  const selectedRack = racks.find((r) => r.id === selectedRackId) ?? racks[0] ?? null;
  const size = slotSize(isEditing);

  const searchedModels = filteredModels.filter((b) => {
    const tokens = searchQuery.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (tokens.length === 0) return true;
    const haystack = (b.fullModelName + ' ' + b.chipset + ' ' + b.brand).toLowerCase();
    return tokens.every((t) => haystack.includes(t));
  });

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={() => {
            setIsEditing((v) => !v);
            setSelectedSlotId(null);
          }}
          style={styles.editBtn}
        >
          <Text style={styles.editBtnTxt}>{isEditing ? 'Done' : 'Edit'}</Text>
        </TouchableOpacity>
      ),
    });
  }, [navigation, isEditing]);

  const handleSelectRack = (id: string) => {
    setSelectedRackId(id);
    setSelectedSlotId(null);
  };

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
      if (!slot.motherboard) return;
      const { shouldPrompt, openedUrl } = await openOfficialPage(slot.motherboard);
      if (shouldPrompt) { setClipTarget(slot.motherboard); setClipOpenedUrl(openedUrl); }
    },
    [openOfficialPage]
  );

  const handleClipSave = () => {
    if (!clipTarget) return;
    setSaveModalTarget(clipTarget);
    setSaveModalInitialUrl(clipOpenedUrl);
    setClipTarget(null);
    setClipOpenedUrl('');
  };

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
          <View key={r.id} style={styles.tabWrapper}>
            <TouchableOpacity
              style={[styles.tab, selectedRack?.id === r.id && styles.tabActive]}
              onPress={() => handleSelectRack(r.id)}
            >
              <Text style={[styles.tabTxt, selectedRack?.id === r.id && styles.tabTxtActive]}>
                {r.name}
              </Text>
            </TouchableOpacity>
            {isEditing && (
              <TouchableOpacity style={styles.tabDeleteBadge} onPress={() => handleDeleteRack(r)}>
                <Text style={styles.tabDeleteBadgeTxt}>×</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
        {isEditing && (
          <TouchableOpacity style={styles.newBtn} onPress={() => setAddRackVisible(true)}>
            <Text style={styles.newBtnTxt}>+ New Rack</Text>
          </TouchableOpacity>
        )}
      </ScrollView>

      {/* Edit mode hint */}
      {isEditing && (
        <View style={styles.editHint}>
          <Text style={styles.editHintTxt}>
            {selectedSlotId
              ? 'Now tap another slot to swap'
              : 'Tap a slot to select, tap another to swap'}
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
                  size={size}
                  isEditing={isEditing}
                  isSelected={slot.id === selectedSlotId}
                  hasSavedUrl={!!slot.motherboard && !!savedUrls[slot.motherboard.id]}
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
          {isEditing && (
            <TouchableOpacity
              style={styles.addRowBtn}
              onPress={() => expandRack(selectedRack.id)}
            >
              <Text style={styles.addRowTxt}>+ Add Row</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      ) : (
        <View style={styles.empty}>
          {isEditing ? (
            <TouchableOpacity style={styles.createFirstBtn} onPress={() => setAddRackVisible(true)}>
              <Text style={styles.createFirstTxt}>+ New Rack</Text>
            </TouchableOpacity>
          ) : (
            <>
              <Text style={styles.emptyTxt}>No racks yet.</Text>
              <Text style={styles.emptyHint}>Tap "Edit" to create your first rack.</Text>
            </>
          )}
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

      {/* Assign modal — paddingTop from insets avoids status bar overlap in Modal context */}
      <Modal visible={assignModalVisible} animationType="slide">
        <View style={[styles.assignModal, { paddingTop: insets.top }]}>
          <View style={styles.assignHeader}>
            <Text style={styles.assignTitle}>Select Motherboard</Text>
            <TouchableOpacity onPress={() => setAssignModalVisible(false)}>
              <Text style={styles.cancelLink}>Cancel</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.searchBox}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search (use spaces for AND, e.g. '650 wifi')"
              value={searchQuery}
              onChangeText={setSearchQuery}
              clearButtonMode="while-editing"
              autoCorrect={false}
              autoFocus={false}
              returnKeyType="done"
              onSubmitEditing={Keyboard.dismiss}
              blurOnSubmit
            />
          </View>
          <FlatList
            data={searchedModels}
            keyExtractor={(item) => item.id}
            keyboardShouldPersistTaps="handled"
            keyboardDismissMode="on-drag"
            renderItem={({ item }) => {
              const row = (
                <TouchableOpacity style={styles.assignRow} onPress={() => handleSelectBoard(item)}>
                  <View style={styles.assignRowLeft}>
                    <Text style={styles.assignModel}>{item.fullModelName}</Text>
                    <Text style={styles.assignChipset}>{item.chipset}</Text>
                  </View>
                  <View style={styles.assignBadges}>
                    {!!savedUrls[item.id] && (
                      <View style={styles.assignUrlBadge}>
                        <Text style={styles.assignUrlBadgeTxt}>URL</Text>
                      </View>
                    )}
                    {item.isCustom && (
                      <View style={styles.customBadge}>
                        <Text style={styles.customBadgeTxt}>Custom</Text>
                      </View>
                    )}
                  </View>
                </TouchableOpacity>
              );
              if (item.isCustom) {
                return (
                  <SwipeableCustomRow onDelete={() => removeCustomBoard(item.id)}>
                    {row}
                  </SwipeableCustomRow>
                );
              }
              return row;
            }}
            ListFooterComponent={
              <TouchableOpacity
                style={styles.addCustomRow}
                onPress={() => {
                  setAssignModalVisible(false);
                  setAddCustomVisible(true);
                }}
              >
                <Text style={styles.addCustomTxt}>+ Can't find your board? Add it manually</Text>
              </TouchableOpacity>
            }
            contentContainerStyle={{ paddingBottom: 24 }}
          />
        </View>
      </Modal>

      {/* Add Custom Board modal */}
      <AddCustomBoardModal
        visible={addCustomVisible}
        onClose={() => {
          setAddCustomVisible(false);
          setAssignModalVisible(true);
        }}
        onSave={(board) => {
          addCustomBoard(board);
          setAddCustomVisible(false);
          if (pendingSlot) {
            assignMotherboard(pendingSlot.rackId, pendingSlot.slot.id, board);
            setPendingSlot(null);
          }
        }}
      />

      <SaveUrlModal
        visible={saveModalTarget !== null}
        boardName={saveModalTarget?.fullModelName ?? ''}
        existingUrl={saveModalTarget ? savedUrls[saveModalTarget.id] : undefined}
        initialUrl={saveModalInitialUrl || undefined}
        onSave={(url) => { if (saveModalTarget) saveUrl(saveModalTarget.id, url); }}
        onClose={() => { setSaveModalTarget(null); setSaveModalInitialUrl(''); }}
      />

      {/* Save URL prompt */}
      {clipTarget && (
        <View style={styles.clipBanner}>
          <View style={styles.clipBannerLeft}>
            <Text style={styles.clipBannerTitle} numberOfLines={1}>{clipTarget.fullModelName}</Text>
            <Text style={styles.clipBannerHint}>Tap Save URL to paste and confirm</Text>
          </View>
          <View style={styles.clipBannerBtns}>
            <TouchableOpacity style={styles.clipSaveBtn} onPress={handleClipSave}>
              <Text style={styles.clipSaveBtnTxt}>Save URL</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setClipTarget(null)}>
              <Text style={styles.clipSkipTxt}>Skip</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  strip: { maxHeight: 56, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#ddd' },
  stripContent: { paddingHorizontal: 12, paddingVertical: 10, gap: 8, alignItems: 'center' },

  tabWrapper: { position: 'relative' },
  tab: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, backgroundColor: '#f0f0f0' },
  tabActive: { backgroundColor: '#007AFF' },
  tabTxt: { fontSize: 14, color: '#333', fontWeight: '500' },
  tabTxtActive: { color: '#fff' },
  tabDeleteBadge: {
    position: 'absolute', top: -5, right: -5,
    backgroundColor: '#FF3B30', borderRadius: 9,
    width: 18, height: 18,
    justifyContent: 'center', alignItems: 'center',
    zIndex: 10,
  },
  tabDeleteBadgeTxt: { color: '#fff', fontSize: 13, fontWeight: '700', lineHeight: 18 },

  newBtn: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: '#007AFF' },
  newBtnTxt: { color: '#007AFF', fontSize: 14, fontWeight: '500' },

  editBtn: { marginRight: 12 },
  editBtnTxt: { color: '#007AFF', fontSize: 16, fontWeight: '600' },

  editHint: {
    backgroundColor: '#FFF9E6',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#F0C040',
    paddingHorizontal: 16,
    paddingVertical: 7,
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
  slotSelected: { borderColor: '#007AFF', borderWidth: 2, backgroundColor: '#EEF5FF' },
  slotTapArea: { flex: 1 },
  slotDeleteBadge: {
    position: 'absolute', top: -6, right: -6,
    backgroundColor: '#FF3B30', borderRadius: 11,
    width: 22, height: 22,
    justifyContent: 'center', alignItems: 'center',
    zIndex: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2, shadowRadius: 2, elevation: 3,
  },
  slotDeleteBadgeTxt: { color: '#fff', fontSize: 15, fontWeight: '700', lineHeight: 18 },
  slotNum: { fontSize: 10, color: '#999', fontWeight: '700', textTransform: 'uppercase' },
  slotModel: { fontSize: 11, fontWeight: '600', color: '#111', flex: 1, marginTop: 2 },
  slotChipset: {
    fontSize: 10, color: '#2563EB', fontWeight: '600',
    backgroundColor: '#EFF6FF', alignSelf: 'flex-start',
    paddingHorizontal: 5, paddingVertical: 2, borderRadius: 4,
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

  rowDelBtn: { width: ROW_DEL_W, justifyContent: 'center', alignItems: 'center', alignSelf: 'stretch' },
  rowDelTxt: { fontSize: 24, color: '#DC2626', fontWeight: '300' },

  addRowBtn: {
    marginTop: 4, paddingVertical: 12, borderRadius: 10,
    borderWidth: 1, borderColor: '#007AFF', borderStyle: 'dashed', alignItems: 'center',
  },
  addRowTxt: { color: '#007AFF', fontSize: 14, fontWeight: '600' },

  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  emptyTxt: { fontSize: 17, color: '#555', fontWeight: '500' },
  emptyHint: { fontSize: 14, color: '#aaa' },
  createFirstBtn: {
    backgroundColor: '#007AFF', paddingHorizontal: 28, paddingVertical: 14,
    borderRadius: 14,
  },
  createFirstTxt: { color: '#fff', fontSize: 16, fontWeight: '600' },

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
  assignHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: 16, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#ddd',
  },
  assignTitle: { fontSize: 18, fontWeight: '700' },
  cancelLink: { color: '#007AFF', fontSize: 16 },
  searchBox: { paddingHorizontal: 16, paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#eee' },
  searchInput: { backgroundColor: '#f2f2f7', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, fontSize: 15 },
  swipeContainer: { overflow: 'hidden' },
  deleteAction: {
    position: 'absolute', right: 0, top: 0, bottom: 0,
    width: SWIPE_DELETE_W, justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#FF3B30',
  },
  deleteActionBtn: { flex: 1, width: '100%', justifyContent: 'center', alignItems: 'center' },
  deleteActionTxt: { color: '#fff', fontSize: 14, fontWeight: '700' },
  assignRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 13, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#eee', backgroundColor: '#fff' },
  assignRowLeft: { flex: 1 },
  assignModel: { fontSize: 15, fontWeight: '500', color: '#111' },
  assignChipset: { fontSize: 13, color: '#888', marginTop: 2 },
  customBadge: { backgroundColor: '#FFF3CD', borderRadius: 6, paddingHorizontal: 7, paddingVertical: 3, marginLeft: 8 },
  customBadgeTxt: { fontSize: 11, color: '#856404', fontWeight: '700' },
  addCustomRow: {
    paddingHorizontal: 16, paddingVertical: 16,
    borderTopWidth: StyleSheet.hairlineWidth, borderColor: '#eee',
    alignItems: 'center',
    marginTop: 8,
  },
  addCustomTxt: { color: '#007AFF', fontSize: 15, fontWeight: '500' },

  slotChipsetRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  slotUrlBadge: { backgroundColor: '#E8F5E9', borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  slotUrlBadgeTxt: { fontSize: 8, color: '#2E7D32', fontWeight: '700' },

  assignBadges: { flexDirection: 'row', gap: 6, alignItems: 'center' },
  assignUrlBadge: { backgroundColor: '#E8F5E9', borderRadius: 6, paddingHorizontal: 7, paddingVertical: 3 },
  assignUrlBadgeTxt: { fontSize: 11, color: '#2E7D32', fontWeight: '700' },

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
  clipBannerBtns: { alignItems: 'center', gap: 4 },
  clipBannerBtnRow: { flexDirection: 'row', gap: 6 },
  clipSaveBtn: { backgroundColor: '#30D158', borderRadius: 10, paddingHorizontal: 14, paddingVertical: 8 },
  clipSaveBtnSuccess: { backgroundColor: '#34C759' },
  clipSaveBtnTxt: { color: '#fff', fontSize: 14, fontWeight: '700' },
  clipEditBtn: { backgroundColor: '#48484A', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8 },
  clipEditBtnTxt: { color: '#fff', fontSize: 14, fontWeight: '600' },
  clipSkipTxt: { fontSize: 12, color: '#8E8E93' },
});
