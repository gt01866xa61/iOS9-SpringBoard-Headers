import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Motherboard } from '../models/Motherboard';
import { VisitStatus } from '../hooks/useVisitedBoards';

interface Props {
  board: Motherboard;
  hasSaved: boolean;
  visitStatus?: VisitStatus;
  size?: 'normal' | 'compact';
}

// Single source of truth for which badges show on a board, in what color, and
// in what priority. Used by every screen that lists boards so the UI never
// drifts out of sync. New states/colors → change here, every list updates.
export function BoardBadges({ board, hasSaved, visitStatus, size = 'normal' }: Props) {
  const status =
    visitStatus === 'wrong' && hasSaved ? 'FIXED' :
    visitStatus === 'wrong'             ? 'WRONG' :
    visitStatus === 'confirmed'         ? 'SEEN'  :
    hasSaved                            ? 'URL'   : null;

  const s = size === 'compact' ? compactStyles : normalStyles;

  return (
    <>
      {board.isCustom && (
        <View style={s.customBadge}><Text style={s.customBadgeTxt}>Custom</Text></View>
      )}
      {status === 'FIXED' && (
        <View style={s.fixedBadge}><Text style={s.fixedBadgeTxt}>FIXED</Text></View>
      )}
      {status === 'WRONG' && (
        <View style={s.wrongBadge}><Text style={s.wrongBadgeTxt}>WRONG</Text></View>
      )}
      {status === 'SEEN' && (
        <View style={s.seenBadge}><Text style={s.seenBadgeTxt}>SEEN</Text></View>
      )}
      {status === 'URL' && (
        <View style={s.savedBadge}><Text style={s.savedBadgeTxt}>URL</Text></View>
      )}
    </>
  );
}

const normalStyles = StyleSheet.create({
  customBadge: { backgroundColor: '#FFF3CD', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  customBadgeTxt: { fontSize: 10, color: '#856404', fontWeight: '700' },
  savedBadge: { backgroundColor: '#E8F5E9', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  savedBadgeTxt: { fontSize: 10, color: '#2E7D32', fontWeight: '700' },
  seenBadge: { backgroundColor: '#DBEAFE', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  seenBadgeTxt: { fontSize: 10, color: '#1D4ED8', fontWeight: '700' },
  fixedBadge: { backgroundColor: '#FFF7ED', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  fixedBadgeTxt: { fontSize: 10, color: '#C2410C', fontWeight: '700' },
  wrongBadge: { backgroundColor: '#FEF2F2', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  wrongBadgeTxt: { fontSize: 10, color: '#DC2626', fontWeight: '700' },
});

const compactStyles = StyleSheet.create({
  customBadge: { backgroundColor: '#FFF3CD', borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  customBadgeTxt: { fontSize: 8, color: '#856404', fontWeight: '700' },
  savedBadge: { backgroundColor: '#E8F5E9', borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  savedBadgeTxt: { fontSize: 8, color: '#2E7D32', fontWeight: '700' },
  seenBadge: { backgroundColor: '#DBEAFE', borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  seenBadgeTxt: { fontSize: 8, color: '#1D4ED8', fontWeight: '700' },
  fixedBadge: { backgroundColor: '#FFF7ED', borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  fixedBadgeTxt: { fontSize: 8, color: '#C2410C', fontWeight: '700' },
  wrongBadge: { backgroundColor: '#FEF2F2', borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  wrongBadgeTxt: { fontSize: 8, color: '#DC2626', fontWeight: '700' },
});
