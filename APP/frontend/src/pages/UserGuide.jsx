import React from 'react'
import { motion } from 'framer-motion'
import { BookOpen, Upload, Search, Eye, Download, AlertCircle } from 'lucide-react'

const steps = [
  {
    num: '1',
    title: 'Select Reference Database',
    desc: 'Choose between ISIC 2020 (33K cases, binary classification) or ISIC 2019 (25K cases, detailed diagnostic categories).',
    icon: Search,
  },
  {
    num: '2',
    title: 'Upload Dermoscopy Image',
    desc: 'Click the upload area or drag and drop your dermoscopy image. Supported formats: JPG, PNG. Ensure the image is clear and properly focused.',
    icon: Upload,
  },
  {
    num: '3',
    title: 'Set Number of Results',
    desc: 'Choose how many similar cases you want to see (5, 10, or 20). More results provide broader reference but may include less similar cases.',
    icon: Eye,
  },
  {
    num: '4',
    title: 'Review Similar Cases',
    desc: 'The system displays cases ranked by visual similarity. Each result shows the lesion image, classification (benign/malignant), and a similarity score.',
    icon: Search,
  },
  {
    num: '5',
    title: 'View Case Details',
    desc: 'Click on any result to see detailed information including patient demographics, anatomical location, diagnosis, and similarity metrics.',
    icon: Eye,
  },
  {
    num: '6',
    title: 'Clinical Assessment',
    desc: 'Use the reference cases to support your clinical evaluation. Compare visual characteristics and consider the diagnostic patterns in similar cases.',
    icon: AlertCircle,
  },
]

const tips = [
  { title: 'Image Quality', desc: 'Use high-quality dermoscopy images with good lighting and focus for best results.' },
  { title: 'Multiple Searches', desc: 'Try searching with different images of the same lesion (different angles, lighting) to get comprehensive references.' },
  { title: 'Database Selection', desc: 'ISIC 2020 is better for binary classification (benign/malignant). ISIC 2019 provides more detailed diagnostic categories.' },
  { title: 'Similarity Scores', desc: 'Higher similarity scores indicate closer visual matches, but always consider clinical context.' },
  { title: 'Reference Only', desc: 'Results are for reference and education. Always base final diagnosis on comprehensive clinical evaluation.' },
]

export default function UserGuide() {
  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <BookOpen size={24} color="var(--accent)" />
          <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--white)' }}>User Guide</h1>
        </div>
        <p style={{ fontSize: 15, color: 'var(--text2)' }}>Step-by-step instructions for using the dermoscopy case finder</p>
      </div>

      {/* Steps */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 20 }}>How to Search for Similar Cases</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {steps.map((step, i) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.num}
                className="card"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                style={{ display: 'flex', gap: 20, alignItems: 'start' }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 20, color: 'white' }}>
                    {step.num}
                  </div>
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={20} color="var(--accent)" />
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 8 }}>{step.title}</h3>
                  <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>{step.desc}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Tips */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 20 }}>Best Practices & Tips</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {tips.map((tip, i) => (
            <motion.div
              key={tip.title}
              className="card"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              style={{ background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.15)' }}
            >
              <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent)', marginBottom: 8 }}>{tip.title}</h4>
              <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{tip.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Understanding Results */}
      <motion.div
        className="card"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        style={{ marginBottom: 40 }}
      >
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 16 }}>Understanding Your Results</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>Similarity Score</h4>
            <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
              Displayed as a percentage (0-100%). Higher scores indicate closer visual matches. Scores above 80% suggest very similar visual characteristics.
            </p>
          </div>
          <div>
            <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>Classification Labels</h4>
            <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
              <span className="badge badge-benign" style={{ marginRight: 8 }}>Benign</span> indicates non-cancerous lesions.
              <span className="badge badge-malignant" style={{ marginLeft: 8, marginRight: 8 }}>Malignant</span> indicates cancerous lesions.
              These are reference classifications from the database, not diagnoses of your uploaded image.
            </p>
          </div>
          <div>
            <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--white)', marginBottom: 6 }}>Case Metadata</h4>
            <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
              Each case includes patient age, sex, anatomical location, and diagnosis. Use this information to understand the clinical context of similar cases.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Disclaimer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 12, padding: '20px 24px', display: 'flex', gap: 14 }}
      >
        <AlertCircle size={20} color="var(--yellow)" style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--yellow)', marginBottom: 6 }}>Important Reminder</h4>
          <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            This tool provides reference cases based on visual similarity only. It does not diagnose, recommend treatment, or replace clinical judgment. Always conduct a comprehensive clinical evaluation including patient history, physical examination, and appropriate diagnostic procedures before making any clinical decisions.
          </p>
        </div>
      </motion.div>
    </div>
  )
}
