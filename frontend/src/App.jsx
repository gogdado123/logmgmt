import { useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'
import Login from './Login'
import Dashboard from './Dashboard'
import Alerts from './Alerts'

export default function App() {
  const [me, setMe] = useState(null)
  const [checking, setChecking] = useState(!!getToken())
  const [tab, setTab] = useState('dashboard')

  useEffect(() => {
    if (!getToken()) return
    api('/me').then(setMe).catch(() => setToken('')).finally(() => setChecking(false))
  }, [])

  if (checking) return <div style={{ padding: 16 }}>loading...</div>
  if (!me) return <Login onDone={() => api('/me').then(setMe)} />

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 16px', background: '#1f2937', color: '#fff' }}>
        <span>
          <b>Log Management</b>{' '}
          <button onClick={() => setTab('dashboard')} disabled={tab === 'dashboard'}>Dashboard</button>{' '}
          <button onClick={() => setTab('alerts')} disabled={tab === 'alerts'}>Alerts</button>
        </span>
        <span>
          {me.username} ({me.role}){' '}
          <button onClick={() => { setToken(''); setMe(null) }}>logout</button>
        </span>
      </div>
      {tab === 'dashboard' ? <Dashboard me={me} /> : <Alerts />}
    </div>
  )
}