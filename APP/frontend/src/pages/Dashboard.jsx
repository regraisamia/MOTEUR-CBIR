import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { getStats } from '../api'
import StatsCards from '../components/StatsCards'
import LoadingSpinner from '../components/LoadingSpinner'
import { Search, Database, Clock, Shield } from 'lucide-react'

const features = [
  { icon: Search,   title: 'Visual Case Matching',   desc: 'Upload a dermoscopy image to find visually similar cases from our extensive medical database.', color: '#3b82f6' },
  { icon: Database, title: 'Extensive Database',      desc: 'Access over 58,000 validated dermoscopy images from ISIC 2019 and 2020 datasets.',            color: '#10b981' },
  { icon: Clock,    title: 'Instant Results',         desc: 'Get similar case recommendations in milliseconds to support your diagnostic workflow.',         color: '#f59e0b' },
  { icon: Shield,   title: 'Clinical Metadata',       desc: 'Each case includes patient demographics, anatomical location, and diagnostic information.',     color: '#06b6d4' },
]

const steps = [
  { num: '1', title: 'Upload Image',       desc: 'Capture or upload dermoscopy image' },
  { num: '2', title: 'Analyze',            desc: 'System finds similar cases' },
  { num: '3', title: 'Review Results',     desc: 'Compare with reference images' },
  { num: '4', title: 'Clinical Decision',  desc: 'Use findings to support diagnosis' },
]

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  useEffect(() => { getStats('isic2020').then(setStats) }, [])

  return (
    <div>
      {/* Hero */}
      <section style={{ textAlign: 'center', padding: '60px 24px 50px' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px', borderRadius: 20, background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)', marginBottom: 20 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', animation: 'pulse 2s infinite' }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>Clinical Decision Support Tool</span>
          </div>
          <h1 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 800, color: 'var(--white)', lineHeight: 1.2, marginBottom: 16 }}>
            Dermoscopy Image<br />
            <span style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent2))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              Case Finder
            </span>
          </h1>
          <p style={{ fontSize: 17, color: 'var(--text2)', maxWidth: 560, margin: '0 auto 32px', lineHeight: 1.7 }}>
            Find similar dermoscopy cases to support your clinical assessment. Compare lesion characteristics with validated reference images.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/search" className="btn btn-primary btn-lg"><Search size={18} /> Search Cases</Link>
            <Link to="/database" className="btn btn-outline btn-lg"><Database size={18} /> Browse Database</Link>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text3)', marginBottom: 20 }}>Database Statistics</h2>
        {stats ? <StatsCards stats={stats} /> : <LoadingSpinner label="Loading statistics..." />}
      </section>

      {/* Features */}
      <section style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text3)', marginBottom: 20 }}>How It Works</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
          {features.map((f, i) => {
            const Icon = f.icon
            return (
              <motion.div key={f.title} className="card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
                <div style={{ width: 44, height: 44, borderRadius: 12, background: `${f.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
                  <Icon size={22} color={f.color} />
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 8 }}>{f.title}</h3>
                <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.6 }}>{f.desc}</p>
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* Workflow */}
      <section style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text3)', marginBottom: 20 }}>Clinical Workflow</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          {steps.map((step, i) => (
            <motion.div key={step.num} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
              style={{ display: 'flex', gap: 14, padding: 16, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 16, color: 'white', flexShrink: 0 }}>
                {step.num}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--white)', marginBottom: 3 }}>{step.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text3)' }}>{step.desc}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
        style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 14, padding: '24px 28px' }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'start' }}>
          <Shield size={20} color="var(--yellow)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--yellow)', marginBottom: 8 }}>Clinical Use Notice</h3>
            <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
              This tool is designed to assist healthcare professionals by providing visual case references. It is <strong style={{ color: 'var(--white)' }}>not a substitute for clinical judgment</strong> or professional medical diagnosis.
            </p>
          </div>
        </div>
      </motion.section>
    </div>
  )
}
