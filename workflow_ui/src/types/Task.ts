export type Priority = 'high' | 'medium' | 'low'

export interface Task {
  id: string
  title: string
  status: string
  priority: Priority
  ownerOrg?: string
  product?: string
  quantity?: string
  tempCondition?: string
  dueDate?: string
  tags: string[]
  notes?: string
  createdAt: string
  updatedAt: string
}

export interface OptionStore {
  status: string[]
  ownerOrg: string[]
  product: string[]
  tempCondition: string[]
  tags: string[]
}

export type OptionField = keyof OptionStore

export interface AppState {
  tasks: Task[]
  options: OptionStore
  version: number
}

export const PRIORITY_LABEL: Record<Priority, string> = {
  high: '高',
  medium: '中',
  low: '低',
}
