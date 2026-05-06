import { useState } from 'react'
import { useStore, type TaskDraft } from './hooks/useStore'
import type { Task } from './types/Task'
import { TaskFormModal } from './components/TaskFormModal'
import { TaskList } from './components/TaskList'

function App() {
  const { state, addTask, updateTask, deleteTask, addOption } = useStore()
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Task | null>(null)

  const openAdd = () => {
    setEditing(null)
    setModalOpen(true)
  }

  const openEdit = (t: Task) => {
    setEditing(t)
    setModalOpen(true)
  }

  const handleSubmit = (draft: TaskDraft) => {
    addOption('status', draft.status)
    if (draft.ownerOrg) addOption('ownerOrg', draft.ownerOrg)
    if (draft.product) addOption('product', draft.product)
    if (draft.tempCondition) addOption('tempCondition', draft.tempCondition)
    draft.tags.forEach((t) => addOption('tags', t))

    if (editing) {
      updateTask(editing.id, draft)
    } else {
      addTask(draft)
    }
    setModalOpen(false)
  }

  const handleDelete = (id: string) => {
    if (confirm('確定刪除這筆工作？')) deleteTask(id)
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <h1 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            工作流 <span className="text-zinc-400 font-normal">/ workflow</span>
          </h1>
          <div className="flex items-center gap-3">
            <span className="text-xs text-zinc-500">{state.tasks.length} 筆</span>
            <button
              type="button"
              onClick={openAdd}
              className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              + 新增工作
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6">
        <TaskList tasks={state.tasks} onEdit={openEdit} onDelete={handleDelete} />
      </main>

      <TaskFormModal
        open={modalOpen}
        initial={editing ?? undefined}
        options={state.options}
        onCancel={() => setModalOpen(false)}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

export default App
