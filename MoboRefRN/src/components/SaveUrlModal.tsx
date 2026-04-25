import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Animated,
  PanResponder,
  TouchableWithoutFeedback,
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
  const [fromClipboard, setFromClipboard] = useState(false);

  const translateY = useRef(new Animated.Value(0)).current;

  const panResponder = useRef(PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: (_, { dy }) => dy > 5,
    onPanResponderTerminationRequest: () => false,
    onPanResponderMove: (_, { dy }) => {
      if (dy > 0) translateY.setValue(dy);
    },
    onPanResponderRelease: (_, { dy, vy }) => {
      if (dy > 80 || vy > 0.8) {
        // useNativeDriver: false — must be consistent with setValue() calls above
        Animated.timing(translateY, { toValue: 600, duration: 180, useNativeDriver: false })
          .start(() => { translateY.setValue(0); onClose(); });
      } else {
        Animated.spring(translateY, { toValue: 0, useNativeDriver: false }).start();
      }
    },
  })).current;

  useEffect(() => {
    if (!visible) { translateY.setValue(0); return; }
    if (existingUrl) { setUrl(existingUrl); setFromClipboard(false); return; }
    (async () => {
      try {
        const clip = (await Clipboard.getStringAsync()).trim();
        if (/^https?:\/\//i.test(clip)) {
          setUrl(clip);
          setFromClipboard(true);
          return;
        }
      } catch {}
      setUrl('');
      setFromClipboard(false);
    })();
  }, [visible, existingUrl]);

  const handlePaste = async () => {
    try {
      const clip = (await Clipboard.getStringAsync()).trim();
      if (clip) { setUrl(clip); setFromClipboard(true); }
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
      <View style={styles.overlay}>
        {/* Backdrop — tap anywhere outside sheet to dismiss */}
        <TouchableWithoutFeedback onPress={onClose}>
          <View style={StyleSheet.absoluteFillObject} />
        </TouchableWithoutFeedback>

        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
          <Animated.View
            style={[styles.sheet, { paddingBottom: insets.bottom + 16 }, { transform: [{ translateY }] }]}
          >
            {/* Drag handle — drag down to dismiss */}
            <View {...panResponder.panHandlers} style={styles.handleArea}>
              <View style={styles.handle} />
            </View>

            <Text style={styles.title}>Save Official URL</Text>
            <Text style={styles.subtitle} numberOfLines={2}>{boardName}</Text>

            {fromClipboard && (
              <View style={styles.clipTag}>
                <Text style={styles.clipTagTxt}>📋 Auto-pasted from clipboard</Text>
              </View>
            )}

            <Text style={styles.hint}>
              Open the board in Safari, copy the URL from the address bar, and paste it below.
            </Text>

            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={url}
                onChangeText={(t) => { setUrl(t); setFromClipboard(false); }}
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
          </Animated.View>
        </KeyboardAvoidingView>
      </View>
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
    gap: 10,
  },
  handleArea: {
    alignItems: 'center',
    paddingTop: 14,
    paddingBottom: 10,
  },
  handle: {
    width: 40, height: 5, borderRadius: 3,
    backgroundColor: '#C7C7CC',
  },
  title: { fontSize: 17, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 13, color: '#8E8E93', marginTop: -4 },
  clipTag: {
    backgroundColor: '#E8F5E9', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 5,
  },
  clipTagTxt: { fontSize: 12, color: '#1C1C1E', fontWeight: '500', lineHeight: 16 },
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
