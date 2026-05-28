import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Users, Search, FileText, Shield, UserCheck, UserX, ChevronDown, BarChart2, UserPlus, X } from 'lucide-react'

const LEVELS = ['intern', 'resident', 'senior', 'professor']
const LEVEL_LABELS = { intern: 'Intern', resident: 'Resident', senior: 'Senior', professor: 'Professor' }
const LEVEL_COLORS = {
  intern:    '#94a3b8',
  resident:  '#3b82f6',
  senior:    '#10b981',
  professor: '#f59e0b',
}

export default function AdminDashboard() {
  const { user, token, canManageUsers } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('users')
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState({ name: '', email: '', password: '', level: 'intern', hospital: '' })
  const [createError, setCreateError] = useState('')
  const [createLoading, setCreateLoading] = useState(false)

  useEffect(() => {
    if (!canManageUsers) { navigate('/'); return }
    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch('http://localhost:8000/api/admin/stats', { headers }).then(r => r.json()),
      fetch('http://localhost:8000/api/admin/users', { headers }).then(r => r.json()),
    ]).then(([s, u]) => {
      setStats(s)
      setUsers(Array.isArray(u) ? u : [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [token, canManageUsers])

  const updateUser = async (userId, data) => {
    const r = await fetch(`http://localhost:8000/api/admin/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(data)
    })
    if (r.ok) {
      const updated = await r.json()
      setUsers(prev => prev.map(u => u.id === userId ? updated : u))
    }
  }

  const deleteUser = async (userId) => {
    if (!confirm('Delete this user?')) return
    const r = await fetch(`http://localhost:8000/api/admin/users/${userId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` }
    })
    if (r.ok) setUsers(prev => prev.filter(u => u.id !== userId))
  }

  const createUser = async (e) => {
    e.preventDefault()
    setCreateError('')
    setCreateLoading(true)
    try {
      const r = await fetch('http://localhost:8000/api/admin/users/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(createForm)
      })
      const data = await r.json()
      if (!r.ok) { setCreateError(data.detail || 'Failed to create user'); setCreateLoading(false); return }
      setUsers(prev => [data, ...prev])
      setCreateOpen(false)
      setCreateForm({ name: '', email: '', password: '', level: 'intern', hospital: '' })
    } catch { setCreateError('Connection error') }
    setCreateLoading(false)
  }

  if (loading) return <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text3)' }}>Loading...</div>

  const doctors = users.filter(u => u.role === 'doctor')

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>
          {user?.role === 'admin' ? 'Admin Dashboard' : 'Department Management'}
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text2)' }}>Manage doctors, levels, and monitor activity</p>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 14, marginBottom: 28 }}>
          {[
            { label: 'Total Doctors', value: stats.total_users, icon: Users, color: '#3b82f6' },
            { label: 'Active', value: stats.active_users, icon: UserCheck, color: '#10b981' },
            { label: 'Total Searches', value: stats.total_searches, icon: Search, color: '#06b6d4' },
            { label: 'Registered Cases', value: stats.total_cases, icon: FileText, color: '#f59e0b' },
          ].map((s, i) => {
            const Icon = s.icon
            return (
              <motion.div key={s.label} className="stat-card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}>
                <div className="stat-icon" style={{ background: `${s.color}15` }}><Icon size={18} color={s.color} /></div>
                <div className="stat-label">{s.label}</div>
                <div className="stat-value" style={{ fontSize: 24 }}>{s.value}</div>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Level breakdown */}
      {stats?.by_level && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChart2 size={16} color="var(--accent)" /> Doctors by Level
          </h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {LEVELS.map(lvl => (
              <div key={lvl} style={{ flex: 1, minWidth: 100, padding: '12px 16px', background: 'var(--surface2)', borderRadius: 10, textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: LEVEL_COLORS[lvl], marginBottom: 4 }}>{stats.by_level[lvl] || 0}</div>
                <div style={{ fontSize: 12, color: 'var(--text3)' }}>{LEVEL_LABELS[lvl]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Users table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)' }}>Doctors ({doctors.length})</h3>
          {user?.role === 'admin' && (
            <button className="btn btn-primary btn-sm" onClick={() => setCreateOpen(true)}>
              <UserPlus size={14} /> Create Account
            </button>
          )}
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Doctor', 'Email', 'Hospital', 'Level', 'Status', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {doctors.map((u, i) => (
                <motion.tr
                  key={u.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.04 }}
                  style={{ borderBottom: '1px solid var(--border)' }}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, color: 'white', fontSize: 14, flexShrink: 0 }}>
                        {u.name?.charAt(0).toUpperCase()}
                      </div>
                      <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--white)' }}>{u.name}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--text2)' }}>{u.email}</td>
                  <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--text2)' }}>{u.hospital || '—'}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <select
                      value={u.level}
                      onChange={e => updateUser(u.id, { level: e.target.value })}
                      style={{ padding: '5px 10px', borderRadius: 8, border: `1px solid ${LEVEL_COLORS[u.level]}40`, background: `${LEVEL_COLORS[u.level]}15`, color: LEVEL_COLORS[u.level], fontSize: 13, fontWeight: 700, cursor: 'pointer', outline: 'none' }}
                    >
                      {LEVELS.map(l => <option key={l} value={l}>{LEVEL_LABELS[l]}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <button
                      onClick={() => updateUser(u.id, { is_active: !u.is_active })}
                      style={{ padding: '4px 12px', borderRadius: 20, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, background: u.is_active ? 'var(--green-bg)' : 'var(--red-bg)', color: u.is_active ? 'var(--green)' : 'var(--red)' }}
                    >
                      {u.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {user?.role === 'admin' && u.id !== user.id && (
                      <button onClick={() => deleteUser(u.id)} className="btn btn-ghost btn-sm" style={{ color: 'var(--red)', padding: '4px 10px' }}>
                        <UserX size={14} />
                      </button>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create User Modal */}
      {createOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20 }}>
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            style={{ background: 'var(--surface)', border: '1px solid var(--border2)', borderRadius: 16, padding: 28, width: '100%', maxWidth: 440 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)' }}>Create Doctor Account</h3>
              <button onClick={() => setCreateOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}><X size={20} /></button>
            </div>
            <form onSubmit={createUser} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[['Full Name', 'name', 'text', 'Dr. Jane Smith'], ['Email', 'email', 'email', 'doctor@hospital.com'], ['Password', 'password', 'password', '••••••••'], ['Hospital', 'hospital', 'text', 'City Medical Center']].map(([label, key, type, ph]) => (
                <div key={key}>
                  <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 5 }}>{label}</label>
                  <input type={type} required={key !== 'hospital'} placeholder={ph} value={createForm[key]}
                    onChange={e => setCreateForm({ ...createForm, [key]: e.target.value })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 9, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                  />
                </div>
              ))}
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 5 }}>Access Level</label>
                <select value={createForm.level} onChange={e => setCreateForm({ ...createForm, level: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 9, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}>
                  {LEVELS.map(l => <option key={l} value={l}>{LEVEL_LABELS[l]}</option>)}
                </select>
              </div>
              {createError && <div style={{ padding: '9px 12px', borderRadius: 8, background: 'var(--red-bg)', color: 'var(--red)', fontSize: 13 }}>{createError}</div>}
              <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                <button type="button" onClick={() => setCreateOpen(false)} className="btn btn-ghost" style={{ flex: 1, justifyContent: 'center' }}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={createLoading} style={{ flex: 1, justifyContent: 'center' }}>
                  {createLoading ? 'Creating...' : <><UserPlus size={14} /> Create Account</>}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
