import React from 'react'
import { motion } from 'framer-motion'
import { Eye } from 'lucide-react'

export default function ResultCard({ r, onDetails, index = 0 }) {
  const isMalignant = r.label === 1
  const simPct = Math.max(0, Math.min(100, (r.similarity ?? 0) * 100))

  return (
    <motion.div
      className="result-card"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onDetails && onDetails(r)}
    >
      <div style={{ position: 'relative' }}>
        <img src={`http://localhost:8000${r.image_url}`} className="result-card-img" alt={r.image_id} />
        <div style={{ position: 'absolute', top: 8, left: 8 }}>
          <span className="badge badge-gray">#{r.rank}</span>
        </div>
        <div style={{ position: 'absolute', top: 8, right: 8 }}>
          <span className={`badge ${isMalignant ? 'badge-malignant' : 'badge-benign'}`}>{r.label_name}</span>
        </div>
      </div>

      <div className="result-card-body">
        <div className="result-card-title">{r.metadata?.diagnosis || r.image_id}</div>
        <div className="result-card-sub">{r.metadata?.anatom_site || '—'}</div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>
          <span>Visual Match</span>
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{simPct.toFixed(1)}%</span>
        </div>
        <div className="sim-bar">
          <div className="sim-bar-fill" style={{ width: `${simPct}%` }} />
        </div>

        <div style={{ marginTop: 12 }}>
          <button className="btn btn-outline btn-sm" style={{ width: '100%', justifyContent: 'center' }}
            onClick={e => { e.stopPropagation(); onDetails && onDetails(r) }}>
            <Eye size={13} /> View Details
          </button>
        </div>
      </div>
    </motion.div>
  )
}
