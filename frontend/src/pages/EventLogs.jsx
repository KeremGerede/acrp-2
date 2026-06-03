import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

export default function EventLogs() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    client.get('/api/events?limit=100')
      .then(r => setEvents(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Event Logs</h1>
      <ErrorMessage message={error} />

      <div className="flex gap-6">
        <div className="flex-1 bg-slate-800 border border-slate-700 rounded-lg overflow-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-700">
              {['ID', 'Type', 'Provider', 'Actor', 'Source Branch', 'Target Branch', 'Sprint', 'Task', 'Time'].map(h =>
                <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal whitespace-nowrap">{h}</th>
              )}
            </tr></thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id} className={`border-b border-slate-700/50 cursor-pointer hover:bg-slate-700/30 ${selected?.id === e.id ? 'bg-slate-700/40' : ''}`} onClick={() => setSelected(e)}>
                  <td className="px-3 py-2 text-slate-500">{e.id}</td>
                  <td className="px-3 py-2"><Badge value={e.event_type} /></td>
                  <td className="px-3 py-2 text-slate-400">{e.provider}</td>
                  <td className="px-3 py-2 text-slate-300">{e.actor_username || '—'}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-400 max-w-[140px] truncate">{e.source_branch || '—'}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-400 max-w-[140px] truncate">{e.target_branch || '—'}</td>
                  <td className="px-3 py-2 text-slate-400">{e.detected_sprint || '—'}</td>
                  <td className="px-3 py-2 text-slate-300 font-mono text-xs">{e.detected_task_key || '—'}</td>
                  <td className="px-3 py-2 text-slate-500 text-xs whitespace-nowrap">{new Date(e.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {events.length === 0 && <tr><td colSpan={9} className="px-4 py-6 text-slate-500 text-center">No events yet.</td></tr>}
            </tbody>
          </table>
        </div>

        {selected && (
          <div className="w-72 bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm flex-shrink-0">
            <div className="flex justify-between mb-3">
              <span className="font-semibold text-slate-200">Event #{selected.id}</span>
              <button className="text-slate-500 hover:text-slate-300" onClick={() => setSelected(null)}>✕</button>
            </div>
            {[
              ['Type', <Badge value={selected.event_type} />],
              ['Is Merge', selected.is_merge_event ? 'Yes' : 'No'],
              ['Actor', selected.actor_username],
              ['Actor Email', selected.actor_email],
              ['Source', selected.source_branch],
              ['Target', selected.target_branch],
              ['Commit', selected.commit_sha?.slice(0, 10)],
              ['Sprint', selected.detected_sprint],
              ['Task', selected.detected_task_key],
            ].map(([label, val]) => (
              <div key={label} className="flex justify-between py-1 border-b border-slate-700/50">
                <span className="text-slate-500">{label}</span>
                <span className="text-slate-300 font-mono text-xs text-right max-w-[150px] truncate">{val || '—'}</span>
              </div>
            ))}
            {selected.commit_messages?.length > 0 && (
              <div className="mt-2">
                <p className="text-slate-500 text-xs mb-1">Commits:</p>
                {selected.commit_messages.map((m, i) => <p key={i} className="text-slate-400 text-xs truncate">{m}</p>)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
