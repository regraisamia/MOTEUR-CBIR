import React, { useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, ImageIcon, X, List } from 'lucide-react'

export default function UploadPanel({ file, preview, onFileChange, topK, setTopK, onAnalyze, loading }) {
  const [drag, setDrag] = useState(false)
  const inputRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) onFileChange({ target: { files: [f] } })
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 4 }}>Upload Dermoscopy Image</h3>
        <p style={{ fontSize: 13, color: 'var(--text2)' }}>Upload a dermoscopy image to search for similar cases</p>
      </div>

      <div
        className={`upload-zone ${drag ? 'drag-over' : ''}`}
        onDragOver={e => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        onClick={() => !preview && inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" accept="image/*" onChange={onFileChange} style={{ display: 'none' }} />
        <AnimatePresence mode="wait">
          {preview ? (
            <motion.div key="preview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <img src={preview} className="upload-preview" alt="preview" />
              <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text2)' }}>{file?.name}</span>
                <button className="btn btn-ghost btn-sm" onClick={e => { e.stopPropagation(); onFileChange({ target: { files: [] } }) }} style={{ padding: '4px 8px' }}>
                  <X size={13} />
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="upload-icon"><ImageIcon size={24} color="var(--accent)" /></div>
              <p style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>Drop image here or click to browse</p>
              <p style={{ fontSize: 13, color: 'var(--text3)' }}>Supports JPG, PNG formats</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          <List size={15} color="var(--text3)" />
          <span style={{ fontSize: 13, color: 'var(--text2)', fontWeight: 500 }}>Number of results</span>
          <select className="select-styled" value={topK} onChange={e => setTopK(parseInt(e.target.value))}>
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
          </select>
        </div>
        <button className="btn btn-primary" onClick={onAnalyze} disabled={loading || !file} style={{ flex: 1, justifyContent: 'center' }}>
          {loading
            ? <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Searching...</>
            : <><Upload size={15} /> Find Similar Cases</>
          }
        </button>
      </div>
    </div>
  )
}
