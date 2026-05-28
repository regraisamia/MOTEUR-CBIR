import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Microscope, User, Mail, Lock, Building, ChevronDown } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const LEVELS = [
  { value: 'intern',    label: 'Intern' },
  { value: 'resident',  label: 'Resident' },
  { value: 'senior',    label: 'Senior Dermatologist' },
  { value: 'professor', label: 'Professor / Head of Department' },
]

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '', level: 'intern', hospital: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    if (form.password.length < 6) { setError('Password must be at least 6 characters'); return }
    setLoading(true); setError('')
    try {
      const r = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.name, email: form.email, password: form.password, level: form.level, hospital: form.hospital })
      })
      const data = await r.json()
      if (!r.ok) { setError(data.detail || 'Registration failed'); setLoading(false); return }
      login(data.token, data.user)
      navigate('/')
    } catch {
      setError('Connection error. Is the server running?')
    }
    setLoading(false)
  }

  const field = (key, label, type, placeholder, icon) => {
    const Icon = icon
    return (
      <div>
        <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>{label}</label>
        <div style={{ position: 'relative' }}>
          <Icon size={16} color="var(--text3)" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type={type} required value={form[key]}
            onChange={e => setForm({ ...form, [key]: e.target.value })}
            placeholder={placeholder}
            style={{ width: '100%', padding: '10px 14px 10px 38px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
          />
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)', padding: 20 }}>
      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 56, height: 56, borderRadius: 16, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', boxShadow: '0 0 24px var(--accent-glow)' }}>
            <Microscope size={28} color="#fff" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--white)', fontFamily: 'Space Grotesk, sans-serif' }}>DermFinder</h1>
          <p style={{ fontSize: 14, color: 'var(--text2)', marginTop: 4 }}>Create your clinical account</p>
        </div>

        <div className="card">
          <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>Register</h2>
          <p style={{ fontSize: 14, color: 'var(--text2)', marginBottom: 24 }}>For authorized dermatology staff only</p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {field('name', 'Full Name', 'text', 'Dr. John Smith', User)}
            {field('email', 'Email', 'email', 'doctor@hospital.com', Mail)}
            {field('hospital', 'Hospital / Institution', 'text', 'City Hospital', Building)}

            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>Clinical Level</label>
              <select
                value={form.level}
                onChange={e => setForm({ ...form, level: e.target.value })}
                className="select-styled" style={{ width: '100%' }}
              >
                {LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
              </select>
            </div>

            {field('password', 'Password', 'password', '••••••••', Lock)}
            {field('confirm', 'Confirm Password', 'password', '••••••••', Lock)}

            {error && <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--red-bg)', color: 'var(--red)', fontSize: 13 }}>{error}</div>}

            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', fontSize: 13, color: 'var(--text2)' }}>
              ⚠️ Your account will be registered as <strong style={{ color: 'var(--white)' }}>{LEVELS.find(l => l.value === form.level)?.label}</strong>. Level can be updated by an admin or professor.
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: 4 }}>
              {loading ? <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Creating account...</> : 'Create Account'}
            </button>
          </form>

          <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text2)', marginTop: 20 }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>Sign In</Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
