import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

const CATEGORIES = ['security', 'code_quality', 'architecture', 'testing', 'performance', 'maintainability', 'style', 'other']
const SEVERITIES = ['info', 'warning', 'high', 'critical']
const empty = { tenant_id: '', integration_id: '', title: '', description: '', category: 'other', severity: 'warning', is_enabled: true }

export default function ReviewRules() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => client.get('/api/review-rules').then(r => setRules(r.data)).catch(e => setError(e.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const f = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const payload = { ...form, tenant_id: parseInt(form.tenant_id), integration_id: form.integration_id ? parseInt(form.integration_id) : null }
    try {
      if (editing) await client.patch(`/api/review-rules/${editing}`, payload)
      else await client.post('/api/review-rules', payload)
      setForm(empty); setEditing(null); load()
    } catch (err) { setError(err.message) } finally { setSaving(false) }
  }

  const toggle = async (id) => { await client.patch(`/api/review-rules/${id}/toggle`).catch(e => setError(e.message)); load() }
  const del = async (id) => { if (!confirm('Delete?')) return; await client.delete(`/api/review-rules/${id}`).catch(e => setError(e.message)); load() }
  const startEdit = (r) => { setForm({ ...r, integration_id: r.integration_id || '' }); setEditing(r.id) }

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Review Rules</h1>
      <ErrorMessage message={error} />

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6 max-w-2xl">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">{editing ? 'Edit Rule' : 'New Rule'}</h2>
        <form onSubmit={submit} className="grid grid-cols-2 gap-3">
          <input className="inp" placeholder="Tenant ID *" value={form.tenant_id} onChange={f('tenant_id')} required />
          <input className="inp" placeholder="Integration ID (optional)" value={form.integration_id} onChange={f('integration_id')} />
          <input className="inp col-span-2" placeholder="Title *" value={form.title} onChange={f('title')} required />
          <textarea className="inp col-span-2" placeholder="Description" rows={2} value={form.description} onChange={f('description')} />
          <select className="inp" value={form.category} onChange={f('category')}>{CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}</select>
          <select className="inp" value={form.severity} onChange={f('severity')}>{SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}</select>
          <div className="col-span-2 flex gap-2">
            <button className="btn-p" disabled={saving}>{saving ? 'Saving...' : editing ? 'Update' : 'Create'}</button>
            {editing && <button type="button" className="btn-s" onClick={() => { setForm(empty); setEditing(null) }}>Cancel</button>}
          </div>
        </form>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['Title', 'Category', 'Severity', 'Status', 'Actions'].map(h => <th key={h} className="text-left text-slate-500 px-4 py-2 font-normal">{h}</th>)}
          </tr></thead>
          <tbody>
            {rules.map(r => (
              <tr key={r.id} className="border-b border-slate-700/50">
                <td className="px-4 py-2 text-slate-200">{r.title}</td>
                <td className="px-4 py-2"><Badge value={r.category} /></td>
                <td className="px-4 py-2"><Badge value={r.severity} /></td>
                <td className="px-4 py-2"><Badge value={r.is_enabled ? 'success' : 'skipped'} label={r.is_enabled ? 'Enabled' : 'Disabled'} /></td>
                <td className="px-4 py-2 flex gap-3">
                  <button className="text-cyan-400 text-xs" onClick={() => startEdit(r)}>Edit</button>
                  <button className="text-yellow-400 text-xs" onClick={() => toggle(r.id)}>{r.is_enabled ? 'Disable' : 'Enable'}</button>
                  <button className="text-red-400 text-xs" onClick={() => del(r.id)}>Delete</button>
                </td>
              </tr>
            ))}
            {rules.length === 0 && <tr><td colSpan={5} className="px-4 py-6 text-slate-500 text-center">No rules yet.</td></tr>}
          </tbody>
        </table>
      </div>
      <style>{`.inp{background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:14px;outline:none;width:100%}.inp:focus{border-color:#22d3ee}.btn-p{background:#0e7490;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}.btn-p:hover{background:#0891b2}.btn-s{background:#334155;color:#e2e8f0;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}`}</style>
    </div>
  )
}
