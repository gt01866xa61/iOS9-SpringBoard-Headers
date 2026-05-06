import type { Task } from '../types/Task'
import { PRIORITY_LABEL } from '../types/Task'
import { PRIORITY_COLOR, STATUS_COLOR } from '../lib/seed'

interface Props {
  task: Task
  onEdit: () => void
  onDelete: () => void
}

function dueLabel(due?: string): { text: string; className: string } | null {
  if (!due) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const d = new Date(due + 'T00:00:00')
  const diff = Math.round((d.getTime() - today.getTime()) / 86400000)
  let text = due
  let className = 'text-zinc-500'
  if (diff < 0) {
    text = `逾期 ${-diff}d`
    className = 'text-red-600 font-semibold'
  } else if (diff === 0) {
    text = '今天到期'
    className = 'text-red-600 font-semibold'
  } else if (diff <= 7) {
    text = `剩 ${diff}d`
    className = 'text-amber-600 font-medium'
  }
  return { text, className }
}

export function TaskCard({ task, onEdit, onDelete }: Props) {
  const due = dueLabel(task.dueDate)
  const statusClass = STATUS_COLOR[task.status] ?? 'bg-zinc-100 text-zinc-700 border-zinc-200'

  return (
    <article className="group rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4 shadow-sm hover:shadow transition">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-medium text-zinc-900 dark:text-zinc-100 leading-snug flex-1">
          {task.title}
        </h3>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
          <button
            type="button"
            onClick={onEdit}
            className="rounded px-2 py-1 text-xs text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            編輯
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            刪除
          </button>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
        <span className={`rounded border px-2 py-0.5 ${statusClass}`}>{task.status}</span>
        <span className={`rounded px-2 py-0.5 ${PRIORITY_COLOR[task.priority]}`}>
          {PRIORITY_LABEL[task.priority]}
        </span>
        {task.ownerOrg && (
          <span className="rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 px-2 py-0.5">
            @{task.ownerOrg}
          </span>
        )}
        {task.product && (
          <span className="rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 px-2 py-0.5 font-mono">
            {task.product}
          </span>
        )}
        {task.quantity && (
          <span className="text-zinc-500 dark:text-zinc-400">{task.quantity}</span>
        )}
        {task.tempCondition && (
          <span className="text-zinc-500 dark:text-zinc-400">· {task.tempCondition}</span>
        )}
        {due && <span className={`ml-auto ${due.className}`}>{due.text}</span>}
      </div>

      {task.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {task.tags.map((t) => (
            <span
              key={t}
              className="rounded bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 text-xs"
            >
              #{t}
            </span>
          ))}
        </div>
      )}

      {task.notes && (
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap">
          {task.notes}
        </p>
      )}
    </article>
  )
}
