import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

const empty = { tenant_id: '', integration_id: '', name: '', test_command: '', working_directory: '', target_branch_pattern: '', is_enabled: true }

export default function FunctionalTestConfigs() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => client.get('/api/functional-test-configs').then(r => setItems(r.data)).catch(e => setError(e.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const f = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const payload = { ...form, tenant_id: parseInt(form.tenant_id), integration_id: parseInt(form.integration_id) }
    try {
      if (editing) await client.patch(`/api/functional-test-configs/${editing}`, payload)
      else await client.post('/api/functional-test-configs', payload)
      setForm(empty); setEditing(null); load()
    } catch (err) { setError(err.message) } finally { setSaving(false) }
  }

  const toggle = async (id) => { await client.patch(`/api/functional-test-configs/${id}/toggle`).catch(e => setError(e.message)); load() }
  const del = async (id) => { if (!confirm('Delete?')) return; await client.delete(`/api/functional-test-configs/${id}`).catch(e => setError(e.message)); load() }
  const startEdit = (item) => { setForm(item); setEditing(item.id) }

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Functional Test Configs</h1>
      <ErrorMessage message={error} />

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6 max-w-2xl">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">{editing ? 'Edit Config' : 'New Config'}</h2>
        <form onSubmit={submit} className="grid grid-cols-2 gap-3">
          <input className="inp" placeholder="Tenant ID *" value={form.tenant_id} onChange={f('tenant_id')} required />
          <input className="inp" placeholder="Integration ID *" value={form.integration_id} onChange={f('integration_id')} required />
          <input className="inp col-span-2" placeholder="Config Name *" value={form.name} onChange={f('name')} required />
          <input className="inp col-span-2" placeholder="Test Command * (e.g. pytest tests/)" value={form.test_command} onChange={f('test_command')} required />
          <input className="inp" placeholder="Working Directory (optional)" value={form.working_directory} onChange={f('working_directory')} />
          <input className="inp" placeholder="Target Branch Pattern (optional)" value={form.target_branch_pattern} onChange={f('target_branch_pattern')} />
          <div className="col-span-2 flex gap-2">
            <button className="btn-p" disabled={saving}>{saving ? 'Saving...' : editing ? 'Update' : 'Create'}</button>
            {editing && <button type="button" className="btn-s" onClick={() => { setForm(empty); setEditing(null) }}>Cancel</button>}
          </div>
        </form>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['Name', 'Command', 'Status', 'Actions'].map(h => <th key={h} className="text-left text-slate-500 px-4 py-2 font-normal">{h}</th>)}
          </tr></thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-b border-slate-700/50">
                <td className="px-4 py-2 text-slate-200">{item.name}</td>
                <td className="px-4 py-2 text-slate-400 font-mono text-xs">{item.test_command}</td>
                <td className="px-4 py-2"><Badge value={item.is_enabled ? 'success' : 'skipped'} label={item.is_enabled ? 'Enabled' : 'Disabled'} /></td>
                <td className="px-4 py-2 flex gap-3">
                  <button className="text-cyan-400 text-xs" onClick={() => startEdit(item)}>Edit</button>
                  <button className="text-yellow-400 text-xs" onClick={() => toggle(item.id)}>{item.is_enabled ? 'Disable' : 'Enable'}</button>
                  <button className="text-red-400 text-xs" onClick={() => del(item.id)}>Delete</button>
                </td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={4} className="px-4 py-6 text-slate-500 text-center">No configs yet.</td></tr>}
          </tbody>
        </table>
      </div>
      <style>{`.inp{background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:14px;outline:none;width:100%}.inp:focus{border-color:#22d3ee}.btn-p{background:#0e7490;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}.btn-p:hover{background:#0891b2}.btn-s{background:#334155;color:#e2e8f0;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}`}</style>
    </div>
  )
}
