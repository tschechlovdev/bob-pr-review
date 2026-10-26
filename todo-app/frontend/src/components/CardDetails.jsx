import { useState, useEffect } from 'react'
import {
  getComments,
  addComment,
  getAttachments,
  uploadAttachment,
  attachmentUrl,
} from '../api'

export default function CardDetails({ todo, onUpdate }) {
  const [comments, setComments] = useState([])
  const [attachments, setAttachments] = useState([])
  const [author, setAuthor] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getComments(todo.id), getAttachments(todo.id)])
      .then(([c, a]) => {
        setComments(c)
        setAttachments(a)
      })
      .catch(() => setError('Failed to load card details.'))
  }, [todo.id])

  async function submitComment(e) {
    e.preventDefault()
    if (!body.trim()) return
    try {
      const created = await addComment(todo.id, author, body)
      setComments((prev) => [...prev, created])
      setBody('')
    } catch {
      setError('Failed to add comment.')
    }
  }

  async function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const created = await uploadAttachment(todo.id, file)
      setAttachments((prev) => [...prev, created])
    } catch {
      setError('Failed to upload file.')
    }
    e.target.value = ''
  }

  return (
    <div className="mt-2 border-t border-gray-100 pt-2 text-xs space-y-3">
      {error && <p className="text-red-600">{error}</p>}

      <label className="flex items-center gap-2">
        <span className="text-gray-500">Assignee</span>
        <input
          type="text"
          defaultValue={todo.assignee ?? ''}
          onBlur={(e) => onUpdate(todo.id, { assignee: e.target.value })}
          className="flex-1 rounded border border-gray-300 px-2 py-0.5"
        />
      </label>

      <div>
        <p className="font-medium text-gray-600 mb-1">Comments</p>
        <ul className="space-y-1">
          {comments.map((c) => (
            <li key={c.id} className="rounded bg-gray-50 p-1.5">
              <span className="font-medium">{c.author}: </span>
              <span dangerouslySetInnerHTML={{ __html: c.body }} />
            </li>
          ))}
        </ul>
        <form onSubmit={submitComment} className="mt-1 flex gap-1">
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Name"
            className="w-20 rounded border border-gray-300 px-1"
          />
          <input
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Add a comment"
            className="flex-1 rounded border border-gray-300 px-1"
          />
          <button type="submit" className="rounded bg-blue-600 px-2 text-white">
            Post
          </button>
        </form>
      </div>

      <div>
        <p className="font-medium text-gray-600 mb-1">Attachments</p>
        <ul className="space-y-0.5">
          {attachments.map((a) => (
            <li key={a.id}>
              <a
                href={attachmentUrl(a.filename)}
                className="text-blue-600 underline"
              >
                {a.filename}
              </a>
            </li>
          ))}
        </ul>
        <input type="file" onChange={handleFile} className="mt-1" />
      </div>
    </div>
  )
}
