import { useState, useRef, useEffect } from 'react'

function KanbanCard({ todo, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(todo.title)
  const inputRef = useRef(null)

  useEffect(() => {
    if (isEditing) inputRef.current?.focus()
  }, [isEditing])

  function startEdit() {
    setDraft(todo.title)
    setIsEditing(true)
  }

  function cancelEdit() {
    setDraft(todo.title)
    setIsEditing(false)
  }

  function saveEdit() {
    const trimmed = draft.trim()
    if (!trimmed) { cancelEdit(); return }
    if (trimmed !== todo.title) onUpdate(todo.id, { title: trimmed })
    setIsEditing(false)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') saveEdit()
    if (e.key === 'Escape') cancelEdit()
  }

  const handleDragStart = (e) => {
    e.dataTransfer.setData('text/plain', String(todo.id))
    e.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className="flex items-center gap-3 rounded-lg bg-white p-3 border border-gray-200
                 shadow-sm cursor-grab active:cursor-grabbing hover:shadow transition-shadow"
    >
      {/* Draggable indicator dots icon */}
      <div className="text-gray-400 select-none flex-shrink-0" title="Drag to reorder">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 6a2 2 0 11-4 0 2 2 0 014 0zM8 12a2 2 0 11-4 0 2 2 0 014 0zM8 18a2 2 0 11-4 0 2 2 0 014 0zM14 6a2 2 0 11-4 0 2 2 0 014 0zM14 12a2 2 0 11-4 0 2 2 0 014 0zM14 18a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      </div>

      {/* Card Content */}
      <div className="flex-1 min-w-0">
        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={saveEdit}
            onKeyDown={handleKeyDown}
            className="w-full rounded border border-blue-400 px-2 py-0.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        ) : (
          <span
            onClick={startEdit}
            title="Click to edit"
            className={`block text-sm cursor-pointer select-none truncate
                        ${todo.completed ? 'line-through text-gray-400' : 'text-gray-800'}`}
          >
            {todo.title}
          </span>
        )}
      </div>

      {/* Delete Button */}
      <button
        onClick={() => onDelete(todo.id)}
        aria-label="Delete todo"
        className="text-gray-400 hover:text-red-500 transition-colors text-lg
                   leading-none flex-shrink-0"
      >
        ×
      </button>
    </div>
  )
}

export default function KanbanBoard({ todos, onUpdate, onDelete }) {
  const [activeOver, setActiveOver] = useState(null)

  const columns = [
    { id: 'todo', title: 'To Do', bg: 'bg-gray-100/80', text: 'text-gray-600', border: 'border-gray-200' },
    { id: 'in_progress', title: 'In Progress', bg: 'bg-blue-50/50', text: 'text-blue-700', border: 'border-blue-100' },
    { id: 'done', title: 'Done', bg: 'bg-green-50/50', text: 'text-green-700', border: 'border-green-100' },
  ]

  const handleDragOver = (e, colId) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (activeOver !== colId) {
      setActiveOver(colId)
    }
  }

  const handleDragLeave = () => {
    // Note: drag leave can be triggered by nested elements, but simple visual cleanup is fine
  }

  const handleDrop = (e, targetStatus) => {
    e.preventDefault()
    setActiveOver(null)
    const idStr = e.dataTransfer.getData('text/plain')
    const id = Number(idStr)
    if (!id) return

    const todo = todos.find((t) => t.id === id)
    if (todo && todo.status !== targetStatus) {
      onUpdate(id, { status: targetStatus })
    }
  }

  const getColTodos = (colId) => {
    return todos.filter((t) => {
      const s = t.status || (t.completed ? 'done' : 'todo')
      return s === colId
    })
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
      {columns.map((col) => {
        const colTodos = getColTodos(col.id)
        const isHovered = activeOver === col.id

        return (
          <div
            key={col.id}
            onDragOver={(e) => handleDragOver(e, col.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, col.id)}
            className={`flex flex-col rounded-xl p-4 min-h-[450px] border-2 transition-colors duration-200
                        ${col.bg} ${isHovered ? 'border-dashed border-blue-400 bg-blue-100/30' : col.border}`}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-200">
              <h2 className={`font-semibold text-sm tracking-wide uppercase ${col.text}`}>
                {col.title}
              </h2>
              <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold shadow-sm border border-gray-100 text-gray-500">
                {colTodos.length}
              </span>
            </div>

            {/* Cards Container */}
            <div className="flex flex-col gap-3 flex-1 overflow-y-auto">
              {colTodos.map((todo) => (
                <KanbanCard
                  key={todo.id}
                  todo={todo}
                  onUpdate={onUpdate}
                  onDelete={onDelete}
                />
              ))}

              {colTodos.length === 0 && (
                <div className="flex flex-col items-center justify-center py-12 px-4 rounded-lg border border-dashed border-gray-300 text-gray-400 text-xs text-center flex-1">
                  Drag tasks here
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
