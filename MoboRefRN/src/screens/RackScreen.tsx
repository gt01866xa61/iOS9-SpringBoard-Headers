import React, { useState, useCallback, useLayoutEffect, useRef, useEffect, useMemo } from 'react';
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
import { AddCustomBoardModal } from '../components/AddCustomBoardModal';
import { SaveUrlModal } from '../components/SaveUrlModal';
import { BoardBadges } from '../components/BoardBadges';
import { Rack, RackSlot } from '../models/Rack';
import { Motherboard } from '../models/Motherboard';
import { VisitStatus } from '../hooks/useVisitedBoards';
import { isIntelChipset, resolve } from '../services/URLResolverService';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/types';

const COLS = 3;
const GAP = 8;
const PADDING = 12;
const ROW_DEL_W = 36;
const WIN_W = Dimensions.get('window').width;

function slotSize(isEditing: boolean) {
  return (WIN_W - PADDING * 2 - GAP * COLS - (isEditing ? ROW_DEL_W : 0)) / COLS;
}

// Bottom-sheet info card. Tap backdrop to dismiss.
// Uses visible+onDismiss so the open-URL call only fires AFTER the slide-out
// animation fully completes — prevents the iOS "two Modals at once" hang.
function InfoCard({
  slot,
  visible,
  hasSavedUrl,
  visitStatus,
  onClose,
  onDismiss,
  onOpenUrl,
}: {
  slot: RackSlot;
  visible: boolean;
  hasSavedUrl: boolean;
  visitStatus?: VisitStatus;
  onClose: () => void;
  onDismiss: () => void;
  onOpenUrl: (s: RackSlot) => void;
}) {
  const board = slot.motherboard!;
  const chipsetIsIntel = isIntelChipset(board.chipset);
  return (
    <Modal
      transparent
      animationType="slide"
      visible={visible}
      onRequestClose={onClose}
      onDismiss={onDismiss}
    >
      <TouchableOpacity style={ic.backdrop} activeOpacity={1} onPress={onClose} />
      <View style={ic.sheet}>
        <View style={ic.handle} />
        <View style={ic.chipRow}>
          <View style={[ic.chipBadge, chipsetIsIntel ? ic.chipIntel : ic.chipAmd]}>
            <Text style={[ic.chipTxt, chipsetIsIntel ? ic.chipTxtIntel : ic.chipTxtAmd]}>
              {board.chipset}
            </Text>
          </View>
          <Text style={ic.brandTxt}>{board.brand}</Text>
        </View>
        <Text style={ic.modelTxt}>{board.fullModelName}</Text>
        <View style={ic.badgesRow}>
          <BoardBadges board={board} hasSaved={hasSavedUrl} visitStatus={visitStatus} />
        </View>
        <TouchableOpacity
          style={ic.openBtn}
          activeOpacity={0.85}
          onPress={() => onOpenUrl(slot)}
        >
          <Text style={ic.openBtnTxt}>🔗  Open Spec Page</Text>
        </TouchableOpacity>
      </View>
    </Modal>
  );
}

// Drag visual: a copy of the slot that follows the finger.
function FloatingSlot({ slot, sz, slotIndex }: { slot: RackSlot; sz: number; slotIndex: number }) {
  const board = slot.motherboard;
  const isIntel = board ? isIntelChipset(board.chipset) : true;
  return (
    <View style={[styles.slot, styles.floatSlot, { width: sz, height: sz }]}>
      <Text style={styles.slotNum}>{slotIndex}</Text>
      {board ? (
        <>
          <Text style={styles.slotModel} numberOfLines={2}>{board.fullModelName}</Text>
          <Text style={styles.slotBrand}>{board.brand}</Text>
          <Text style={[styles.slotChipset, isIntel ? styles.slotChipsetIntel : styles.slotChipsetAmd]}>
            {board.chipset}
          </Text>
        </>
      ) : (
        <View style={styles.emptySlotHint}>
          <Text style={styles.emptySlotTxt}>—</Text>
        </View>
      )}
    </View>
  );
}

// A space coordinate that has no slot framework. Edit mode shows "+" to
// re-add a slot here. Drag mode highlights when the finger is over it so the
// dragged slot can land directly on this empty space.
function EmptySpace({
  space,
  size,
  isEditing,
  isHoverTarget,
  hasSelection,
  onAddSlot,
  onTapWithSelection,
}: {
  space: number;
  size: number;
  isEditing: boolean;
  isHoverTarget: boolean;
  hasSelection: boolean;
  onAddSlot: (space: number) => void;
  onTapWithSelection: (space: number) => void;
}) {
  return (
    <View
      style={[
        styles.emptySpace,
        { width: size, height: size },
        isHoverTarget && styles.slotHover,
      ]}
    >
      {isEditing ? (
        hasSelection ? (
          <TouchableOpacity
            style={styles.emptySpaceTap}
            onPress={() => onTapWithSelection(space)}
            activeOpacity={0.6}
          >
            <Text style={styles.emptySpaceTapTxt}>↵</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={styles.emptySpaceTap}
            onPress={() => onAddSlot(space)}
            activeOpacity={0.6}
          >
            <Text style={styles.emptySpaceAddTxt}>+</Text>
          </TouchableOpacity>
        )
      ) : null}
    </View>
  );
}

function GridSlot({
  slot,
  size,
  isEditing,
  isSelected,
  isDragging,
  isHoverTarget,
  hasSavedUrl,
  visitStatus,
  onAssign,
  onClear,
  onDeleteSlot,
  onTap,
  onInfo,
  onOpenUrl,
  onLongPressDrag,
  slotIndex,
}: {
  slot: RackSlot;
  size: number;
  isEditing: boolean;
  isSelected: boolean;
  isDragging: boolean;
  isHoverTarget: boolean;
  hasSavedUrl: boolean;
  visitStatus?: VisitStatus;
  onAssign: (s: RackSlot) => void;
  onClear: (s: RackSlot) => void;
  onDeleteSlot: (s: RackSlot) => void;
  onTap: (s: RackSlot) => void;
  onInfo: (s: RackSlot) => void;
  onOpenUrl: (s: RackSlot) => void;
  onLongPressDrag: (s: RackSlot) => void;
  slotIndex: number;
}) {
  const board = slot.motherboard;
  const chipsetIsIntel = board ? isIntelChipset(board.chipset) : true;

  if (isEditing) {
    return (
      <View
        style={[
          styles.slot,
          { width: size, height: size },
          isSelected && styles.slotSelected,
          isHoverTarget && !isSelected && styles.slotHover,
          isDragging && styles.slotDragging,
        ]}
      >
        <TouchableOpacity
          style={styles.slotTapArea}
          activeOpacity={0.7}
          onPress={() => onTap(slot)}
          onLongPress={() => onLongPressDrag(slot)}
          delayLongPress={350}
        >
          <Text style={styles.slotNum}>{slotIndex}</Text>
          {board ? (
            <>
              <Text style={styles.slotModel} numberOfLines={3}>{board.fullModelName}</Text>
              <Text style={styles.slotBrand}>{board.brand}</Text>
              <Text style={[styles.slotChipset, chipsetIsIntel ? styles.slotChipsetIntel : styles.slotChipsetAmd]}>
                {board.chipset}
              </Text>
            </>
          ) : (
            <View style={styles.emptySlotHint}>
              <Text style={styles.emptySlotTxt}>{isSelected ? '✓' : '—'}</Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Top-left × — color depends on whether the slot holds a board.
            RED × on a filled slot: clears the board, slot stays as a drop target.
            GRAY × on an empty slot: deletes the slot framework and compacts —
            slots after it shift one space forward (last space ends up empty). */}
        {!isSelected && (
          <TouchableOpacity
            style={board ? styles.slotRemoveBadge : styles.slotDeleteBadge}
            onPress={() => {
              if (board) {
                Alert.alert(
                  'Clear Slot',
                  `Remove "${board.fullModelName}"?\nSlot position stays as a drop target.`,
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Clear', style: 'destructive', onPress: () => onClear(slot) },
                  ]
                );
              } else {
                onDeleteSlot(slot);
              }
            }}
          >
            <Text style={board ? styles.slotRemoveBadgeTxt : styles.slotDeleteBadgeTxt}>×</Text>
          </TouchableOpacity>
        )}
        {/* Top-right: ✓ marks the selected source slot for tap-to-move. */}
        {isSelected && (
          <View style={styles.selectedBadge}>
            <Text style={styles.selectedBadgeTxt}>✓</Text>
          </View>
        )}
      </View>
    );
  }

  return (
    <View style={[styles.slot, { width: size, height: size }]}>
      <TouchableOpacity
        style={styles.slotTapArea}
        activeOpacity={board ? 0.75 : 1}
        onPress={() => (board ? onInfo(slot) : onAssign(slot))}
      >
        <Text style={styles.slotNum}>{slotIndex}</Text>
        {board ? (
          <>
            <Text style={styles.slotModel} numberOfLines={1}>{board.fullModelName}</Text>
            <Text style={styles.slotBrand}>{board.brand}</Text>
            <Text style={[styles.slotChipset, chipsetIsIntel ? styles.slotChipsetIntel : styles.slotChipsetAmd]}>
              {board.chipset}
            </Text>
            <View style={styles.slotBadgesRow}>
              <BoardBadges board={board} hasSaved={hasSavedUrl} visitStatus={visitStatus} size="compact" />
            </View>
          </>
        ) : (
          <View style={styles.emptySlotHint}>
            <Text style={styles.assignTxt}>+</Text>
          </View>
        )}
      </TouchableOpacity>
      {/* Quick-open URL: bypasses InfoCard for one-tap access. */}
      {board && (
        <TouchableOpacity
          style={styles.slotUrlBtn}
          onPress={() => onOpenUrl(slot)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Text style={styles.slotUrlBtnTxt}>🔗</Text>
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
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const insets = useSafeAreaInsets();
  const { racks, addRack, removeRack, assignMotherboard, clearSlot, expandRack, removeRow, deleteSlot, addSlotAtSpace, moveSlot } = useRacks();
  const { filteredModels, addCustomBoard, removeCustomBoard, savedUrls, saveUrl, visitRecord } = useCatalog();

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
  const [infoCardSlot, setInfoCardSlot] = useState<RackSlot | null>(null);
  const [infoCardVisible, setInfoCardVisible] = useState(false);
  // When user taps "Open Spec Page", we first close the sheet (→ slide-out
  // animation), then open the URL in onDismiss (fires after animation ends).
  const pendingInfoOpenRef = useRef<RackSlot | null>(null);
  // Forward-declared ref to handleOpenUrl (defined later) so handleInfoDismiss
  // can call it without a circular dep / TDZ on the useCallback dependency list.
  const handleOpenUrlRef = useRef<((slot: RackSlot) => Promise<void>) | null>(null);

  // ── iPhone-style drag state ────────────────────────────────────────────
  // dragSlotId === null while idle. Once long-press fires, we set everything
  // and the absolute overlay below captures finger movement.
  const [dragSlotId, setDragSlotId] = useState<string | null>(null);
  const [dragPos, setDragPos] = useState({ x: 0, y: 0 });
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Refs feed values into PanResponder closures (created once via useRef below).
  const dragSlotIdRef = useRef<string | null>(null);
  const hoverIndexRef = useRef<number | null>(null);
  const slotsRef = useRef<RackSlot[]>([]);
  const totalSpacesRef = useRef(0);
  const selectedRackRef = useRef<Rack | null>(null);
  const moveSlotRef = useRef(moveSlot);
  const containerRef = useRef<View>(null);
  const containerOriginRef = useRef({ x: 0, y: 0 });
  const gridContainerRef = useRef<View>(null);
  const gridOriginRef = useRef({ x: 0, y: 0 });
  const szRef = useRef(0);

  const selectedRack = racks.find((r) => r.id === selectedRackId) ?? racks[0] ?? null;
  const size = slotSize(isEditing);
  // Sort slots by space coordinate (slots may be sparse — gaps allowed).
  const slots = useMemo(
    () => [...(selectedRack?.slots ?? [])].sort((a, b) => a.space - b.space),
    [selectedRack]
  );
  const slotIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    slots.forEach((s, i) => map.set(s.id, i + 1));
    return map;
  }, [slots]);
  const totalSpaces = selectedRack?.totalSpaces ?? 0;

  // Keep refs in sync so the once-created PanResponder always sees fresh values.
  useEffect(() => { slotsRef.current = slots; }, [slots]);
  useEffect(() => { totalSpacesRef.current = totalSpaces; }, [totalSpaces]);
  useEffect(() => { selectedRackRef.current = selectedRack; }, [selectedRack]);
  useEffect(() => { moveSlotRef.current = moveSlot; }, [moveSlot]);

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
      const board = slot.motherboard;
      const url = savedUrls[board.id] ?? (await resolve(board));
      navigation.navigate('Browser', { board, initialUrl: url });
    },
    [navigation, savedUrls]
  );

  // Keep the forward-declared ref in sync so handleInfoDismiss reads the
  // latest handleOpenUrl (avoids stale closure when its deps change).
  useEffect(() => { handleOpenUrlRef.current = handleOpenUrl; }, [handleOpenUrl]);

  // Gray ×: delete the slot framework. Slots after it shift one space forward;
  // the highest space ends up empty (still part of totalSpaces, can be filled
  // back via the "+" button at that space).
  const handleDeleteSlot = useCallback(
    (rackId: string, slot: RackSlot) => {
      Alert.alert(
        'Delete Slot',
        `Remove slot at position ${slot.space + 1}?\nThe space will remain empty.`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Delete', style: 'destructive', onPress: () => deleteSlot(rackId, slot.id) },
        ]
      );
    },
    [deleteSlot]
  );

  const handleAddSlotAtSpace = useCallback(
    (rackId: string, space: number) => addSlotAtSpace(rackId, space),
    [addSlotAtSpace]
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
      // Tap-to-move: target's space is the destination.
      moveSlot(selectedRack.id, selectedSlotId, slot.space);
      setSelectedSlotId(null);
    },
    [selectedRack, selectedSlotId, moveSlot]
  );

  // Tap on an empty space (with selected source) → relocate selected slot here.
  const handleEmptySpaceTap = useCallback(
    (space: number) => {
      if (!selectedRack || !selectedSlotId) return;
      moveSlot(selectedRack.id, selectedSlotId, space);
      setSelectedSlotId(null);
    },
    [selectedRack, selectedSlotId, moveSlot]
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

  const handleSlotInfo = useCallback((slot: RackSlot) => {
    if (!slot.motherboard) return;
    pendingInfoOpenRef.current = null;
    setInfoCardSlot(slot);
    setInfoCardVisible(true);
  }, []);

  const handleInfoClose = useCallback(() => {
    pendingInfoOpenRef.current = null;
    setInfoCardVisible(false);
  }, []);

  // "Open Spec Page" pressed inside the card: dismiss the sheet, then open
  // the URL in onDismiss so iOS has no overlapping modal animations.
  const handleInfoOpenUrl = useCallback((slot: RackSlot) => {
    pendingInfoOpenRef.current = slot;
    setInfoCardVisible(false);
  }, []);

  // Fires after the slide-out animation fully completes (iOS onDismiss).
  // We delegate to handleOpenUrl (via ref to avoid TDZ) so the in-app browser
  // is used — same UX as the 🔗 button. onDismiss timing guarantees the
  // InfoCard Modal is fully gone before the browser Modal presents, avoiding
  // the "two stacked Modals" hang we hit before.
  const handleInfoDismiss = useCallback(() => {
    const slot = pendingInfoOpenRef.current;
    pendingInfoOpenRef.current = null;
    setInfoCardSlot(null);
    if (slot) handleOpenUrlRef.current?.(slot);
  }, []);

  // Long-press → enter drag mode. We measure the grid container in window
  // coordinates so subsequent finger positions can be mapped to slot indices.
  const handleLongPressDrag = useCallback((slot: RackSlot) => {
    // Measure container first so we can convert window coords → container coords.
    containerRef.current?.measureInWindow((cx, cy) => {
      containerOriginRef.current = { x: cx, y: cy };
      gridContainerRef.current?.measureInWindow((gx, gy) => {
        const sz = slotSize(true);
        szRef.current = sz;
        gridOriginRef.current = { x: gx, y: gy };

        const col = slot.space % COLS;
        const row = Math.floor(slot.space / COLS);
        // Subtract container origin: dragPos is relative to the dragOverlay which
        // sits at position:absolute top/left 0 within the container View.
        const x = gx + PADDING + col * (sz + GAP) - cx;
        const y = gy + PADDING + row * (sz + GAP) - cy;

        dragSlotIdRef.current = slot.id;
        hoverIndexRef.current = slot.space;
        setDragSlotId(slot.id);
        setDragPos({ x, y });
        setHoverIndex(slot.space);
        setSelectedSlotId(null);
      });
    });
  }, []);

  // Created once. Closures reference *Ref values so they always read fresh state.
  // Capture variants are set so this overlay wins responder negotiation while
  // dragging, even though the touch originated on the slot below.
  const overlayPan = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => !!dragSlotIdRef.current,
      onStartShouldSetPanResponderCapture: () => !!dragSlotIdRef.current,
      onMoveShouldSetPanResponder: () => !!dragSlotIdRef.current,
      onMoveShouldSetPanResponderCapture: () => !!dragSlotIdRef.current,
      onPanResponderGrant: (e) => {
        const sz = szRef.current;
        const { pageX, pageY } = e.nativeEvent;
        const { x: cx, y: cy } = containerOriginRef.current;
        setDragPos({ x: pageX - sz / 2 - cx, y: pageY - sz / 2 - cy });
      },
      onPanResponderMove: (_, { moveX, moveY }) => {
        const sz = szRef.current;
        const { x: cx, y: cy } = containerOriginRef.current;
        setDragPos({ x: moveX - sz / 2 - cx, y: moveY - sz / 2 - cy });

        const { x: gx, y: gy } = gridOriginRef.current;
        const relX = moveX - gx - PADDING;
        const relY = moveY - gy - PADDING;
        if (relX < 0 || relY < 0) return;
        const total = totalSpacesRef.current;
        if (total === 0) return;
        const col = Math.min(Math.max(Math.floor(relX / (sz + GAP)), 0), COLS - 1);
        const row = Math.max(Math.floor(relY / (sz + GAP)), 0);
        const space = Math.min(row * COLS + col, total - 1);
        if (space !== hoverIndexRef.current) {
          hoverIndexRef.current = space;
          setHoverIndex(space);
        }
      },
      onPanResponderRelease: () => {
        const fromId = dragSlotIdRef.current;
        const toSpace = hoverIndexRef.current;
        const rack = selectedRackRef.current;
        const cur = slotsRef.current;
        if (fromId && toSpace !== null && rack) {
          const from = cur.find((s) => s.id === fromId);
          if (from && from.space !== toSpace) {
            // moveSlot handles both empty (direct relocate) and occupied (insert) targets.
            moveSlotRef.current(rack.id, fromId, toSpace);
          }
        }
        dragSlotIdRef.current = null;
        hoverIndexRef.current = null;
        setDragSlotId(null);
        setHoverIndex(null);
      },
      onPanResponderTerminate: () => {
        dragSlotIdRef.current = null;
        hoverIndexRef.current = null;
        setDragSlotId(null);
        setHoverIndex(null);
      },
    })
  ).current;

  const draggedSlot = dragSlotId ? slots.find((s) => s.id === dragSlotId) ?? null : null;

  return (
    <View style={styles.container} ref={containerRef}>
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
            {dragSlotId
              ? 'Drag to a target slot, release to drop'
              : selectedSlotId
              ? 'Tap destination slot to move here (or hold any slot to drag)'
              : '🔴× clears board · ⚫× deletes slot · + adds slot · Hold to drag · − removes row'}
          </Text>
        </View>
      )}

      {/* Grid */}
      {selectedRack ? (
        <ScrollView contentContainerStyle={styles.grid} scrollEnabled={!dragSlotId}>
          {/* PanResponder lives on the grid (an ancestor of every slot) so it can
              steal the in-progress touch from the slot's TouchableOpacity right
              after long-press flips dragSlotIdRef.current to true. */}
          <View ref={gridContainerRef} collapsable={false} {...overlayPan.panHandlers}>
            {Array.from({ length: Math.ceil(totalSpaces / COLS) }, (_, row) => (
              <View key={row} style={styles.gridRow}>
                {Array.from({ length: COLS }, (_, col) => {
                  const space = row * COLS + col;
                  if (space >= totalSpaces) return null;
                  const slot = slots.find((s) => s.space === space);
                  if (slot) {
                    return (
                      <GridSlot
                        key={slot.id}
                        slot={slot}
                        size={size}
                        isEditing={isEditing}
                        isSelected={slot.id === selectedSlotId}
                        isDragging={slot.id === dragSlotId}
                        isHoverTarget={
                          dragSlotId !== null && slot.id !== dragSlotId && slot.space === hoverIndex
                        }
                        hasSavedUrl={!!slot.motherboard && !!savedUrls[slot.motherboard.id]}
                        visitStatus={slot.motherboard ? visitRecord[slot.motherboard.id] : undefined}
                        onAssign={(s) => handleAssign(selectedRack.id, s)}
                        onClear={(s) => clearSlot(selectedRack.id, s.id)}
                        onDeleteSlot={(s) => handleDeleteSlot(selectedRack.id, s)}
                        onTap={handleSlotTap}
                        onInfo={handleSlotInfo}
                        onOpenUrl={handleOpenUrl}
                        onLongPressDrag={handleLongPressDrag}
                        slotIndex={slotIndexMap.get(slot.id) ?? slot.space + 1}
                      />
                    );
                  }
                  return (
                    <EmptySpace
                      key={`empty-${space}`}
                      space={space}
                      size={size}
                      isEditing={isEditing}
                      isHoverTarget={dragSlotId !== null && hoverIndex === space}
                      hasSelection={!!selectedSlotId}
                      onAddSlot={(s) => handleAddSlotAtSpace(selectedRack.id, s)}
                      onTapWithSelection={handleEmptySpaceTap}
                    />
                  );
                })}
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
          </View>
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
                    <Text style={styles.assignChipset}>{item.brand} · {item.chipset}</Text>
                  </View>
                  <View style={styles.assignBadges}>
                    <BoardBadges
                      board={item}
                      hasSaved={!!savedUrls[item.id]}
                      visitStatus={visitRecord[item.id]}
                    />
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
        onSave={(url) => { if (saveModalTarget) saveUrl(saveModalTarget.id, url); }}
        onClose={() => setSaveModalTarget(null)}
      />

      {/* Info card — keep mounted until onDismiss so the slot data stays valid
          during the slide-out animation; visible controls actual visibility. */}
      {infoCardSlot && (
        <InfoCard
          slot={infoCardSlot}
          visible={infoCardVisible}
          hasSavedUrl={!!infoCardSlot.motherboard && !!savedUrls[infoCardSlot.motherboard.id]}
          visitStatus={
            infoCardSlot.motherboard ? visitRecord[infoCardSlot.motherboard.id] : undefined
          }
          onClose={handleInfoClose}
          onDismiss={handleInfoDismiss}
          onOpenUrl={handleInfoOpenUrl}
        />
      )}

      {/* Visual-only overlay for the floating slot. pointerEvents="none" so it
          never blocks taps; the actual gesture is handled by the grid View. */}
      {dragSlotId !== null && draggedSlot && (
        <View style={styles.dragOverlay} pointerEvents="none">
          <View style={[styles.dragFloatPos, { left: dragPos.x, top: dragPos.y }]}>
            <FloatingSlot slot={draggedSlot} sz={size} slotIndex={slotIndexMap.get(draggedSlot.id) ?? draggedSlot.space + 1} />
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
  slotHover: { borderColor: '#34C759', borderWidth: 2, backgroundColor: '#E8F8EE' },
  slotDragging: { opacity: 0.25, borderColor: '#C0C0C0', borderStyle: 'dashed' },
  slotTapArea: { flex: 1 },
  slotUrlBtn: {
    position: 'absolute', bottom: 4, right: 4,
    width: 26, height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(0,122,255,0.10)',
    alignItems: 'center', justifyContent: 'center',
  },
  slotUrlBtnTxt: { fontSize: 13 },
  slotRemoveBadge: {
    position: 'absolute', top: -6, left: -6,
    backgroundColor: '#FF3B30', borderRadius: 11,
    width: 22, height: 22,
    justifyContent: 'center', alignItems: 'center',
    zIndex: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2, shadowRadius: 2, elevation: 3,
  },
  slotRemoveBadgeTxt: { color: '#fff', fontSize: 15, fontWeight: '700', lineHeight: 18 },
  slotDeleteBadge: {
    position: 'absolute', top: -6, left: -6,
    backgroundColor: '#8E8E93', borderRadius: 11,
    width: 22, height: 22,
    justifyContent: 'center', alignItems: 'center',
    zIndex: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2, shadowRadius: 2, elevation: 3,
  },
  slotDeleteBadgeTxt: { color: '#fff', fontSize: 15, fontWeight: '700', lineHeight: 18 },
  slotNum: { fontSize: 10, color: '#999', fontWeight: '700', textTransform: 'uppercase' },
  slotModel: { fontSize: 11, fontWeight: '600', color: '#111', flex: 1, marginTop: 2 },
  slotBrand: { fontSize: 9, color: '#8E8E93', fontWeight: '500', marginTop: 1 },
  slotChipset: {
    fontSize: 10, fontWeight: '600',
    alignSelf: 'flex-start',
    paddingHorizontal: 5, paddingVertical: 2, borderRadius: 4,
  },
  slotChipsetIntel: { color: '#2563EB', backgroundColor: '#EFF6FF' },
  slotChipsetAmd: { color: '#8B3A1B', backgroundColor: '#F8CBAD' },
  slotBtns: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  btnPage: { backgroundColor: '#007AFF', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 },
  btnPageTxt: { fontSize: 12 },
  btnRemove: { backgroundColor: '#FEE2E2', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 },
  btnRemoveTxt: { fontSize: 12, color: '#DC2626' },

  assignBtn: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  assignTxt: { fontSize: 28, color: '#007AFF', fontWeight: '300' },

  emptySlotHint: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptySlotTxt: { fontSize: 20, color: '#ccc' },

  // Space with no slot framework — drawn as a dashed placeholder.
  emptySpace: {
    backgroundColor: '#FAFAFA',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderStyle: 'dashed',
    padding: 8,
    justifyContent: 'flex-start',
  },
  emptySpaceNum: { fontSize: 10, color: '#C7C7CC', fontWeight: '700' },
  emptySpaceTap: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptySpaceAddTxt: { fontSize: 32, color: '#C7C7CC', fontWeight: '300' },
  emptySpaceTapTxt: { fontSize: 22, color: '#34C759', fontWeight: '600' },

  selectedBadge: {
    position: 'absolute', top: 4, right: 4,
    backgroundColor: '#007AFF', borderRadius: 10,
    width: 18, height: 18, justifyContent: 'center', alignItems: 'center',
  },
  selectedBadgeTxt: { color: '#fff', fontSize: 11, fontWeight: '700' },

  rowDelBtn: { width: ROW_DEL_W, justifyContent: 'center', alignItems: 'center', alignSelf: 'stretch', marginLeft: 'auto' },
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
  addCustomRow: {
    paddingHorizontal: 16, paddingVertical: 16,
    borderTopWidth: StyleSheet.hairlineWidth, borderColor: '#eee',
    alignItems: 'center',
    marginTop: 8,
  },
  addCustomTxt: { color: '#007AFF', fontSize: 15, fontWeight: '500' },

  slotChipsetRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2, flexWrap: 'wrap' },
  slotBadgesRow: {
    flexDirection: 'row', flexWrap: 'wrap',
    gap: 3, marginTop: 3, minHeight: 14,
  },
  assignBadges: { flexDirection: 'row', gap: 6, alignItems: 'center', flexWrap: 'wrap' },

  // Drag visual: floating slot follows the finger; receives raised shadow.
  dragOverlay: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    zIndex: 100,
  },
  dragFloatPos: { position: 'absolute' },
  floatSlot: {
    backgroundColor: '#fff',
    borderColor: '#007AFF', borderWidth: 2,
    transform: [{ scale: 1.06 }],
    shadowColor: '#000', shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25, shadowRadius: 14,
    elevation: 12,
  },
});

// Info card (bottom sheet) styles — kept separate for clarity.
const ic = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)' },
  sheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 22, borderTopRightRadius: 22,
    paddingHorizontal: 24, paddingTop: 12, paddingBottom: 44,
    gap: 14,
  },
  handle: {
    alignSelf: 'center', width: 36, height: 4,
    borderRadius: 2, backgroundColor: '#D1D1D6', marginBottom: 2,
  },
  chipRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 2 },
  chipBadge: { borderRadius: 8, paddingHorizontal: 12, paddingVertical: 5 },
  chipIntel: { backgroundColor: '#EFF6FF' },
  chipAmd: { backgroundColor: '#F8CBAD' },
  chipTxt: { fontSize: 14, fontWeight: '700' },
  chipTxtIntel: { color: '#2563EB' },
  chipTxtAmd: { color: '#8B3A1B' },
  brandTxt: { fontSize: 14, color: '#8E8E93', fontWeight: '500' },
  modelTxt: { fontSize: 22, fontWeight: '700', color: '#1C1C1E', lineHeight: 30 },
  badgesRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, minHeight: 20 },
  openBtn: {
    marginTop: 4, backgroundColor: '#007AFF',
    borderRadius: 14, paddingVertical: 16, alignItems: 'center',
  },
  openBtnTxt: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
