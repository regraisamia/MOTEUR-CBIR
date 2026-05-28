import React from 'react'
import { motion } from 'framer-motion'
import { Brain, Database, Zap, Shield, AlertTriangle, BookOpen, Users, Award } from 'lucide-react'

const capabilities = [
  { icon: Database, title: 'Extensive Reference Library', desc: 'Over 58,000 validated dermoscopy images from international dermatology databases (ISIC 2019 & 2020).', color: '#3b82f6' },
  { icon: Brain, title: 'Advanced Image Analysis', desc: 'Deep learning algorithms analyze visual patterns to find cases with similar characteristics.', color: '#8b5cf6' },
  { icon: Zap, title: 'Instant Results', desc: 'Get similar case recommendations in under a second to support your clinical workflow.', color: '#f59e0b' },
  { icon: Shield, title: 'Clinical Metadata', desc: 'Each case includes patient demographics, anatomical site, and diagnostic classification.', color: '#10b981' },
]

const useCases = [
  { icon: Users, title: 'Clinical Education', desc: 'Medical students and residents can explore diverse dermoscopy cases for learning.' },
  { icon: Award, title: 'Diagnostic Support', desc: 'Experienced clinicians can reference similar cases when encountering challenging lesions.' },
  { icon: BookOpen, title: 'Case Documentation', desc: 'Compare current cases with historical references for clinical documentation.' },
]

export default function About() {
  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--white)', marginBottom: 8 }}>About This Tool</h1>
        <p style={{ fontSize: 15, color: 'var(--text2)' }}>Clinical decision support for dermoscopy image analysis</p>
      </div>

      {/* Overview */}
      <motion.div className="card" style={{ marginBottom: 24 }} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 12 }}>Purpose</h2>
        <p style={{ color: 'var(--text2)', lineHeight: 1.8, marginBottom: 12 }}>
          This tool helps healthcare professionals find visually similar dermoscopy cases from validated medical databases. When you upload an image, the system searches through tens of thousands of reference cases to find those with similar visual characteristics.
        </p>
        <p style={{ color: 'var(--text2)', lineHeight: 1.8 }}>
          The goal is to provide quick access to reference cases that may assist in clinical assessment, education, and documentation — not to replace professional medical judgment.
        </p>
      </motion.div>

      {/* Capabilities */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text3)', marginBottom: 16 }}>Key Capabilities</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16 }}>
          {capabilities.map((c, i) => {
            const Icon = c.icon
            return (
              <motion.div
                key={c.title}
                className="card"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
              >
                <div style={{ width: 44, height: 44, borderRadius: 12, background: `${c.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                  <Icon size={22} color={c.color} />
                </div>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>{c.title}</h3>
                <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{c.desc}</p>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Use Cases */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text3)', marginBottom: 16 }}>Clinical Applications</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
          {useCases.map((u, i) => {
            const Icon = u.icon
            return (
              <motion.div
                key={u.title}
                className="card"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                style={{ display: 'flex', gap: 14 }}
              >
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={20} color="var(--accent)" />
                </div>
                <div>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>{u.title}</h3>
                  <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{u.desc}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Technical Note */}
      <motion.div
        className="card"
        style={{ marginBottom: 24, background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.15)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Brain size={18} /> How It Works
        </h3>
        <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
          The system uses deep learning algorithms trained on medical images to analyze visual patterns. When you upload an image, it extracts key visual features and compares them against our reference database to find the most similar cases. The entire process takes less than a second.
        </p>
      </motion.div>

      {/* Data Sources */}
      <motion.div className="card" style={{ marginBottom: 24 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 10 }}>Data Sources</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--white)', marginBottom: 4 }}>ISIC 2020 Challenge Dataset</div>
            <div style={{ fontSize: 13, color: 'var(--text2)' }}>33,126 dermoscopy images with binary classification (benign/malignant)</div>
          </div>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--white)', marginBottom: 4 }}>ISIC 2019 Challenge Dataset</div>
            <div style={{ fontSize: 13, color: 'var(--text2)' }}>25,331 dermoscopy images with detailed diagnostic categories (melanoma, nevus, basal cell carcinoma, etc.)</div>
          </div>
        </div>
      </motion.div>

      {/* Disclaimer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 12, padding: '20px 24px', display: 'flex', gap: 14 }}
      >
        <AlertTriangle size={20} color="var(--yellow)" style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--yellow)', marginBottom: 6 }}>Important Medical Disclaimer</h4>
          <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            This tool is designed to <strong style={{ color: 'var(--white)' }}>assist</strong> healthcare professionals, not replace them. It provides reference cases based on visual similarity only and does not perform diagnosis. All clinical decisions must be made by qualified healthcare providers based on comprehensive patient evaluation, clinical history, and appropriate diagnostic procedures. This system is for educational and reference purposes in a clinical setting.
          </p>
        </div>
      </motion.div>
    </div>
  )
}
