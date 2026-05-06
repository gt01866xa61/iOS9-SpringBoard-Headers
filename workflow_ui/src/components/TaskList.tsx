import type { Task } from '../types/Task'
import { TaskCard } from './TaskCard'

interface Props {
  tasks: Task[]
  onEdit: (t: Task) => void
  onDelete: (id: string) => void
}

export function TaskList({ tasks, onEdit, onDelete }: Props) {
  if (tasks.length === 0) {
    return (
      <div className="mx-auto max-w-md rounded-lg border border-dashed border-zinc-300 dark:border-zinc-700 p-12 text-center text-sm text-zinc-500">
        還沒有工作。點右上「+ 新增工作」開始。
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
      {tasks.map((t) => (
        <TaskCard
          key={t.id}
          task={t}
          onEdit={() => onEdit(t)}
          onDelete={() => onDelete(t.id)}
        />
      ))}
    </div>
  )
}
