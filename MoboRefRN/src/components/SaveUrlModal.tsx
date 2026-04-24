import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface Props {
  visible: boolean;
  boardName: string;
  existingUrl?: string;
  onSave: (url: string) => void;
  onClose: () => void;
}

export function SaveUrlModal({ visible, boardName, existingUrl, onSave, onClose }: Props) {
  const insets = useSafeAreaInsets();
  const [url, setUrl] = useState('');
  const [pastedFromClipboard, setPastedFromClipboard] = useState(false);

  useEffect(() => {
    if (!visible) return;
    // If there's an existing saved URL, prefer it. Otherwise try clipboard.
    if (existingUrl) {
      setUrl(existingUrl);
      setPastedFromClipboard(false);
      return;
    }
    (async () => {
      try {
        const clip = (await Clipboard.getStringAsync()).trim();
        if (/^https?:\/\//i.test(clip)) {
          setUrl(clip);
          setPastedFromClipboard(true);
          return;
        }
      } catch {}
      setUrl('');
      setPastedFromClipboard(false);
    })();
  }, [visible, existingUrl]);

  const handlePaste = async () => {
    try {
      const clip = (await Clipboard.getStringAsync()).trim();
      if (clip) {
        setUrl(clip);
        setPastedFromClipboard(true);
      }
    } catch {}
  };

  const handleSave = () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    onSave(trimmed);
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <KeyboardAvoidingView
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={[styles.sheet, { paddingBottom: insets.bottom + 16 }]}>
          <View style={styles.handle} />
          <Text style={styles.title}>Save Official URL</Text>
          <Text style={styles.subtitle} numberOfLines={2}>{boardName}</Text>

          {pastedFromClipboard && (
            <View style={styles.pastedTag}>
              <Text style={styles.pastedTagTxt}>📋 Auto-pasted from clipboard</Text>
            </View>
          )}

          <Text style={styles.hint}>
            Open the board in Safari, copy the URL from the address bar, and paste it below.
          </Text>

          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={url}
              onChangeText={(t) => { setUrl(t); setPastedFromClipboard(false); }}
              placeholder="https://..."
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              returnKeyType="done"
              onSubmitEditing={handleSave}
              multiline
            />
            <TouchableOpacity style={styles.pasteBtn} onPress={handlePaste}>
              <Text style={styles.pasteBtnTxt}>📋</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.saveBtn, !url.trim() && styles.saveBtnDisabled]}
            onPress={handleSave}
            disabled={!url.trim()}
          >
            <Text style={styles.saveBtnTxt}>Save URL</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.cancelBtn} onPress={onClose}>
            <Text style={styles.cancelTxt}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.35)',
  },
  sheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingHorizontal: 20,
    paddingTop: 12,
    gap: 10,
  },
  handle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: '#D1D1D6', alignSelf: 'center', marginBottom: 8,
  },
  title: { fontSize: 17, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 13, color: '#8E8E93', marginTop: -4 },
  pastedTag: {
    alignSelf: 'flex-start',
    backgroundColor: '#E8F5E9',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  pastedTagTxt: { fontSize: 12, color: '#2E7D32', fontWeight: '600' },
  hint: { fontSize: 13, color: '#555', lineHeight: 18 },
  inputRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  input: {
    flex: 1,
    borderWidth: 1, borderColor: '#D1D1D6', borderRadius: 10,
    padding: 12, fontSize: 14, minHeight: 72,
    textAlignVertical: 'top', backgroundColor: '#F9F9F9',
  },
  pasteBtn: {
    backgroundColor: '#007AFF',
    borderRadius: 10,
    width: 44, height: 44,
    justifyContent: 'center', alignItems: 'center',
  },
  pasteBtnTxt: { fontSize: 20 },
  saveBtn: {
    backgroundColor: '#007AFF', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center', marginTop: 4,
  },
  saveBtnDisabled: { backgroundColor: '#A8C7F0' },
  saveBtnTxt: { color: '#fff', fontSize: 16, fontWeight: '600' },
  cancelBtn: { alignItems: 'center', paddingVertical: 10 },
  cancelTxt: { color: '#8E8E93', fontSize: 15 },
});
