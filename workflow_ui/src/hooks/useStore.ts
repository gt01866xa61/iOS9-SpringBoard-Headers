import { useCallback, useEffect, useState } from 'react'
import { nanoid } from 'nanoid'
import type { AppState, OptionField, Task } from '../types/Task'
import { SEED_OPTIONS } from '../lib/seed'

const STORAGE_KEY = 'workflow_ui:v1'
const CURRENT_VERSION = 1

const defaultState: AppState = {
  tasks: [],
  options: SEED_OPTIONS,
  version: CURRENT_VERSION,
}

function load(): AppState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultState
    const parsed = JSON.parse(raw) as Partial<AppState>
    return {
      tasks: parsed.tasks ?? [],
      options: { ...SEED_OPTIONS, ...(parsed.options ?? {}) },
      version: parsed.version ?? CURRENT_VERSION,
    }
  } catch {
    return defaultState
  }
}

function save(state: AppState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (err) {
    console.error('persist failed', err)
  }
}

export type TaskDraft = Omit<Task, 'id' | 'createdAt' | 'updatedAt'>

export function useStore() {
  const [state, setState] = useState<AppState>(load)

  useEffect(() => {
    save(state)
  }, [state])

  const addTask = useCallback((draft: TaskDraft) => {
    const now = new Date().toISOString()
    const task: Task = {
      ...draft,
      id: nanoid(8),
      createdAt: now,
      updatedAt: now,
    }
    setState((s) => ({ ...s, tasks: [task, ...s.tasks] }))
    return task
  }, [])

  const updateTask = useCallback((id: string, patch: Partial<Task>) => {
    setState((s) => ({
      ...s,
      tasks: s.tasks.map((t) =>
        t.id === id ? { ...t, ...patch, updatedAt: new Date().toISOString() } : t,
      ),
    }))
  }, [])

  const deleteTask = useCallback((id: string) => {
    setState((s) => ({ ...s, tasks: s.tasks.filter((t) => t.id !== id) }))
  }, [])

  const addOption = useCallback((field: OptionField, value: string) => {
    const v = value.trim()
    if (!v) return
    setState((s) => {
      const list = s.options[field]
      if (list.includes(v)) return s
      return { ...s, options: { ...s.options, [field]: [...list, v] } }
    })
  }, [])

  const removeOption = useCallback((field: OptionField, value: string) => {
    setState((s) => ({
      ...s,
      options: { ...s.options, [field]: s.options[field].filter((v) => v !== value) },
    }))
  }, [])

  return { state, addTask, updateTask, deleteTask, addOption, removeOption }
}
