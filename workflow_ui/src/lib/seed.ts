import type { OptionStore } from '../types/Task'

export const SEED_OPTIONS: OptionStore = {
  status: ['進行中', '急迫', '追蹤中', 'pending', '放置', '可拋棄'],
  ownerOrg: ['WK', '芯成', 'MT', 'FM', 'Bosh', 'Enzo', '永翰', 'vic', 'PM', '自己'],
  product: [
    'B68S',
    'N58R',
    '59XT3',
    '59XT2',
    '1136',
    'N4PA',
    '5766',
    'N38A',
    '3309EN',
    'mSATA',
    'M2 SATA',
    'UDIMM',
    'AI198L',
    '工控gen3',
  ],
  tempCondition: ['常溫', '高溫(85度)', '寬溫', 'DT'],
  tags: ['確認', '通報', '測報整理', '歸檔', '實驗', 'MP準備', 'RDT', 'CFM'],
}

export const STATUS_COLOR: Record<string, string> = {
  進行中: 'bg-blue-100 text-blue-800 border-blue-200',
  急迫: 'bg-red-100 text-red-800 border-red-200',
  追蹤中: 'bg-amber-100 text-amber-800 border-amber-200',
  pending: 'bg-zinc-100 text-zinc-700 border-zinc-200',
  放置: 'bg-zinc-100 text-zinc-500 border-zinc-200',
  可拋棄: 'bg-zinc-50 text-zinc-400 border-zinc-200 line-through',
}

export const PRIORITY_COLOR: Record<string, string> = {
  high: 'bg-red-500 text-white',
  medium: 'bg-amber-500 text-white',
  low: 'bg-zinc-400 text-white',
}
