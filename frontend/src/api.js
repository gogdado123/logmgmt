let token = localStorage.getItem('token') || ''

export const getToken = () => token
export const setToken = (t) => {
  token = t
  if (t) localStorage.setItem('token', t)
  else localStorage.removeItem('token')
}

export async function api(path, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== '' && v != null)
  ).toString()
  const res = await fetch(`/api${path}${qs ? '?' + qs : ''}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 401) {
    setToken('')
    window.location.reload()
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function login(username, password) {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
  const data = await res.json()
  setToken(data.access_token)
  return data
}