import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { RackSlot } from '../models/Rack';

interface Props {
  slot: RackSlot;
  onAssign: (slot: RackSlot) => void;
  onClear: (slot: RackSlot) => void;
  onOpenUrl: (slot: RackSlot) => void;
}

export function SlotItem({ slot, onAssign, onClear, onOpenUrl }: Props) {
  const board = slot.motherboard;

  return (
    <View style={styles.container}>
      <Text style={styles.position}>Slot {slot.position + 1}</Text>
      {board ? (
        <View style={styles.boardInfo}>
          <Text style={styles.modelName} numberOfLines={2}>
            {board.fullModelName}
          </Text>
          <Text style={styles.chipset}>{board.chipset}</Text>
          <View style={styles.actions}>
            <TouchableOpacity
              style={[styles.btn, styles.btnPrimary]}
              onPress={() => onOpenUrl(slot)}
            >
              <Text style={styles.btnTextPrimary}>Official Page</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.btnDanger]}
              onPress={() => onClear(slot)}
            >
              <Text style={styles.btnTextDanger}>Remove</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <TouchableOpacity
          style={[styles.btn, styles.btnSecondary]}
          onPress={() => onAssign(slot)}
        >
          <Text style={styles.btnTextSecondary}>+ Assign Board</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f8f8f8',
    borderRadius: 10,
    padding: 14,
    marginVertical: 6,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  position: {
    fontSize: 12,
    color: '#888',
    marginBottom: 6,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  boardInfo: {
    gap: 4,
  },
  modelName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
  },
  chipset: {
    fontSize: 13,
    color: '#555',
    marginBottom: 8,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  btn: {
    paddingVertical: 7,
    paddingHorizontal: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnPrimary: {
    backgroundColor: '#007AFF',
  },
  btnDanger: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#FF3B30',
  },
  btnSecondary: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  btnTextPrimary: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  btnTextDanger: {
    color: '#FF3B30',
    fontSize: 13,
    fontWeight: '600',
  },
  btnTextSecondary: {
    color: '#007AFF',
    fontSize: 13,
    fontWeight: '600',
  },
});
