import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import WebView, { WebViewNavigation, WebViewErrorEvent, WebViewHttpErrorEvent } from 'react-native-webview';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/types';
import { useSavedUrls } from '../hooks/useSavedUrls';
import { useVisitedBoards } from '../hooks/useVisitedBoards';

type Props = NativeStackScreenProps<RootStackParamList, 'Browser'>;

function normalizeUrl(raw: string): string {
  const t = raw.trim();
  return /^https?:\/\//i.test(t) ? t : `https://${t}`;
}

export function BrowserScreen({ route, navigation }: Props) {
  const { board, initialUrl } = route.params;
  const insets = useSafeAreaInsets();
  const { saveUrl } = useSavedUrls();
  const { markConfirmed } = useVisitedBoards();
  const webViewRef = useRef<WebView>(null);

  const safeUrl = normalizeUrl(initialUrl);
  // sourceUrl drives the WebView; updating it causes the WebView to navigate.
  const [sourceUrl, setSourceUrl] = useState(safeUrl);
  const [currentUrl, setCurrentUrl] = useState(safeUrl);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const handleNavigationStateChange = useCallback((state: WebViewNavigation) => {
    if (state.url) setCurrentUrl(state.url);
  }, []);

  const handleLoadStart = useCallback(() => {
    setIsLoading(true);
    setLoadError(null);
  }, []);

  const handleError = useCallback((e: WebViewErrorEvent) => {
    setIsLoading(false);
    setLoadError(e.nativeEvent.description || '無法載入頁面');
  }, []);

  const handleHttpError = useCallback((e: WebViewHttpErrorEvent) => {
    setIsLoading(false);
    setLoadError(`頁面回傳錯誤 (HTTP ${e.nativeEvent.statusCode})`);
  }, []);

  const handleStop = useCallback(() => {
    webViewRef.current?.stopLoading();
    setIsLoading(false);
  }, []);

  const handleSave = useCallback(() => {
    saveUrl(board.id, currentUrl);
    markConfirmed(board.id);
    setSaved(true);
  }, [board.id, currentUrl, saveUrl, markConfirmed]);

  const handleManualUrl = useCallback(() => {
    Alert.prompt(
      '手動輸入網址',
      '貼上或輸入規格頁面的完整 URL',
      (text) => {
        if (!text?.trim()) return;
        const url = normalizeUrl(text.trim());
        setSourceUrl(url);
        setCurrentUrl(url);
        setLoadError(null);
        setIsLoading(true);
      },
      'plain-text',
      currentUrl,
    );
  }, [currentUrl]);

  const displayHost = (() => {
    try { return new URL(currentUrl).hostname; }
    catch { return currentUrl; }
  })();

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Top bar — sits ABOVE the overlay layer so it's always tappable */}
      <View style={styles.bar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeBtn} hitSlop={8}>
          <Text style={styles.closeTxt}>✕</Text>
        </TouchableOpacity>

        <Text style={styles.urlTxt} numberOfLines={1}>{displayHost}</Text>

        {isLoading && !loadError ? (
          <TouchableOpacity onPress={handleStop} style={styles.stopBtn} hitSlop={8}>
            <Text style={styles.stopTxt}>⏹ 停止</Text>
          </TouchableOpacity>
        ) : (
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
        )}
      </View>

      {/* WebView area — overlays live here, never extend into the top bar */}
      <View style={styles.webviewArea}>
        <WebView
          ref={webViewRef}
          source={{ uri: sourceUrl }}
          onNavigationStateChange={handleNavigationStateChange}
          onLoadStart={handleLoadStart}
          onLoadEnd={() => setIsLoading(false)}
          onError={handleError}
          onHttpError={handleHttpError}
          style={styles.webview}
        />

        {isLoading && !loadError && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color="#007AFF" />
          </View>
        )}

        {loadError && (
          <View style={styles.errorOverlay}>
            <Text style={styles.errorIcon}>🌐</Text>
            <Text style={styles.errorTitle}>無法載入頁面</Text>
            <Text style={styles.errorDesc}>{loadError}</Text>
            <Text style={styles.errorUrl} numberOfLines={2}>{currentUrl}</Text>
            <View style={styles.errorBtns}>
              <TouchableOpacity
                style={styles.retryBtn}
                onPress={() => { setLoadError(null); setIsLoading(true); webViewRef.current?.reload(); }}
              >
                <Text style={styles.retryTxt}>重試</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.manualBtn} onPress={handleManualUrl}>
                <Text style={styles.manualTxt}>手動輸入</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
                <Text style={styles.backTxt}>關閉</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
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

  stopBtn: { backgroundColor: '#F2F2F7', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  stopTxt: { fontSize: 12, color: '#FF3B30', fontWeight: '700' },

  saveBtn: { backgroundColor: '#007AFF', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  saveBtnDone: { backgroundColor: '#34C759' },
  saveTxt: { fontSize: 12, color: '#fff', fontWeight: '700' },
  saveTxtDone: { color: '#fff' },

  webviewArea: { flex: 1 },
  webview: { flex: 1 },

  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.85)',
  },

  errorOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 28,
    gap: 10,
  },
  errorIcon: { fontSize: 48 },
  errorTitle: { fontSize: 18, fontWeight: '700', color: '#1C1C1E' },
  errorDesc: { fontSize: 13, color: '#8E8E93', textAlign: 'center' },
  errorUrl: { fontSize: 11, color: '#AEAEB2', textAlign: 'center', marginTop: 4 },
  errorBtns: { flexDirection: 'row', gap: 8, marginTop: 8, flexWrap: 'wrap', justifyContent: 'center' },
  retryBtn: { backgroundColor: '#007AFF', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 10 },
  retryTxt: { color: '#fff', fontWeight: '700', fontSize: 14 },
  manualBtn: { backgroundColor: '#FF9F0A', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 10 },
  manualTxt: { color: '#fff', fontWeight: '700', fontSize: 14 },
  backBtn: { backgroundColor: '#E5E5EA', borderRadius: 10, paddingHorizontal: 18, paddingVertical: 10 },
  backTxt: { color: '#1C1C1E', fontWeight: '600', fontSize: 14 },
});
