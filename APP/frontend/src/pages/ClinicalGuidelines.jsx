import React from 'react'
import { motion } from 'framer-motion'
import { FileText, AlertTriangle, CheckCircle, XCircle, Shield, Users } from 'lucide-react'

const dos = [
  'Use this tool as a reference and educational resource',
  'Compare multiple similar cases to identify patterns',
  'Consider patient history and clinical presentation alongside visual findings',
  'Verify findings with appropriate diagnostic procedures (biopsy, histopathology)',
  'Use high-quality dermoscopy images for accurate matching',
  'Document your clinical reasoning and decision-making process',
  'Consult with colleagues or specialists when uncertain',
  'Stay updated with current dermatology guidelines and literature',
]

const donts = [
  'Do not use this tool as the sole basis for diagnosis',
  'Do not skip comprehensive clinical evaluation',
  'Do not ignore patient symptoms or clinical history',
  'Do not delay necessary biopsies or referrals',
  'Do not share patient images without proper consent and de-identification',
  'Do not use low-quality or unclear images',
  'Do not assume similar appearance means identical diagnosis',
  'Do not bypass established clinical protocols',
]

const scenarios = [
  {
    title: 'Suspicious Pigmented Lesion',
    desc: 'Use the tool to compare with known melanoma and nevus cases. Look for ABCDE criteria patterns in similar cases. Always perform biopsy for definitive diagnosis.',
    icon: AlertTriangle,
    color: '#f43f5e',
  },
  {
    title: 'Educational Case Review',
    desc: 'Medical students and residents can explore diverse cases to learn dermoscopy patterns. Compare classic presentations with atypical variants.',
    icon: Users,
    color: '#3b82f6',
  },
  {
    title: 'Second Opinion Preparation',
    desc: 'Before referring a case, review similar cases to better articulate your concerns and provide context to the consulting specialist.',
    icon: FileText,
    color: '#10b981',
  },
]

export default function ClinicalGuidelines() {
  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <Shield size={24} color="var(--accent)" />
          <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--white)' }}>Clinical Guidelines</h1>
        </div>
        <p style={{ fontSize: 15, color: 'var(--text2)' }}>Best practices for using this tool in clinical practice</p>
      </div>

      {/* Introduction */}
      <motion.div
        className="card"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: 32, background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.15)' }}
      >
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent)', marginBottom: 12 }}>Clinical Context</h2>
        <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.8, marginBottom: 12 }}>
          This dermoscopy case finder is designed to support clinical decision-making by providing visual reference cases. It uses advanced image analysis to find similar cases from validated medical databases.
        </p>
        <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.8 }}>
          The tool is intended for use by qualified healthcare professionals (dermatologists, primary care physicians, medical students under supervision) as part of a comprehensive clinical evaluation.
        </p>
      </motion.div>

      {/* Do's and Don'ts */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 20 }}>Clinical Do's and Don'ts</h2>
        <div className="guidelines-grid">
          {/* Do's */}
          <motion.div
            className="card"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            style={{ background: 'rgba(16,185,129,0.04)', border: '1px solid rgba(16,185,129,0.15)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <CheckCircle size={20} color="var(--green)" />
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--green)' }}>Recommended Practices</h3>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {dos.map((item, i) => (
                <li key={i} style={{ display: 'flex', gap: 10, fontSize: 14, color: 'var(--text2)', lineHeight: 1.6 }}>
                  <CheckCircle size={16} color="var(--green)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Don'ts */}
          <motion.div
            className="card"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            style={{ background: 'rgba(244,63,94,0.04)', border: '1px solid rgba(244,63,94,0.15)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <XCircle size={20} color="var(--red)" />
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--red)' }}>Avoid These Practices</h3>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {donts.map((item, i) => (
                <li key={i} style={{ display: 'flex', gap: 10, fontSize: 14, color: 'var(--text2)', lineHeight: 1.6 }}>
                  <XCircle size={16} color="var(--red)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>

      {/* Clinical Scenarios */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 20 }}>Clinical Use Scenarios</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {scenarios.map((scenario, i) => {
            const Icon = scenario.icon
            return (
              <motion.div
                key={scenario.title}
                className="card"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                style={{ display: 'flex', gap: 16, alignItems: 'start' }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: `${scenario.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={24} color={scenario.color} />
                </div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 8 }}>{scenario.title}</h3>
                  <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>{scenario.desc}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Limitations */}
      <motion.div
        className="card"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        style={{ marginBottom: 32 }}
      >
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 16 }}>System Limitations</h2>
        <ul style={{ display: 'flex', flexDirection: 'column', gap: 12, paddingLeft: 20 }}>
          <li style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--white)' }}>Visual similarity only:</strong> The system matches based on appearance, not clinical diagnosis. Similar-looking lesions may have different diagnoses.
          </li>
          <li style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--white)' }}>Database limitations:</strong> Results are limited to cases in the ISIC 2019/2020 databases. Rare conditions may have few or no similar cases.
          </li>
          <li style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--white)' }}>Image quality dependent:</strong> Poor quality images will produce less accurate matches.
          </li>
          <li style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--white)' }}>No clinical context:</strong> The system does not consider patient history, symptoms, or other clinical factors.
          </li>
          <li style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--white)' }}>Not validated for diagnosis:</strong> This tool has not undergone clinical validation studies for diagnostic accuracy.
          </li>
        </ul>
      </motion.div>

      {/* Legal Disclaimer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 12, padding: '20px 24px', display: 'flex', gap: 14 }}
      >
        <AlertTriangle size={20} color="var(--yellow)" style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--yellow)', marginBottom: 6 }}>Medical & Legal Disclaimer</h4>
          <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7, marginBottom: 10 }}>
            This tool is provided for educational and reference purposes only. It is not a medical device and has not been approved by regulatory authorities for clinical diagnosis.
          </p>
          <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.7 }}>
            Healthcare professionals using this tool assume full responsibility for all clinical decisions. The developers and providers of this tool assume no liability for clinical outcomes, misdiagnosis, or any adverse events resulting from its use.
          </p>
        </div>
      </motion.div>
    </div>
  )
}
