import { Motherboard } from '../models/Motherboard';

export type RootStackParamList = {
  Tabs: undefined;
  Browser: { board: Motherboard; initialUrl: string };
};
