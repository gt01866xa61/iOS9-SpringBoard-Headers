import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = 'saved_urls_v1';

export async function getSavedUrls(): Promise<Record<string, string>> {
  const raw = await AsyncStorage.getItem(KEY);
  return raw ? JSON.parse(raw) : {};
}

export async function saveUrl(boardId: string, url: string): Promise<void> {
  const current = await getSavedUrls();
  current[boardId] = url;
  await AsyncStorage.setItem(KEY, JSON.stringify(current));
}

export async function removeUrl(boardId: string): Promise<void> {
  const current = await getSavedUrls();
  delete current[boardId];
  await AsyncStorage.setItem(KEY, JSON.stringify(current));
}
