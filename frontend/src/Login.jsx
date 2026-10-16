import { useState } from 'react'
import { login } from './api'

export default function Login({ onDone }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    try {
      const data = await login(username, password)
      onDone(data)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form onSubmit={submit} style={{ maxWidth: 320, margin: '15vh auto', display: 'grid', gap: 12 }}>
      <h2>Log Management</h2>
      <input placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Login</button>
      {error && <div style={{ color: 'crimson' }}>{error}</div>}
    </form>
  )
}