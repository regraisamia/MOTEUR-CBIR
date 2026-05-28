import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Database, Eye } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import MetadataPanel from '../components/MetadataPanel'

const DATABASES = [
  { id: 'isic2020', label: 'ISIC 2020', sub: '33K · Binary', color: '#3b82f6' },
  { id: 'isic2019', label: 'ISIC 2019', sub: '25K · Multi-class', color: '#06b6d4' },
]

export default function DatabasePage() {
  const [db, setDb] = useState('isic2020')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setLoading(true)
    fetch(`http://localhost:8000/api/sample?n=20&db=${db}`)
      .then(r => r.json())
      .then(d => { setItems(d.items || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [db])

  return (
    <div>
      <div className="section-header">
        <div className="section-tag"><Database size={12} /> Dataset</div>
        <h1 className="section-title">Database Sample</h1>
        <p className="section-sub">Preview dermoscopy images from the selected dataset</p>
      </div>

      {/* DB selector */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
        {DATABASES.map(d => (
          <button
            key={d.id}
            onClick={() => setDb(d.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 18px', borderRadius: 10, cursor: 'pointer',
              border: db === d.id ? `2px solid ${d.color}` : '2px solid var(--border)',
              background: db === d.id ? `rgba(${d.id === 'isic2020' ? '59,130,246' : '6,182,212'},0.08)` : 'var(--surface)',
              transition: 'all 0.2s',
            }}
          >
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: db === d.id ? d.color : 'var(--text3)' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, color: db === d.id ? 'var(--white)' : 'var(--text2)' }}>{d.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text3)' }}>{d.sub}</div>
            </div>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card"><LoadingSpinner label="Loading sample..." /></div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14 }}>
          {items.map((it, i) => {
            const isMalignant = it.metadata?.target === 1
            return (
              <motion.div
                key={it.image_id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.04 }}
                style={{ position: 'relative', borderRadius: 12, overflow: 'hidden', cursor: 'pointer', border: '1px solid var(--border)', background: 'var(--surface)' }}
                onClick={() => setSelected(it)}
              >
                <img
                  src={`http://localhost:8000${it.image_url}`}
                  alt={it.image_id}
                  style={{ width: '100%', height: 160, objectFit: 'cover', display: 'block' }}
                />
                <div style={{
                  position: 'absolute', inset: 0,
                  background: 'linear-gradient(to top, rgba(5,13,26,0.95) 0%, rgba(5,13,26,0.3) 50%, transparent 100%)',
                  display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: 12
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--white)', marginBottom: 3 }}>
                        {it.metadata?.diagnosis || it.metadata?.label_name || '—'}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text2)' }}>{it.metadata?.anatom_site || '—'}</div>
                    </div>
                    <span className={`badge ${isMalignant ? 'badge-malignant' : 'badge-benign'}`} style={{ fontSize: 10 }}>
                      {isMalignant ? 'Malignant' : 'Benign'}
                    </span>
                  </div>
                </div>
                <div style={{ position: 'absolute', top: 8, right: 8, background: 'rgba(0,0,0,0.5)', borderRadius: 6, padding: 5, display: 'flex' }}>
                  <Eye size={13} color="white" />
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      <Modal open={!!selected} onClose={() => setSelected(null)} title={selected?.image_id || 'Image Details'}>
        {selected && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <img src={`http://localhost:8000${selected.image_url}`} alt={selected.image_id} style={{ width: '100%', borderRadius: 10 }} />
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>Clinical Metadata</h4>
              <MetadataPanel metadata={selected.metadata} />
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
