import React from 'react'
import { NavLink } from 'react-router-dom'
import { Microscope, AlertTriangle } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <NavLink to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
            <div className="navbar-brand-icon"><Microscope size={16} color="#fff" /></div>
            <span className="navbar-brand-text">Derm<span>Finder</span></span>
          </NavLink>
          <p>A clinical decision support tool for dermoscopy image analysis. Find similar reference cases from validated medical databases.</p>
        </div>
        <div className="footer-col">
          <h4>Navigation</h4>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/search">Search Cases</NavLink>
          <NavLink to="/database">Browse Database</NavLink>
          <NavLink to="/about">About</NavLink>
        </div>
        <div className="footer-col">
          <h4>Resources</h4>
          <a href="https://www.isic-archive.com" target="_blank" rel="noopener noreferrer">ISIC Archive</a>
          <NavLink to="/user-guide">User Guide</NavLink>
          <NavLink to="/clinical-guidelines">Clinical Guidelines</NavLink>
          <NavLink to="/contact">Contact Support</NavLink>
        </div>
      </div>
      <div className="footer-bottom">
        <p>© {new Date().getFullYear()} DermFinder — Clinical Decision Support Tool</p>
        <div className="footer-disclaimer">
          <AlertTriangle size={13} />
          For healthcare professional use only. Not a diagnostic device.
        </div>
      </div>
    </footer>
  )
}
