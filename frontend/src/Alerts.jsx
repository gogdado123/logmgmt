import { useEffect, useState } from 'react'
import { api } from './api'

export default function Alerts() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const load = () => api('/alerts').then(setRows).catch((e) => setError(e.message))
    load()
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ padding: 16 }}>
      <h3>Alerts ({rows.length})</h3>
      {error && <div style={{ color: 'crimson' }}>{error}</div>}
      <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
        <thead><tr><th>time</th><th>tenant</th><th>rule</th><th>src_ip</th><th>count</th><th>users</th><th>message</th></tr></thead>
        <tbody>
          {rows.map((a, i) => (
            <tr key={i} style={{ background: 'rgba(220,38,38,0.15)' }}>
              <td>{a['@timestamp']}</td><td>{a.tenant}</td><td>{a.rule}</td><td>{a.src_ip}</td>
              <td>{a.count}</td><td>{(a.users || []).join(', ')}</td><td>{a.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}