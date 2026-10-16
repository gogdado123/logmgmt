import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'
import { api } from './api'

const RANGES = { '1h': 3600e3, '24h': 86400e3, '7d': 7 * 86400e3 }
const INTERVAL = { '1h': '5m', '24h': '1h', '7d': '1d' }
const SOURCES = ['', 'firewall', 'network', 'api', 'crowdstrike', 'aws', 'm365', 'ad']

function TopChart({ title, data }) {
  return (
    <div style={{ flex: 1, minWidth: 280, height: 240 }}>
      <h4>{title}</h4>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 30 }}>
          <XAxis type="number" allowDecimals={false} />
          <YAxis type="category" dataKey="key" width={150} />
          <Tooltip />
          <Bar dataKey="count" fill="#4f7cff" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Dashboard({ me }) {
  const [tenant, setTenant] = useState(me.tenants.includes('*') ? '' : me.tenants[0])
  const [source, setSource] = useState('')
  const [range, setRange] = useState('24h')
  const [q, setQ] = useState('*')
  const [ips, setIps] = useState([])
  const [users, setUsers] = useState([])
  const [types, setTypes] = useState([])
  const [timeline, setTimeline] = useState([])
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  async function load() {
    const start = new Date(Date.now() - RANGES[range]).toISOString()
    const f = { tenant, source, start, q }
    try {
      setError('')
      const [a, b, c, t, r] = await Promise.all([
        api('/stats/top', { ...f, field: 'src_ip' }),
        api('/stats/top', { ...f, field: 'user' }),
        api('/stats/top', { ...f, field: 'event_type' }),
        api('/stats/timeline', { ...f, interval: INTERVAL[range] }),
        api('/search', { ...f, size: 50 }),
      ])
      setIps(a); setUsers(b); setTypes(c); setTimeline(t); setRows(r)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [tenant, source, range, q])

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        {me.tenants.includes('*') ? (
          <input placeholder="tenant (ว่าง = ทั้งหมด)" value={tenant} onChange={(e) => setTenant(e.target.value)} />
        ) : (
          <select value={tenant} onChange={(e) => setTenant(e.target.value)}>
            {me.tenants.map((t) => <option key={t}>{t}</option>)}
          </select>
        )}
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          {SOURCES.map((s) => <option key={s} value={s}>{s || 'all sources'}</option>)}
        </select>
        <select value={range} onChange={(e) => setRange(e.target.value)}>
          {Object.keys(RANGES).map((r) => <option key={r}>{r}</option>)}
        </select>
        <input style={{ flex: 1, minWidth: 200 }} placeholder="query เช่น user:alice" defaultValue="*"
          onKeyDown={(e) => e.key === 'Enter' && setQ(e.target.value || '*')} />
      </div>

      {error && <div style={{ color: 'crimson' }}>{error}</div>}

      <h4>Timeline</h4>
      <div style={{ height: 220 }}>
        <ResponsiveContainer>
          <LineChart data={timeline}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" tickFormatter={(v) => v.slice(5, 16).replace('T', ' ')} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line dataKey="count" stroke="#4f7cff" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <TopChart title="Top Source IP" data={ips} />
        <TopChart title="Top User" data={users} />
        <TopChart title="Top Event Type" data={types} />
      </div>

      <h4 style={{ marginTop: 40 }}>Events ({rows.length})</h4>
      <div style={{ overflowX: 'auto' }}>
        <table border="1" cellPadding="4" style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
          <thead>
            <tr><th>time</th><th>tenant</th><th>source</th><th>event_type</th><th>user</th><th>src_ip</th><th>host</th><th>action</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{r['@timestamp']}</td><td>{r.tenant}</td><td>{r.source}</td><td>{r.event_type}</td>
                <td>{r.user}</td><td>{r.src_ip}</td><td>{r.host}</td><td>{r.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}