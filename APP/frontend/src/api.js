const BASE = 'http://localhost:8000/api'

export async function getStats(db = 'isic2020') {
  const r = await fetch(`${BASE}/stats?db=${db}`)
  return r.json()
}

export async function searchImage(file, top_k = 10, db = 'isic2020', token = null) {
  const fd = new FormData()
  fd.append('file', file)
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const r = await fetch(`${BASE}/search?top_k=${top_k}&db=${db}`, { method: 'POST', body: fd, headers })
  return r.json()
}

export async function getMetadata(id, db = 'isic2020') {
  const r = await fetch(`${BASE}/metadata/${id}?db=${db}`)
  return r.json()
}

export async function getMessages() {
  const r = await fetch(`${BASE}/messages`)
  return r.json()
}

export async function markMessageRead(id) {
  await fetch(`${BASE}/messages/${id}/read`, { method: 'PATCH' })
}
