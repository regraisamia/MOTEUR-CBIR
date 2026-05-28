import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, MessageSquare, Phone, MapPin, Send, CheckCircle } from 'lucide-react'
import { useApp } from '../AppContext'
import { t } from '../i18n'

export default function Contact() {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' })
  const [submitted, setSubmitted] = useState(false)
  const { lang } = useApp()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('http://localhost:8000/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const result = await response.json()
      if (response.ok) {
        setSubmitted(true)
        setTimeout(() => {
          setSubmitted(false)
          setFormData({ name: '', email: '', subject: '', message: '' })
        }, 3000)
      } else {
        alert('Error: ' + result.detail)
      }
    } catch (error) {
      alert('Failed to send message. Please try again.')
    }
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <MessageSquare size={24} color="var(--accent)" />
          <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--white)' }}>{t(lang, 'contact_title')}</h1>
        </div>
        <p style={{ fontSize: 15, color: 'var(--text2)' }}>{t(lang, 'contact_sub')}</p>
      </div>

      <div className="contact-grid">
        {/* Contact Form */}
        <motion.div
          className="card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--white)', marginBottom: 16 }}>{t(lang, 'contact_send')}</h2>
          
          {submitted ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              style={{ textAlign: 'center', padding: '40px 20px' }}
            >
              <CheckCircle size={48} color="var(--green)" style={{ margin: '0 auto 16px' }} />
              <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)', marginBottom: 8 }}>{t(lang, 'contact_sent_title')}</h3>
              <p style={{ fontSize: 14, color: 'var(--text2)' }}>{t(lang, 'contact_sent_sub')}</p>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>{t(lang, 'contact_name')} *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none' }}
                  placeholder="Dr. John Smith"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>{t(lang, 'contact_email')} *</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none' }}
                  placeholder="john.smith@hospital.com"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>{t(lang, 'contact_subject')} *</label>
                <select
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  required
                  className="select-styled"
                  style={{ width: '100%' }}
                >
                  <option value="">{t(lang, 'contact_subject')}</option>
                  <option value="technical">{t(lang, 'contact_subject_technical')}</option>
                  <option value="feedback">{t(lang, 'contact_subject_feedback')}</option>
                  <option value="feature">{t(lang, 'contact_subject_feature')}</option>
                  <option value="question">{t(lang, 'contact_subject_question')}</option>
                  <option value="other">{t(lang, 'contact_subject_other')}</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text2)', marginBottom: 6 }}>{t(lang, 'contact_message')} *</label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  required
                  rows={6}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface2)', color: 'var(--text)', fontSize: 14, outline: 'none', resize: 'vertical', fontFamily: 'inherit' }}
                  placeholder="Describe your issue or feedback..."
                />
              </div>
              <button type="submit" className="btn btn-primary" style={{ justifyContent: 'center' }}>
                <Send size={16} /> {t(lang, 'contact_btn')}
              </button>
            </form>
          )}
        </motion.div>

        {/* Contact Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <motion.div
            className="card"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 16 }}>Support Information</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'start' }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Mail size={18} color="var(--accent)" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text3)', marginBottom: 4 }}>Email Support</div>
                  <div style={{ fontSize: 14, color: 'var(--text)', fontWeight: 600 }}>support@dermfinder.com</div>
                  <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 2 }}>Response within 24-48 hours</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, alignItems: 'start' }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(16,185,129,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Phone size={18} color="var(--green)" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text3)', marginBottom: 4 }}>Phone Support</div>
                  <div style={{ fontSize: 14, color: 'var(--text)', fontWeight: 600 }}>+1 (555) 123-4567</div>
                  <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 2 }}>Mon-Fri, 9AM-5PM EST</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, alignItems: 'start' }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(245,158,11,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <MapPin size={18} color="var(--yellow)" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text3)', marginBottom: 4 }}>Address</div>
                  <div style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.6 }}>
                    Medical AI Research Lab<br />
                    123 Healthcare Drive<br />
                    Medical District, MD 12345
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="card"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            style={{ background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.15)' }}
          >
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent)', marginBottom: 12 }}>Quick Help</h3>
            <ul style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingLeft: 20, margin: 0 }}>
              <li style={{ fontSize: 14, color: 'var(--text2)' }}>Check the <a href="/user-guide" style={{ color: 'var(--accent)', textDecoration: 'none' }}>User Guide</a> for step-by-step instructions</li>
              <li style={{ fontSize: 14, color: 'var(--text2)' }}>Review <a href="/clinical-guidelines" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Clinical Guidelines</a> for best practices</li>
              <li style={{ fontSize: 14, color: 'var(--text2)' }}>Visit the <a href="/about" style={{ color: 'var(--accent)', textDecoration: 'none' }}>About</a> page for system information</li>
            </ul>
          </motion.div>

          <motion.div
            className="card"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--white)', marginBottom: 12 }}>Common Issues</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <details style={{ cursor: 'pointer' }}>
                <summary style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>Image upload not working</summary>
                <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6, paddingLeft: 16 }}>
                  Ensure your image is in JPG or PNG format and under 10MB. Try a different browser if the issue persists.
                </p>
              </details>
              <details style={{ cursor: 'pointer' }}>
                <summary style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>No results returned</summary>
                <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6, paddingLeft: 16 }}>
                  Check that your image is a clear dermoscopy image. Low quality or non-dermoscopy images may not return results.
                </p>
              </details>
              <details style={{ cursor: 'pointer' }}>
                <summary style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>Slow search performance</summary>
                <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6, paddingLeft: 16 }}>
                  Check your internet connection. Large images may take longer to upload. Try reducing image size if needed.
                </p>
              </details>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
