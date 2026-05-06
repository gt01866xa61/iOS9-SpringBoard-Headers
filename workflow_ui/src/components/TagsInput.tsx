import { useState, type KeyboardEvent } from 'react'

interface Props {
  value: string[]
  onChange: (tags: string[]) => void
  suggestions: string[]
}

export function TagsInput({ value, onChange, suggestions }: Props) {
  const [draft, setDraft] = useState('')

  const add = (raw: string) => {
    const v = raw.trim()
    if (!v) return
    if (value.includes(v)) {
      setDraft('')
      return
    }
    onChange([...value, v])
    setDraft('')
  }

  const remove = (t: string) => onChange(value.filter((v) => v !== t))

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      add(draft)
    } else if (e.key === 'Backspace' && !draft && value.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  const remaining = suggestions.filter((s) => !value.includes(s))

  return (
    <div>
      <div className="flex flex-wrap items-center gap-1 rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 min-h-[2.25rem]">
        {value.map((t) => (
          <span
            key={t}
            className="inline-flex items-center gap-1 rounded bg-indigo-100 dark:bg-indigo-900/40 text-indigo-800 dark:text-indigo-200 px-2 py-0.5 text-xs"
          >
            {t}
            <button
              type="button"
              onClick={() => remove(t)}
              className="text-indigo-500 hover:text-indigo-700"
              aria-label={`移除 ${t}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          list="tag-suggestions"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKey}
          onBlur={() => add(draft)}
          placeholder={value.length === 0 ? '輸入後按 Enter' : ''}
          className="flex-1 min-w-[6rem] bg-transparent text-sm py-1 focus:outline-none"
        />
        <datalist id="tag-suggestions">
          {remaining.map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>
      </div>
    </div>
  )
}
