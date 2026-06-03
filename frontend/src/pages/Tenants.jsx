import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'

const empty = { name: '', contact_email: '' }

export default function Tenants() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => client.get('/api/tenants').then(r => setTenants(r.data)).catch(e => setError(e.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      if (editing) { await client.patch(`/api/tenants/${editing}`, form) }
      else { await client.post('/api/tenants', form) }
      setForm(empty); setEditing(null); load()
    } catch (err) { setError(err.message) } finally { setSaving(false) }
  }

  const startEdit = (t) => { setForm({ name: t.name, contact_email: t.contact_email }); setEditing(t.id) }

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Tenants</h1>
      <ErrorMessage message={error} />

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6 max-w-lg">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">{editing ? 'Edit Tenant' : 'New Tenant'}</h2>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <input className="input" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
          <input className="input" placeholder="Contact Email" type="email" value={form.contact_email} onChange={e => setForm({ ...form, contact_email: e.target.value })} required />
          <div className="flex gap-2">
            <button className="btn-primary" disabled={saving}>{saving ? 'Saving...' : editing ? 'Update' : 'Create'}</button>
            {editing && <button type="button" className="btn-secondary" onClick={() => { setForm(empty); setEditing(null) }}>Cancel</button>}
          </div>
        </form>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            <th className="text-left text-slate-500 px-4 py-2 font-normal">ID</th>
            <th className="text-left text-slate-500 px-4 py-2 font-normal">Name</th>
            <th className="text-left text-slate-500 px-4 py-2 font-normal">Email</th>
            <th className="text-left text-slate-500 px-4 py-2 font-normal">Actions</th>
          </tr></thead>
          <tbody>
            {tenants.map(t => (
              <tr key={t.id} className="border-b border-slate-700/50">
                <td className="px-4 py-2 text-slate-500">{t.id}</td>
                <td className="px-4 py-2 text-slate-200">{t.name}</td>
                <td className="px-4 py-2 text-slate-400">{t.contact_email}</td>
                <td className="px-4 py-2"><button className="text-cyan-400 hover:text-cyan-300 text-xs" onClick={() => startEdit(t)}>Edit</button></td>
              </tr>
            ))}
            {tenants.length === 0 && <tr><td colSpan={4} className="px-4 py-6 text-slate-500 text-center">No tenants yet.</td></tr>}
          </tbody>
        </table>
      </div>

      <style>{`.input{background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:14px;outline:none;width:100%}.input:focus{border-color:#22d3ee}.btn-primary{background:#0e7490;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}.btn-primary:hover{background:#0891b2}.btn-secondary{background:#334155;color:#e2e8f0;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}`}</style>
    </div>
  )
}
