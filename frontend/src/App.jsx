import { useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'
import Login from './Login'
import Dashboard from './Dashboard'

export default function App() {
  const [me, setMe] = useState(null)
  const [checking, setChecking] = useState(!!getToken())

  useEffect(() => {
    if (!getToken()) return
    api('/me').then(setMe).catch(() => setToken('')).finally(() => setChecking(false))
  }, [])

  if (checking) return <div style={{ padding: 16 }}>loading...</div>
  if (!me) return <Login onDone={() => api('/me').then(setMe)} />

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 16px', background: '#1f2937', color: '#fff' }}>
        <b>Log Management</b>
        <span>
          {me.username} ({me.role}){' '}
          <button onClick={() => { setToken(''); setMe(null) }}>logout</button>
        </span>
      </div>
      <Dashboard me={me} />
    </div>
  )
}