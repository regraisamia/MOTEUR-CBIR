import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { User, Mail, Building, Award, Shield, Save, Lock } from 'lucide-react'

const LEVEL_COLORS = {
  intern:    { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)' },
  resident:  { color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' },
  senior:    { color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  professor: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
}

const LEVEL_LABELS = { intern: 'Intern', resident: 'Resident', senior: 'Senior Dermatologist', professor: 'Professor' }

export default function Profile() {
  const { user, token, updateUser } = useAuth()
  const [form, setForm] = useState({ name: user?.name || '', hospital: user?.hospital || '' })
  const [pwdForm, setPwdForm] = useState({ password: '', confirm: '' })
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const save = async (e) => {
    e.preventDefault()
    setLoading(true); setMsg(''); setError('')
    const payload = { name: form.name, hospital: form.hospital }
    if (pwdForm.password) {
      if (pwdForm.password !== pwdForm.confirm) { setError('Passwords do not match'); setLoading(false); return }
      payload.password = pwdForm.password
    }
    try {
      const r = await fetch('http://localhost:8000/api/auth/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload)
      })
      const data = await r.json()
      if (!r.ok) { setError(data.detail); setLoading(false); return }
      updateUser(data)
      setMsg('Profile updated successfully')
      setPwdForm({ password: '', confirm: '' })
    } catch { setError('Failed to update profile') }
    setLoading(false)
  }

  const lc = LEVEL_COLORS[user?.level] || LEVEL_COLORS.intern

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>My Profile</h1>
        <p style={{ fontSize: 14, color: 'var(--text2)' }}>Manage your account information</p>
      </div>

      {/* Profile card */}
      <motion.div className="card" style={{ marginBottom: 20 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 24 }}>
          <div style={{ width: 72, height: 72, borderRadius: 20, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 800, color: 'white', flexShrink: 0 }}>
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>{user?.name}</h2>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ padding: '3px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: lc.bg, color: lc.color }}>
                {LEVEL_LABELS[user?.level]}
              </span>
              <span className="badge badge-blue">{user?.specialty}</span>
              {user?.role === 'admin' && <span className="badge badge-malignant">Admin</span>}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          {[
            { icon: Mail, label: 'Email', value: user?.email },
            { icon: Building, label: 'Hospital', value: user?.hospital || '—' },
            { icon: Award, label: 'Specialty', value: user?.specialty },
            { icon: Shield, label: 'Member since', value: user?.created_at?.split('T')[0] },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} style={{ padding: '12px 14px', background: 'var(--surface2)', borderRadius: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Icon size={14} color="var(--text3)" />
                <span style={{ fontSize: 12, color: 'var(--text3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--white)' }}>{value}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Edit form */}
      <motion.div className="card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 20 }}>Edit Information</h3>
        <form onSubmit={save} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>Full Name</label>
            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
              style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }} />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>Hospital / Institution</label>
            <input value={form.hospital} onChange={e => setForm({ ...form, hospital: e.target.value })}
              style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }} />
          </div>

          <div style={{ height: 1, background: 'var(--border)', margin: '4px 0' }} />
          <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text2)', display: 'flex', alignItems: 'center', gap: 8 }}><Lock size={14} /> Change Password (optional)</h4>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>New Password</label>
              <input type="password" value={pwdForm.password} onChange={e => setPwdForm({ ...pwdForm, password: e.target.value })} placeholder="Leave blank to keep current"
                style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>Confirm Password</label>
              <input type="password" value={pwdForm.confirm} onChange={e => setPwdForm({ ...pwdForm, confirm: e.target.value })} placeholder="••••••••"
                style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }} />
            </div>
          </div>

          {msg && <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--green-bg)', color: 'var(--green)', fontSize: 13 }}>{msg}</div>}
          {error && <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--red-bg)', color: 'var(--red)', fontSize: 13 }}>{error}</div>}

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ justifyContent: 'center' }}>
            <Save size={15} /> {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </motion.div>
    </div>
  )
}
