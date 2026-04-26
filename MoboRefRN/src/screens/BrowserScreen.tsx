import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import WebView, { WebViewNavigation } from 'react-native-webview';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/types';
import { useSavedUrls } from '../hooks/useSavedUrls';
import { useVisitedBoards } from '../hooks/useVisitedBoards';

type Props = NativeStackScreenProps<RootStackParamList, 'Browser'>;

export function BrowserScreen({ route, navigation }: Props) {
  const { board, initialUrl } = route.params;
  const insets = useSafeAreaInsets();
  const { saveUrl } = useSavedUrls();
  const { markConfirmed } = useVisitedBoards();

  const [currentUrl, setCurrentUrl] = useState(initialUrl);
  const [isLoading, setIsLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleNavigationStateChange = useCallback((state: WebViewNavigation) => {
    if (state.url) setCurrentUrl(state.url);
  }, []);

  const handleSave = useCallback(() => {
    saveUrl(board.id, currentUrl);
    markConfirmed(board.id);
    setSaved(true);
  }, [board.id, currentUrl, saveUrl, markConfirmed]);

  const displayHost = (() => {
    try {
      return new URL(currentUrl).hostname;
    } catch {
      return currentUrl;
    }
  })();

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Top bar */}
      <View style={styles.bar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeBtn} hitSlop={8}>
          <Text style={styles.closeTxt}>✕</Text>
        </TouchableOpacity>

        <Text style={styles.urlTxt} numberOfLines={1}>{displayHost}</Text>

        <TouchableOpacity
          onPress={handleSave}
          disabled={saved}
          style={[styles.saveBtn, saved && styles.saveBtnDone]}
          hitSlop={8}
        >
          <Text style={[styles.saveTxt, saved && styles.saveTxtDone]}>
            {saved ? '✓ Saved' : '📌 Save as Spec'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* WebView */}
      <WebView
        source={{ uri: initialUrl }}
        onNavigationStateChange={handleNavigationStateChange}
        onLoadStart={() => setIsLoading(true)}
        onLoadEnd={() => setIsLoading(false)}
        style={styles.webview}
      />

      {isLoading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },

  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: '#E5E5EA',
    backgroundColor: '#fff',
    gap: 8,
  },
  closeBtn: { padding: 4 },
  closeTxt: { fontSize: 16, color: '#8E8E93', fontWeight: '600' },

  urlTxt: { flex: 1, fontSize: 13, color: '#3C3C43', textAlign: 'center' },

  saveBtn: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  saveBtnDone: { backgroundColor: '#34C759' },
  saveTxt: { fontSize: 12, color: '#fff', fontWeight: '700' },
  saveTxtDone: { color: '#fff' },

  webview: { flex: 1 },

  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.85)',
  },
});
