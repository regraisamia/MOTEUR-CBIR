import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { Clock, Search, FileText, Database, ChevronDown, ChevronUp } from 'lucide-react'

const LEVEL_LABELS = { intern: 'Intern', resident: 'Resident', senior: 'Senior', professor: 'Professor' }

function SearchEntry({ entry, index }) {
  const [open, setOpen] = useState(false)
  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      style={{ padding: 0, overflow: 'hidden' }}
    >
      <div
        style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setOpen(o => !o)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Search size={16} color="var(--accent)" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--white)' }}>{entry.filename}</div>
            <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 2 }}>
              {entry.db?.toUpperCase()} · {entry.top_k} results · {entry.search_time_ms} ms
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: 'var(--text3)' }}>{entry.timestamp}</span>
          {open ? <ChevronUp size={16} color="var(--text3)" /> : <ChevronDown size={16} color="var(--text3)" />}
        </div>
      </div>

      {open && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '14px 18px', background: 'var(--bg2)' }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text3)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>All Results</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(entry.results || entry.results_summary)?.map(r => (
              <div key={r.rank} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--surface)', borderRadius: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 12, color: 'var(--text3)' }}>#{r.rank}</span>
                  {r.image_url && (
                    <img src={`http://localhost:8000${r.image_url}`} alt={r.image_id}
                      style={{ width: 36, height: 36, borderRadius: 6, objectFit: 'cover' }}
                      onError={e => { e.target.style.display = 'none' }}
                    />
                  )}
                  <span style={{ fontSize: 13, color: 'var(--text)' }}>{r.image_id}</span>
                  <span className={`badge ${r.label_name === 'Malignant' ? 'badge-malignant' : 'badge-benign'}`} style={{ fontSize: 11 }}>{r.label_name}</span>
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)' }}>{(r.similarity * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

function CaseEntry({ entry, index }) {
  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      style={{ display: 'flex', gap: 16 }}
    >
      <img
        src={`http://localhost:8000${entry.image_url}`}
        alt={entry.image_id}
        style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 10, flexShrink: 0 }}
        onError={e => { e.target.style.display = 'none' }}
      />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 6 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--white)', marginBottom: 4 }}>{entry.diagnosis}</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <span className="badge badge-blue" style={{ fontSize: 11 }}>Dr. {entry.doctor_name}</span>
              <span className="badge badge-gray" style={{ fontSize: 11 }}>{LEVEL_LABELS[entry.doctor_level]}</span>
              <span className="badge badge-gray" style={{ fontSize: 11 }}>{entry.db?.toUpperCase()}</span>
            </div>
          </div>
          <span style={{ fontSize: 12, color: 'var(--text3)', flexShrink: 0 }}>{entry.timestamp}</span>
        </div>
        {entry.notes && <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{entry.notes}</p>}
        <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 6 }}>
          {entry.metadata?.anatom_site && `📍 ${entry.metadata.anatom_site}`}
          {entry.metadata?.age_approx && ` · Age ${entry.metadata.age_approx}`}
          {entry.metadata?.sex && ` · ${entry.metadata.sex}`}
        </div>
      </div>
    </motion.div>
  )
}

export default function History() {
  const { token, canViewAll } = useAuth()
  const [tab, setTab] = useState('searches')
  const [searches, setSearches] = useState([])
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch('http://localhost:8000/api/history', { headers }).then(r => r.json()),
      fetch('http://localhost:8000/api/cases', { headers }).then(r => r.json()),
    ]).then(([h, c]) => {
      setSearches(Array.isArray(h) ? h : [])
      setCases(Array.isArray(c) ? c : [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [token])

  const tabs = [
    { id: 'searches', label: 'Search History', icon: Search, count: searches.length },
    { id: 'cases', label: 'Registered Cases', icon: FileText, count: cases.length },
  ]

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>
          {canViewAll ? 'All Activity' : 'My Activity'}
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text2)' }}>
          {canViewAll ? 'Search history and registered cases from all doctors' : 'Your search history and registered cases'}
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {tabs.map(t => {
          const Icon = t.icon
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '10px 18px', borderRadius: 10, cursor: 'pointer',
                border: tab === t.id ? '2px solid var(--accent)' : '2px solid var(--border)',
                background: tab === t.id ? 'rgba(59,130,246,0.08)' : 'var(--surface)',
                color: tab === t.id ? 'var(--white)' : 'var(--text2)',
                fontWeight: 600, fontSize: 14, transition: 'all 0.2s',
              }}
            >
              <Icon size={15} />
              {t.label}
              <span style={{ padding: '1px 8px', borderRadius: 20, background: tab === t.id ? 'var(--accent)' : 'var(--surface2)', color: tab === t.id ? 'white' : 'var(--text3)', fontSize: 12, fontWeight: 700 }}>
                {t.count}
              </span>
            </button>
          )
        })}
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text3)' }}>Loading...</div>
      ) : tab === 'searches' ? (
        searches.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><Search size={28} color="var(--text3)" /></div>
            <p style={{ fontWeight: 600, color: 'var(--text2)' }}>No searches yet</p>
            <p style={{ fontSize: 14 }}>Your search history will appear here</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {searches.map((s, i) => <SearchEntry key={s.id} entry={s} index={i} />)}
          </div>
        )
      ) : (
        cases.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><FileText size={28} color="var(--text3)" /></div>
            <p style={{ fontWeight: 600, color: 'var(--text2)' }}>No registered cases yet</p>
            <p style={{ fontSize: 14 }}>Cases you register from search results will appear here</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {cases.map((c, i) => <CaseEntry key={c.id} entry={c} index={i} />)}
          </div>
        )
      )}
    </div>
  )
}
