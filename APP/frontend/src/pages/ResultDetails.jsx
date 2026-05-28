import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { getMetadata } from '../api'
import MetadataPanel from '../components/MetadataPanel'
import LoadingSpinner from '../components/LoadingSpinner'
import { ArrowLeft, FileImage } from 'lucide-react'

export default function ResultDetails() {
  const { id } = useParams()
  const [md, setMd] = useState(null)

  useEffect(() => { if (id) getMetadata(id).then(setMd) }, [id])

  if (!md) return <div className="card"><LoadingSpinner label="Loading case details..." /></div>

  const isMalignant = md.target === 1

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Link to="/search" className="btn btn-ghost btn-sm" style={{ marginBottom: 16, display: 'inline-flex' }}>
          <ArrowLeft size={14} /> Back to Search
        </Link>
        <div className="section-tag"><FileImage size={12} /> Case Details</div>
        <h1 className="section-title">{id}</h1>
      </div>

      <div className="details-grid">
        <motion.div className="card" style={{ padding: 0, overflow: 'hidden' }} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
          <img src={`http://localhost:8000/api/image/${id}`} alt={id} style={{ width: '100%', display: 'block' }} />
          <div style={{ padding: 16, display: 'flex', gap: 8 }}>
            <span className={`badge ${isMalignant ? 'badge-malignant' : 'badge-benign'}`}>
              {isMalignant ? 'Malignant' : 'Benign'}
            </span>
            {md.diagnosis && <span className="badge badge-blue">{md.diagnosis}</span>}
          </div>
        </motion.div>

        <motion.div className="card" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 16 }}>Clinical Metadata</h3>
          <MetadataPanel metadata={md} />
        </motion.div>
      </div>
    </div>
  )
}
