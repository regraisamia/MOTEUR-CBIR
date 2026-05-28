import React from 'react'

export default function LoadingSpinner({ size = 36, label = 'Loading...' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: 32 }}>
      <div className="spinner" style={{ width: size, height: size }} />
      {label && <p style={{ color: 'var(--text3)', fontSize: 14 }}>{label}</p>}
    </div>
  )
}
