import { useState, useEffect } from 'react'
import { getTodos, createTodo, updateTodo, deleteTodo } from './api'
import AddTodo from './components/AddTodo'
import TodoList from './components/TodoList'
import KanbanBoard from './components/KanbanBoard'

export default function App() {
  const [todos, setTodos] = useState([])
  const [error, setError] = useState(null)
  const [view, setView] = useState('list')

  useEffect(() => {
    getTodos()
      .then(setTodos)
      .catch(() => setError('Failed to load todos.'))
  }, [])

  async function handleAdd(title) {
    try {
      const created = await createTodo(title)
      setTodos((prev) => [created, ...prev])
    } catch {
      setError('Failed to add todo.')
    }
  }

  async function handleUpdate(id, fields) {
    try {
      const updated = await updateTodo(id, fields)
      setTodos((prev) => prev.map((t) => (t.id === id ? updated : t)))
    } catch {
      setError('Failed to update todo.')
    }
  }

  async function handleDelete(id) {
    try {
      await deleteTodo(id)
      setTodos((prev) => prev.filter((t) => t.id !== id))
    } catch {
      setError('Failed to delete todo.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className={`mx-auto w-full transition-all duration-300 ${view === 'list' ? 'max-w-md' : 'max-w-5xl'}`}>

        <h1 className="text-2xl font-semibold text-gray-800 mb-2 text-center">
          My Todos
        </h1>

        {/* View Switcher Toggle */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex rounded-lg bg-gray-200 p-0.5" role="group">
            <button
              onClick={() => setView('list')}
              className={`rounded-md px-4 py-1.5 text-xs font-medium transition-colors
                          ${view === 'list'
                            ? 'bg-white text-gray-800 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                          }`}
            >
              List View
            </button>
            <button
              onClick={() => setView('board')}
              className={`rounded-md px-4 py-1.5 text-xs font-medium transition-colors
                          ${view === 'board'
                            ? 'bg-white text-gray-800 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                          }`}
            >
              Board View
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-2
                          text-sm text-red-700 flex justify-between items-center">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-400 hover:text-red-600"
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        <div className="mb-4">
          <AddTodo onAdd={handleAdd} />
        </div>

        {view === 'list' ? (
          <TodoList
            todos={todos}
            onUpdate={handleUpdate}
            onDelete={handleDelete}
          />
        ) : (
          <KanbanBoard
            todos={todos}
            onUpdate={handleUpdate}
            onDelete={handleDelete}
          />
        )}

        {todos.length > 0 && (
          <p className="mt-4 text-center text-xs text-gray-400">
            {todos.filter((t) => t.completed).length} / {todos.length} completed
          </p>
        )}
      </div>
    </div>
  )
}
