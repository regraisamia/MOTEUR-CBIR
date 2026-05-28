import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { searchImage } from '../api'
import { useAuth } from '../context/AuthContext'
import UploadPanel from '../components/UploadPanel'
import ResultCard from '../components/ResultCard'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import MetadataPanel from '../components/MetadataPanel'
import { Search, Clock, FileText, AlertTriangle, Database, FilePlus, CheckCircle } from 'lucide-react'

const DATABASES = [
  { id: 'isic2020', label: 'ISIC 2020', sub: '33,126 cases', color: '#3b82f6' },
  { id: 'isic2019', label: 'ISIC 2019', sub: '25,331 cases', color: '#06b6d4' },
]

export default function SearchPage() {
  const { user, token, canAnnotate } = useAuth()
  const [db, setDb] = useState('isic2020')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [topK, setTopK] = useState(10)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [searchMeta, setSearchMeta] = useState(null)
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState(null)

  // Register case
  const [registerOpen, setRegisterOpen] = useState(false)
  const [registerTarget, setRegisterTarget] = useState(null)
  const [regForm, setRegForm] = useState({ diagnosis: '', notes: '' })
  const [regLoading, setRegLoading] = useState(false)
  const [regSuccess, setRegSuccess] = useState(false)

  const onFile = (e) => {
    const f = e.target.files?.[0]
    if (!f) { setFile(null); setPreview(null); return }
    setFile(f); setPreview(URL.createObjectURL(f))
    setResults([]); setSearchMeta(null)
  }

  const analyze = async () => {
    if (!file) return
    setLoading(true)
    try {
      const res = await searchImage(file, topK, db, token)
      setResults(res.results || [])
      setSearchMeta({ time: res.search_time_ms, topK: res.top_k, db: res.db })
    } catch (e) { console.error(e); setResults([]) }
    setLoading(false)
  }

  const handleDbChange = (newDb) => { setDb(newDb); setResults([]); setSearchMeta(null) }

  const openRegister = () => {
    if (!file) return
    setRegForm({ diagnosis: '', notes: '' })
    setRegSuccess(false)
    setRegisterOpen(true)
  }

  const submitRegister = async () => {
    if (!regForm.diagnosis.trim()) return
    setRegLoading(true)
    try {
      await fetch('http://localhost:8000/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          image_id: file.name,
          db,
          diagnosis: regForm.diagnosis,
          notes: regForm.notes,
          image_url: preview,
          metadata: { image_name: file.name },
          is_query_image: true,
          top_results: results.slice(0, 5).map(r => ({
            rank: r.rank,
            image_id: r.image_id,
            label_name: r.label_name,
            similarity: r.similarity,
          }))
        })
      })
      setRegSuccess(true)
      setTimeout(() => setRegisterOpen(false), 1500)
    } catch (e) { console.error(e) }
    setRegLoading(false)
  }

  const benignCount = results.filter(r => r.label === 0).length
  const malignantCount = results.filter(r => r.label === 1).length

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--white)', marginBottom: 8 }}>Case Search</h1>
        <p style={{ fontSize: 15, color: 'var(--text2)' }}>Upload a dermoscopy image to find similar cases from our reference database</p>
      </div>

      {/* DB selector */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <Database size={15} color="var(--text3)" />
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Reference Database</span>
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {DATABASES.map(d => (
            <button key={d.id} onClick={() => handleDbChange(d.id)} style={{
              display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
              padding: '14px 20px', borderRadius: 12, cursor: 'pointer', minWidth: 180,
              border: db === d.id ? `2px solid ${d.color}` : '2px solid var(--border)',
              background: db === d.id ? `rgba(${d.id === 'isic2020' ? '59,130,246' : '6,182,212'},0.08)` : 'var(--surface)',
              transition: 'all 0.2s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: db === d.id ? d.color : 'var(--text3)' }} />
                <span style={{ fontWeight: 700, fontSize: 15, color: db === d.id ? 'var(--white)' : 'var(--text2)' }}>{d.label}</span>
              </div>
              <span style={{ fontSize: 12, color: 'var(--text3)', paddingLeft: 16 }}>{d.sub}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="search-layout">
        {/* Left */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <UploadPanel file={file} preview={preview} onFileChange={onFile} topK={topK} setTopK={setTopK} onAnalyze={analyze} loading={loading} />

          {!user && (
            <div style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 12, padding: '14px 16px', display: 'flex', gap: 10 }}>
              <FileText size={16} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
              <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>
                <a href="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>Sign in</a> to save your search history and register cases.
              </p>
            </div>
          )}

          {canAnnotate && (
            <div style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 12, padding: '14px 16px', display: 'flex', gap: 10 }}>
              <FilePlus size={16} color="var(--green)" style={{ flexShrink: 0, marginTop: 2 }} />
              <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>
                As <strong style={{ color: 'var(--white)' }}>{user?.name}</strong>, you can register cases with your diagnosis.
              </p>
            </div>
          )}

          <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 12, padding: '14px 16px', display: 'flex', gap: 10 }}>
            <AlertTriangle size={16} color="var(--yellow)" style={{ flexShrink: 0, marginTop: 2 }} />
            <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>
              For <strong style={{ color: 'var(--yellow)' }}>reference only</strong>. Not a diagnostic tool.
            </p>
          </div>
        </div>

        {/* Right */}
        <div>
          <AnimatePresence>
            {searchMeta && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
                <div className="card" style={{ padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                  <Clock size={15} color="var(--accent)" />
                  <span style={{ fontSize: 13, color: 'var(--text2)' }}>Search completed</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--white)' }}>{searchMeta.time?.toFixed(0)} ms</span>
                </div>
                <div className="card" style={{ padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 8, flex: 1, flexWrap: 'wrap' }}>
                  <FileText size={15} color="var(--accent2)" />
                  <span className="badge badge-benign">{benignCount} Benign</span>
                  <span className="badge badge-malignant">{malignantCount} Malignant</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {loading ? (
            <div className="card"><LoadingSpinner label="Searching reference database..." /></div>
          ) : results.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon"><Search size={28} color="var(--text3)" /></div>
              <p style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>No results yet</p>
              <p style={{ fontSize: 14 }}>Upload a dermoscopy image to find similar reference cases</p>
            </div>
          ) : (
            <>  
              <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)' }}>Similar Cases ({results.length})</h3>
                  <p style={{ fontSize: 13, color: 'var(--text3)', marginTop: 4 }}>Ranked by visual similarity</p>
                </div>
                {canAnnotate && (
                  <button className="btn btn-primary btn-sm" onClick={openRegister}>
                    <FilePlus size={14} /> Register This Case
                  </button>
                )}
              </div>
              <div className="results-grid">
                {results.map((r, i) => (
                  <ResultCard key={r.image_id} r={r} index={i}
                    canAnnotate={canAnnotate}
                    onDetails={res => { setSelected(res); setOpen(true) }}
                    onRegister={openRegister}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Detail Modal */}
      <Modal open={open} onClose={() => setOpen(false)} title={selected ? `Reference Case #${selected.rank}` : 'Details'}>
        {selected && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div>
              <img src={`http://localhost:8000${selected.image_url}`} style={{ width: '100%', borderRadius: 10, display: 'block' }} alt={selected.image_id} />
              <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <span className={`badge ${selected.label === 1 ? 'badge-malignant' : 'badge-benign'}`}>{selected.label_name}</span>
                <span className="badge badge-gray">Match #{selected.rank}</span>
              </div>
              {canAnnotate && (
                <button className="btn btn-primary" style={{ marginTop: 14, width: '100%', justifyContent: 'center' }}
                  onClick={() => { setOpen(false); openRegister(selected) }}>
                  <FilePlus size={15} /> Register This Case
                </button>
              )}
            </div>
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>Case Information</h4>
              <MetadataPanel metadata={selected.metadata} />
              <div className="divider" style={{ margin: '16px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: 'var(--text2)' }}>Visual Match</span>
                <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{((selected.similarity ?? 0) * 100).toFixed(1)}%</span>
              </div>
              <div className="sim-bar"><div className="sim-bar-fill" style={{ width: `${Math.max(0, Math.min(100, (selected.similarity ?? 0) * 100))}%` }} /></div>
            </div>
          </div>
        )}
      </Modal>

      {/* Register Case Modal — for the QUERY image */}
      <Modal open={registerOpen} onClose={() => setRegisterOpen(false)} title="Register Case">
        {regSuccess ? (
          <div style={{ textAlign: 'center', padding: '32px 20px' }}>
            <CheckCircle size={48} color="var(--green)" style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)', marginBottom: 8 }}>Case Registered!</h3>
            <p style={{ fontSize: 14, color: 'var(--text2)' }}>Saved under your name in the activity log.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div>
              <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Query Image</p>
              <img src={preview} style={{ width: '100%', borderRadius: 10, display: 'block', marginBottom: 12 }} alt="query" />
              <p style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 8 }}>Top similar cases found:</p>
              {results.slice(0, 3).map(r => (
                <div key={r.rank} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--surface2)', borderRadius: 8, marginBottom: 6, fontSize: 13 }}>
                  <span style={{ color: 'var(--text2)' }}>#{r.rank} {r.metadata?.diagnosis || r.image_id}</span>
                  <span className={`badge ${r.label === 1 ? 'badge-malignant' : 'badge-benign'}`} style={{ fontSize: 11 }}>{r.label_name}</span>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ padding: '12px 14px', background: 'var(--surface2)', borderRadius: 10 }}>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>Registering as</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--white)' }}>Dr. {user?.name}</div>
                <div style={{ fontSize: 12, color: 'var(--accent)' }}>{user?.level?.charAt(0).toUpperCase() + user?.level?.slice(1)} · {user?.hospital}</div>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>Your Diagnosis *</label>
                <input
                  value={regForm.diagnosis}
                  onChange={e => setRegForm({ ...regForm, diagnosis: e.target.value })}
                  placeholder="e.g. Melanocytic nevus, Melanoma..."
                  style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 6 }}>Clinical Notes</label>
                <textarea
                  value={regForm.notes}
                  onChange={e => setRegForm({ ...regForm, notes: e.target.value })}
                  rows={4}
                  placeholder="Additional observations, patient context..."
                  style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box' }}
                />
              </div>
              <button className="btn btn-primary" onClick={submitRegister} disabled={regLoading || !regForm.diagnosis.trim()} style={{ justifyContent: 'center' }}>
                {regLoading ? <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Saving...</> : <><FilePlus size={15} /> Register Case</>}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
