import { useEffect, useState } from 'react'
import type { OptionStore, Priority, Task } from '../types/Task'
import type { TaskDraft } from '../hooks/useStore'
import { ComboInput } from './ComboInput'
import { TagsInput } from './TagsInput'

interface Props {
  open: boolean
  initial?: Task
  options: OptionStore
  onCancel: () => void
  onSubmit: (draft: TaskDraft) => void
}

const emptyDraft = (status: string): TaskDraft => ({
  title: '',
  status,
  priority: 'medium',
  ownerOrg: '',
  product: '',
  quantity: '',
  tempCondition: '',
  dueDate: '',
  tags: [],
  notes: '',
})

export function TaskFormModal({ open, initial, options, onCancel, onSubmit }: Props) {
  const [draft, setDraft] = useState<TaskDraft>(() =>
    initial
      ? { ...initial }
      : emptyDraft(options.status[0] ?? '進行中'),
  )

  useEffect(() => {
    if (open) {
      setDraft(initial ? { ...initial } : emptyDraft(options.status[0] ?? '進行中'))
    }
  }, [open, initial, options.status])

  if (!open) return null

  const set = <K extends keyof TaskDraft>(key: K, val: TaskDraft[K]) =>
    setDraft((d) => ({ ...d, [key]: val }))

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft.title.trim() || !draft.status.trim()) return
    onSubmit({
      ...draft,
      title: draft.title.trim(),
      status: draft.status.trim(),
      ownerOrg: draft.ownerOrg?.trim() || undefined,
      product: draft.product?.trim() || undefined,
      quantity: draft.quantity?.trim() || undefined,
      tempCondition: draft.tempCondition?.trim() || undefined,
      dueDate: draft.dueDate || undefined,
      notes: draft.notes?.trim() || undefined,
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div className="w-full max-w-2xl rounded-lg bg-white dark:bg-zinc-900 shadow-xl">
        <header className="border-b border-zinc-200 dark:border-zinc-800 px-6 py-4">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            {initial ? '編輯工作' : '新增工作'}
          </h2>
        </header>
        <form onSubmit={submit}>
          <div className="grid grid-cols-2 gap-4 px-6 py-5">
            <Field label="標題" colSpan>
              <input
                type="text"
                value={draft.title}
                onChange={(e) => set('title', e.target.value)}
                required
                autoFocus
                className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </Field>

            <Field label="狀態">
              <ComboInput
                value={draft.status}
                onChange={(v) => set('status', v)}
                options={options.status}
                required
              />
            </Field>

            <Field label="優先">
              <select
                value={draft.priority}
                onChange={(e) => set('priority', e.target.value as Priority)}
                className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm"
              >
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </Field>

            <Field label="負責單位">
              <ComboInput
                value={draft.ownerOrg ?? ''}
                onChange={(v) => set('ownerOrg', v)}
                options={options.ownerOrg}
              />
            </Field>

            <Field label="產品/料號">
              <ComboInput
                value={draft.product ?? ''}
                onChange={(v) => set('product', v)}
                options={options.product}
              />
            </Field>

            <Field label="數量">
              <input
                type="text"
                value={draft.quantity ?? ''}
                onChange={(e) => set('quantity', e.target.value)}
                placeholder="例: 100pcs / 5K"
                className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm"
              />
            </Field>

            <Field label="溫度條件">
              <ComboInput
                value={draft.tempCondition ?? ''}
                onChange={(v) => set('tempCondition', v)}
                options={options.tempCondition}
              />
            </Field>

            <Field label="預計交期">
              <input
                type="date"
                value={draft.dueDate ?? ''}
                onChange={(e) => set('dueDate', e.target.value)}
                className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm"
              />
            </Field>

            <Field label="標籤" colSpan>
              <TagsInput
                value={draft.tags}
                onChange={(tags) => set('tags', tags)}
                suggestions={options.tags}
              />
            </Field>

            <Field label="備註" colSpan>
              <textarea
                value={draft.notes ?? ''}
                onChange={(e) => set('notes', e.target.value)}
                rows={3}
                className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </Field>
          </div>

          <footer className="flex justify-end gap-2 border-t border-zinc-200 dark:border-zinc-800 px-6 py-3">
            <button
              type="button"
              onClick={onCancel}
              className="rounded border border-zinc-300 dark:border-zinc-700 px-4 py-1.5 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-800"
            >
              取消
            </button>
            <button
              type="submit"
              className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              儲存
            </button>
          </footer>
        </form>
      </div>
    </div>
  )
}

function Field({
  label,
  colSpan,
  children,
}: {
  label: string
  colSpan?: boolean
  children: React.ReactNode
}) {
  return (
    <label className={`flex flex-col gap-1 ${colSpan ? 'col-span-2' : ''}`}>
      <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{label}</span>
      {children}
    </label>
  )
}
