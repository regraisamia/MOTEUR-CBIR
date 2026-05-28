import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Inbox, Mail, MailOpen, Clock, Tag, RefreshCw, ArrowLeft, Microscope } from 'lucide-react'
import { getMessages, markMessageRead } from '../api'
import { useApp } from '../AppContext'
import { t } from '../i18n'

const SUBJECT_COLORS = {
  technical: '#f43f5e',
  feedback: '#10b981',
  feature: '#3b82f6',
  question: '#f59e0b',
  other: '#94a3b8',
}

export default function InboxPage() {
  const [data, setData] = useState({ total: 0, unread: 0, messages: [] })
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const { lang } = useApp()

  const SUBJECT_LABELS = {
    technical: t(lang, 'contact_subject_technical'),
    feedback: t(lang, 'contact_subject_feedback'),
    feature: t(lang, 'contact_subject_feature'),
    question: t(lang, 'contact_subject_question'),
    other: t(lang, 'contact_subject_other'),
  }

  const load = () => {
    setLoading(true)
    getMessages().then(d => { setData(d); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const openMsg = async (msg) => {
    setSelected(msg)
    if (!msg.read) {
      await markMessageRead(msg.id)
      setData(prev => ({
        ...prev,
        unread: Math.max(0, prev.unread - 1),
        messages: prev.messages.map(m => m.id === msg.id ? { ...m, read: true } : m),
      }))
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>

      {/* Admin header */}
      <div style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg2)', padding: '0 32px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Microscope size={15} color="#fff" />
          </div>
          <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--white)' }}>
            DermFinder <span style={{ color: 'var(--text3)', fontWeight: 400 }}>/ Admin</span>
          </span>
        </div>
        <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text2)', textDecoration: 'none' }}>
          <ArrowLeft size={14} /> Back to App
        </a>
      </div>

      {/* Content */}
      <div style={{ padding: '32px 24px', maxWidth: 1280, margin: '0 auto' }}>

        {/* Page header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Inbox size={24} color="var(--accent)" />
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--white)' }}>{t(lang, 'inbox_title')}</h1>
              <p style={{ fontSize: 13, color: 'var(--text2)', marginTop: 2 }}>{t(lang, 'inbox_sub')}</p>
            </div>
            {data.unread > 0 && (
              <span style={{ background: 'var(--accent)', color: '#fff', fontSize: 12, fontWeight: 700, borderRadius: 20, padding: '2px 10px' }}>
                {data.unread} {t(lang, 'inbox_new')}
              </span>
            )}
          </div>
          <button className="btn btn-outline btn-sm" onClick={load}>
            <RefreshCw size={13} /> {t(lang, 'inbox_refresh')}
          </button>
        </div>

        {/* Body */}
        {loading ? (
          <div className="card" style={{ textAlign: 'center', padding: 48 }}>
            <div className="spinner" style={{ width: 28, height: 28, margin: '0 auto' }} />
          </div>
        ) : data.messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><Inbox size={28} color="var(--text3)" /></div>
            <p style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>{t(lang, 'inbox_empty')}</p>
            <p style={{ fontSize: 14 }}>{t(lang, 'inbox_empty_sub')}</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: selected ? '380px 1fr' : '1fr', gap: 16, alignItems: 'start' }}>

            {/* Message list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.messages.map((msg, i) => {
                const color = SUBJECT_COLORS[msg.subject] || '#94a3b8'
                const isSelected = selected?.id === msg.id
                return (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    onClick={() => openMsg(msg)}
                    style={{
                      background: isSelected ? 'var(--surface2)' : 'var(--surface)',
                      border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
                      borderRadius: 12, padding: '14px 16px', cursor: 'pointer',
                      transition: 'all 0.2s', position: 'relative',
                    }}
                  >
                    {!msg.read && (
                      <div style={{ position: 'absolute', top: 16, right: 14, width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)' }} />
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      {msg.read
                        ? <MailOpen size={14} color="var(--text3)" />
                        : <Mail size={14} color="var(--accent)" />
                      }
                      <span style={{ fontWeight: msg.read ? 500 : 700, fontSize: 14, color: msg.read ? 'var(--text2)' : 'var(--white)' }}>
                        {msg.name}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto', paddingRight: 16 }}>
                        {msg.timestamp.replace('T', ' ')}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 20, background: `${color}18`, color }}>
                        {SUBJECT_LABELS[msg.subject] || msg.subject}
                      </span>
                      <span style={{ fontSize: 13, color: 'var(--text3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 180 }}>
                        {msg.message}
                      </span>
                    </div>
                  </motion.div>
                )
              })}
            </div>

            {/* Detail panel */}
            <AnimatePresence>
              {selected && (
                <motion.div
                  key={selected.id}
                  initial={{ opacity: 0, x: 16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 16 }}
                  className="card"
                  style={{ position: 'sticky', top: 88 }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
                    <div>
                      <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 4 }}>{selected.name}</h2>
                      <a href={`mailto:${selected.email}`} style={{ fontSize: 13, color: 'var(--accent)', textDecoration: 'none' }}>{selected.email}</a>
                    </div>
                    <button className="btn btn-ghost btn-sm" onClick={() => setSelected(null)}>✕</button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Tag size={13} color="var(--text3)" />
                      <span style={{ fontSize: 13, color: 'var(--text3)' }}>{t(lang, 'inbox_subject_label')}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, padding: '2px 10px', borderRadius: 20, background: `${SUBJECT_COLORS[selected.subject] || '#94a3b8'}18`, color: SUBJECT_COLORS[selected.subject] || '#94a3b8' }}>
                        {SUBJECT_LABELS[selected.subject] || selected.subject}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Clock size={13} color="var(--text3)" />
                      <span style={{ fontSize: 13, color: 'var(--text3)' }}>{selected.timestamp.replace('T', ' at ')}</span>
                    </div>
                  </div>

                  <div className="divider" style={{ margin: '0 0 16px' }} />
                  <p style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{selected.message}</p>
                  <div className="divider" style={{ margin: '20px 0 16px' }} />

                  <a
                    href={`mailto:${selected.email}?subject=Re: ${SUBJECT_LABELS[selected.subject] || selected.subject}`}
                    className="btn btn-primary"
                    style={{ justifyContent: 'center' }}
                  >
                    <Mail size={14} /> {t(lang, 'inbox_reply')}
                  </a>
                </motion.div>
              )}
            </AnimatePresence>

          </div>
        )}

      </div>
    </div>
  )
}
