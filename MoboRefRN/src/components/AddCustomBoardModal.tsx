import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Modal,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Platform,
  KeyboardAvoidingView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Motherboard } from '../models/Motherboard';
import { buildDirectProductUrl } from '../services/URLResolverService';

const KNOWN_BRANDS = ['ASUS', 'GIGABYTE', 'MSI', 'ASRock', 'Other'];

type Step = 'form' | 'url' | 'confirm';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSave: (board: Motherboard) => void;
}

export function AddCustomBoardModal({ visible, onClose, onSave }: Props) {
  const insets = useSafeAreaInsets();

  const [step, setStep] = useState<Step>('form');
  const [brand, setBrand] = useState('ASUS');
  const [chipset, setChipset] = useState('');
  const [modelName, setModelName] = useState('');
  const [specUrl, setSpecUrl] = useState('');
  const [isFinding, setIsFinding] = useState(false);

  const reset = () => {
    setStep('form');
    setBrand('ASUS');
    setChipset('');
    setModelName('');
    setSpecUrl('');
    setIsFinding(false);
  };

  const handleClose = () => { reset(); onClose(); };

  const handleNext = async () => {
    if (!chipset.trim() || !modelName.trim()) return;
    setStep('url');
    setIsFinding(true);

    // Build the best-effort brand search / product URL
    const draft: Omit<Motherboard, 'id' | 'isCustom'> = {
      brand,
      chipset: chipset.trim().toUpperCase(),
      fullModelName: modelName.trim(),
    };
    const suggested = buildDirectProductUrl(draft as Motherboard);
    setSpecUrl(suggested);
    setIsFinding(false);
  };

  const handleSave = () => {
    const board: Motherboard = {
      id: 'c_' + Math.random().toString(36).slice(2) + Date.now().toString(36),
      brand,
      chipset: chipset.trim().toUpperCase(),
      fullModelName: modelName.trim(),
      officialSupportUrl: specUrl.trim() || undefined,
      isCustom: true,
    };
    onSave(board);
    reset();
  };

  return (
    <Modal visible={visible} animationType="slide">
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={[styles.container, { paddingTop: insets.top }]}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={handleClose}>
              <Text style={styles.cancelLink}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.title}>Add Custom Board</Text>
            <View style={{ width: 60 }} />
          </View>

          {/* Step indicators */}
          <View style={styles.steps}>
            {(['form', 'url', 'confirm'] as Step[]).map((s, i) => (
              <View key={s} style={styles.stepRow}>
                <View style={[styles.stepDot, step === s && styles.stepDotActive,
                  (step === 'url' && s === 'form') || (step === 'confirm' && s !== 'confirm') ? styles.stepDotDone : null
                ]}>
                  <Text style={[styles.stepDotTxt,
                    step === s ? styles.stepDotTxtActive : null,
                    (step === 'url' && s === 'form') || (step === 'confirm' && s !== 'confirm') ? styles.stepDotTxtDone : null
                  ]}>{i + 1}</Text>
                </View>
                {i < 2 && <View style={styles.stepLine} />}
              </View>
            ))}
          </View>

          <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">

            {/* ── Step 1: Form ── */}
            {step === 'form' && (
              <>
                <Text style={styles.sectionLabel}>BRAND</Text>
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  style={styles.brandScroll}
                  contentContainerStyle={styles.brandScrollContent}
                >
                  {KNOWN_BRANDS.map((b) => (
                    <TouchableOpacity
                      key={b}
                      style={[styles.brandPill, brand === b && styles.brandPillActive]}
                      onPress={() => setBrand(b)}
                    >
                      <Text style={[styles.brandPillTxt, brand === b && styles.brandPillTxtActive]}>
                        {b}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>

                <Text style={styles.sectionLabel}>CHIPSET</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. B650, X570, Z490"
                  value={chipset}
                  onChangeText={setChipset}
                  autoCapitalize="characters"
                  returnKeyType="next"
                />

                <Text style={styles.sectionLabel}>MODEL NAME</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. B650M C V3 (rev. 1.0)"
                  value={modelName}
                  onChangeText={setModelName}
                  returnKeyType="done"
                />

                <TouchableOpacity
                  style={[styles.primaryBtn, (!chipset.trim() || !modelName.trim()) && styles.primaryBtnDisabled]}
                  onPress={handleNext}
                  disabled={!chipset.trim() || !modelName.trim()}
                >
                  <Text style={styles.primaryBtnTxt}>Next — Find Spec Page</Text>
                </TouchableOpacity>
              </>
            )}

            {/* ── Step 2: URL ── */}
            {step === 'url' && (
              <>
                {isFinding ? (
                  <View style={styles.findingBox}>
                    <ActivityIndicator size="large" color="#007AFF" />
                    <Text style={styles.findingTxt}>Finding official page…</Text>
                  </View>
                ) : (
                  <>
                    <Text style={styles.urlHint}>
                      We found the best URL for this board. You can edit it or paste the exact spec page URL.
                    </Text>
                    <Text style={styles.sectionLabel}>SPEC / PRODUCT PAGE URL</Text>
                    <TextInput
                      style={[styles.input, styles.urlInput]}
                      value={specUrl}
                      onChangeText={setSpecUrl}
                      autoCapitalize="none"
                      autoCorrect={false}
                      keyboardType="url"
                      returnKeyType="done"
                      multiline
                    />
                    <Text style={styles.urlNote}>
                      Tip: open this URL in Safari first to verify it's the right page, then copy the final URL back here.
                    </Text>
                    <TouchableOpacity style={styles.primaryBtn} onPress={() => setStep('confirm')}>
                      <Text style={styles.primaryBtnTxt}>Next — Confirm</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.skipBtn} onPress={() => { setSpecUrl(''); setStep('confirm'); }}>
                      <Text style={styles.skipTxt}>Skip (no URL for now)</Text>
                    </TouchableOpacity>
                  </>
                )}
              </>
            )}

            {/* ── Step 3: Confirm ── */}
            {step === 'confirm' && (
              <>
                <Text style={styles.urlHint}>Review and save your custom board.</Text>

                <View style={styles.summaryCard}>
                  <Row label="Brand" value={brand} />
                  <Row label="Chipset" value={chipset.trim().toUpperCase()} />
                  <Row label="Model" value={modelName.trim()} />
                  <Row label="Spec URL" value={specUrl.trim() || '(none)'} small />
                </View>

                <TouchableOpacity style={styles.primaryBtn} onPress={handleSave}>
                  <Text style={styles.primaryBtnTxt}>Save to Catalog</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.skipBtn} onPress={() => setStep('url')}>
                  <Text style={styles.skipTxt}>← Back</Text>
                </TouchableOpacity>
              </>
            )}

          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function Row({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <View style={styles.summaryRow}>
      <Text style={styles.summaryLabel}>{label}</Text>
      <Text style={[styles.summaryValue, small && styles.summaryValueSmall]} numberOfLines={small ? 3 : 1}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#ddd',
  },
  cancelLink: { color: '#007AFF', fontSize: 16, width: 60 },
  title: { fontSize: 17, fontWeight: '700' },

  steps: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingVertical: 16, gap: 0,
  },
  stepRow: { flexDirection: 'row', alignItems: 'center' },
  stepDot: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: '#f0f0f0', justifyContent: 'center', alignItems: 'center',
  },
  stepDotActive: { backgroundColor: '#007AFF' },
  stepDotDone: { backgroundColor: '#34C759' },
  stepDotTxt: { fontSize: 13, fontWeight: '700', color: '#aaa' },
  stepDotTxtActive: { color: '#fff' },
  stepDotTxtDone: { color: '#fff' },
  stepLine: { width: 40, height: 2, backgroundColor: '#e0e0e0', marginHorizontal: 4 },

  body: { padding: 20, gap: 8 },

  sectionLabel: { fontSize: 11, color: '#8E8E93', fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.6, marginTop: 8 },

  brandScroll: { marginTop: 6, marginBottom: 4 },
  brandScrollContent: { gap: 8, paddingVertical: 4 },
  brandPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
  },
  brandPillActive: { backgroundColor: '#1C1C1E' },
  brandPillTxt: { fontSize: 14, fontWeight: '600', color: '#3C3C43' },
  brandPillTxtActive: { color: '#fff' },

  input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 10, padding: 12, fontSize: 15, backgroundColor: '#fff' },
  urlInput: { minHeight: 72, textAlignVertical: 'top' },

  primaryBtn: { backgroundColor: '#007AFF', borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginTop: 16 },
  primaryBtnDisabled: { backgroundColor: '#A8C7F0' },
  primaryBtnTxt: { color: '#fff', fontSize: 16, fontWeight: '600' },

  skipBtn: { alignItems: 'center', paddingVertical: 12 },
  skipTxt: { color: '#8E8E93', fontSize: 15 },

  findingBox: { alignItems: 'center', paddingVertical: 40, gap: 16 },
  findingTxt: { color: '#555', fontSize: 15 },

  urlHint: { fontSize: 14, color: '#555', lineHeight: 20, marginBottom: 8 },
  urlNote: { fontSize: 12, color: '#8E8E93', lineHeight: 17, marginTop: 4 },

  summaryCard: { backgroundColor: '#f9f9f9', borderRadius: 12, padding: 16, gap: 12, marginVertical: 8 },
  summaryRow: { gap: 2 },
  summaryLabel: { fontSize: 11, color: '#8E8E93', fontWeight: '600', textTransform: 'uppercase' },
  summaryValue: { fontSize: 15, color: '#111', fontWeight: '500' },
  summaryValueSmall: { fontSize: 12, color: '#555' },
});
