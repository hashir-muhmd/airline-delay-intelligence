export const API_BASE = 'http://localhost:8000'

export async function fetchJSON(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`)
  }
  return res.json()
}