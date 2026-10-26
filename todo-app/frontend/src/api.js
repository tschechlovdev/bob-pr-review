const BASE = '/api/todos'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) throw new Error(data.error ?? 'Request failed')
  return data
}

export const getTodos = () => request(BASE)

export const createTodo = (title) =>
  request(BASE, { method: 'POST', body: JSON.stringify({ title }) })

export const updateTodo = (id, fields) =>
  request(`${BASE}/${id}`, { method: 'PUT', body: JSON.stringify(fields) })

export const deleteTodo = (id) =>
  request(`${BASE}/${id}`, { method: 'DELETE' })

export const getComments = (id) => request(`${BASE}/${id}/comments`)

export const addComment = (id, author, body) =>
  request(`${BASE}/${id}/comments`, {
    method: 'POST',
    body: JSON.stringify({ author, body }),
  })

export const getAttachments = (id) => request(`${BASE}/${id}/attachments`)

export async function uploadAttachment(id, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/${id}/attachments`, { method: 'POST', body: form })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error ?? 'Upload failed')
  return data
}

export const attachmentUrl = (filename) => `${BASE}/attachments/download/${filename}`
