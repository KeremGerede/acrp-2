import { useEffect, useState } from 'react'
import client from '../api/client'
import Badge from '../components/Badge'
import Loading from '../components/Loading'

function StatCard({ label, value, color = 'text-cyan-400' }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState({ tenants: [], integrations: [], events: [], reviews: [], tests: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      client.get('/api/tenants'),
      client.get('/api/integrations'),
      client.get('/api/events?limit=10'),
      client.get('/api/merge-reviews?limit=10'),
      client.get('/api/functional-tests?limit=10'),
    ]).then(([t, i, e, r, ft]) => {
      setData({ tenants: t.data, integrations: i.data, events: e.data, reviews: r.data, tests: ft.data })
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  const reviewSuccess = data.reviews.filter(r => r.result === 'success').length
  const reviewFailed = data.reviews.filter(r => r.result === 'failed').length
  const testSuccess = data.tests.filter(r => r.result === 'success').length
  const testFailed = data.tests.filter(r => r.result === 'failed').length

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Tenants" value={data.tenants.length} />
        <StatCard label="Integrations" value={data.integrations.length} />
        <StatCard label="Reviews (success)" value={reviewSuccess} color="text-green-400" />
        <StatCard label="Reviews (failed)" value={reviewFailed} color="text-red-400" />
        <StatCard label="Tests (success)" value={testSuccess} color="text-green-400" />
        <StatCard label="Tests (failed)" value={testFailed} color="text-red-400" />
        <StatCard label="Total Events" value={data.events.length} color="text-slate-300" />
        <StatCard label="Total Reviews" value={data.reviews.length} color="text-slate-300" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Recent Events</h2>
          <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            {data.events.length === 0 ? (
              <div className="text-slate-500 text-sm p-4">No events yet.</div>
            ) : (
              <table className="w-full text-sm">
                <thead><tr className="border-b border-slate-700">
                  <th className="text-left text-slate-500 px-4 py-2 font-normal">Type</th>
                  <th className="text-left text-slate-500 px-4 py-2 font-normal">Actor</th>
                  <th className="text-left text-slate-500 px-4 py-2 font-normal">Branch</th>
                </tr></thead>
                <tbody>
                  {data.events.map(e => (
                    <tr key={e.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="px-4 py-2"><Badge value={e.event_type} /></td>
                      <td className="px-4 py-2 text-slate-300">{e.actor_username || '—'}</td>
                      <td className="px-4 py-2 text-slate-400 font-mono text-xs truncate max-w-[160px]">{e.source_branch || e.branch || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Recent Reviews</h2>
          <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            {data.reviews.length === 0 ? (
              <div className="text-slate-500 text-sm p-4">No reviews yet.</div>
            ) : (
              <table className="w-full text-sm">
                <thead><tr className="border-b border-slate-700">
                  <th className="text-left text-slate-500 px-4 py-2 font-normal">Result</th>
                  <th className="text-left text-slate-500 px-4 py-2 font-normal">Task</th>
                  <th className="text-left text-slate-500 px-4 py-2 font-normal">Risk</th>
                </tr></thead>
                <tbody>
                  {data.reviews.map(r => (
                    <tr key={r.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="px-4 py-2"><Badge value={r.result || r.status} /></td>
                      <td className="px-4 py-2 text-slate-300">{r.task_key || '—'}</td>
                      <td className="px-4 py-2"><Badge value={r.risk_level} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
