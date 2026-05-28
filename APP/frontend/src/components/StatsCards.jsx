import React from 'react'
import { motion } from 'framer-motion'
import { ImageIcon, ShieldCheck, AlertCircle, Database } from 'lucide-react'

const cards = [
  { key: 'total_images', label: 'Reference Cases',  icon: Database,     color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' },
  { key: 'benign',       label: 'Benign Cases',     icon: ShieldCheck,  color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  { key: 'malignant',    label: 'Malignant Cases',  icon: AlertCircle,  color: '#f43f5e', bg: 'rgba(244,63,94,0.12)' },
]

export default function StatsCards({ stats }) {
  if (!stats) return null
  return (
    <div className="stats-grid">
      {cards.map((c, i) => {
        const Icon = c.icon
        return (
          <motion.div key={c.key} className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <div className="stat-icon" style={{ background: c.bg }}><Icon size={20} color={c.color} /></div>
            <div className="stat-label">{c.label}</div>
            <div className="stat-value">{(stats[c.key] ?? 0).toLocaleString()}</div>
            {c.key === 'benign'    && stats.total_images > 0 && <div className="stat-sub">{((stats.benign    / stats.total_images) * 100).toFixed(1)}% of database</div>}
            {c.key === 'malignant' && stats.total_images > 0 && <div className="stat-sub">{((stats.malignant / stats.total_images) * 100).toFixed(1)}% of database</div>}
            {c.key === 'total_images' && <div className="stat-sub">Validated images</div>}
          </motion.div>
        )
      })}
    </div>
  )
}
