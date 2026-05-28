import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mail, MailOpen, Trash2, RefreshCw, User, Clock, Tag } from 'lucide-react'

const ADMIN_PASSWORD = 'admin123'

export default function Admin() {
  const [auth, setAuth] = useState(false)
  const [password, setPassword] = useState('')
  const [messages, setMessages] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const login = (e) => {
    e.preventDefault()
    if (password === ADMIN_PASSWORD) {
      setAuth(true)
      setError('')
    } else {
      setError('Incorrect password')
    }
  }

  const fetchMessages = async () => {
    setLoading(true)
    try {
      const r = await fetch('http://localhost:8000/api/messages')
      const data = await r.json()
      setMessages(data.messages || [])
    } catch {
      setError('Failed to load messages')
    }
    setLoading(false)
  }

  const markRead = async (id) => {
    await fetch(`http://localhost:8000/api/messages/${id}/read`, { method: 'PATCH' })
    setMessages(prev => prev.map(m => m.id === id ? { ...m, read: true } : m))
    if (selected?.id === id) setSelected(prev => ({ ...prev, read: true }))
  }

  const openMessage = (msg) => {
    setSelected(msg)
    if (!msg.read) markRead(msg.id)
  }

  useEffect(() => { if (auth) fetchMessages() }, [auth])

  const unread = messages.filter(m => !m.read).length

  if (!auth) {
    return (
      <div style={{ maxWidth: 400, margin: '80px auto' }}>
        <div className="card">
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <div style={{ width: 56, height: 56, borderRadius: 16, background: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <Mail size={28} color="var(--accent)" />
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>Admin Panel</h2>
            <p style={{ fontSize: 14, color: 'var(--text2)' }}>Enter password to access messages</p>
          </div>
          <form onSubmit={login} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              style={{ padding: '10px 14px', borderRadius: 10, border: `1px solid ${error ? 'var(--red)' : 'var(--border)'}`, background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none' }}
            />
            {error && <p style={{ fontSize: 13, color: 'var(--red)' }}>{error}</p>}
            <button type="submit" className="btn btn-primary" style={{ justifyContent: 'center' }}>Login</button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--white)', marginBottom: 4 }}>Messages</h1>
          <p style={{ fontSize: 14, color: 'var(--text2)' }}>
            {messages.length} total · <span style={{ color: unread > 0 ? 'var(--accent)' : 'var(--text3)' }}>{unread} unread</span>
          </p>
        </div>
        <button className="btn btn-ghost" onClick={fetchMessages}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Message list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {loading ? (
            <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text3)' }}>Loading...</div>
          ) : messages.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text3)' }}>No messages yet</div>
          ) : messages.map(msg => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              onClick={() => openMessage(msg)}
              style={{
                padding: '14px 16px', borderRadius: 12, cursor: 'pointer',
                background: selected?.id === msg.id ? 'rgba(59,130,246,0.1)' : 'var(--surface)',
                border: `1px solid ${selected?.id === msg.id ? 'var(--accent)' : !msg.read ? 'rgba(59,130,246,0.3)' : 'var(--border)'}`,
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {!msg.read
                    ? <Mail size={14} color="var(--accent)" />
                    : <MailOpen size={14} color="var(--text3)" />
                  }
                  <span style={{ fontSize: 14, fontWeight: msg.read ? 500 : 700, color: msg.read ? 'var(--text2)' : 'var(--white)' }}>{msg.name}</span>
                </div>
                {!msg.read && <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)' }} />}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{msg.subject}</div>
              <div style={{ fontSize: 11, color: 'var(--text3)' }}>{msg.timestamp}</div>
            </motion.div>
          ))}
        </div>

        {/* Message detail */}
        <AnimatePresence mode="wait">
          {selected ? (
            <motion.div
              key={selected.id}
              className="card"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 20 }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)' }}>{selected.subject}</h2>
                <span className={`badge ${selected.read ? 'badge-gray' : 'badge-blue'}`}>
                  {selected.read ? 'Read' : 'Unread'}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20, padding: '14px 16px', background: 'var(--surface2)', borderRadius: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <User size={14} color="var(--text3)" />
                  <span style={{ fontSize: 13, color: 'var(--text3)' }}>From</span>
                  <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--white)' }}>{selected.name}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Mail size={14} color="var(--text3)" />
                  <span style={{ fontSize: 13, color: 'var(--text3)' }}>Email</span>
                  <a href={`mailto:${selected.email}`} style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none' }}>{selected.email}</a>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Tag size={14} color="var(--text3)" />
                  <span style={{ fontSize: 13, color: 'var(--text3)' }}>Subject</span>
                  <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--white)' }}>{selected.subject}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Clock size={14} color="var(--text3)" />
                  <span style={{ fontSize: 13, color: 'var(--text3)' }}>Received</span>
                  <span style={{ fontSize: 14, color: 'var(--text2)' }}>{selected.timestamp}</span>
                </div>
              </div>

              <div style={{ fontSize: 15, color: 'var(--text)', lineHeight: 1.8, whiteSpace: 'pre-wrap', padding: '16px', background: 'var(--bg2)', borderRadius: 10 }}>
                {selected.message}
              </div>

              <div style={{ marginTop: 20 }}>
                <a href={`mailto:${selected.email}?subject=Re: ${selected.subject}`} className="btn btn-primary">
                  <Mail size={15} /> Reply via Email
                </a>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text3)' }}
            >
              <div style={{ width: 64, height: 64, borderRadius: 16, background: 'var(--surface2)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <Mail size={28} color="var(--text3)" />
              </div>
              <p style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>Select a message</p>
              <p style={{ fontSize: 14 }}>Click on a message to read it</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
