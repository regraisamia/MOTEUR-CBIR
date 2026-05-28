import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Microscope, Menu, X, Search, User, LogOut, History, Shield, ChevronDown } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const LEVEL_LABELS = { intern: 'Intern', resident: 'Resident', senior: 'Senior', professor: 'Professor' }
const LEVEL_COLORS = { intern: '#94a3b8', resident: '#3b82f6', senior: '#10b981', professor: '#f59e0b' }

export default function Navbar() {
  const { user, logout, canManageUsers } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const handleLogout = () => { logout(); navigate('/login') }

  const links = [
    { to: '/', label: 'Home', exact: true },
    { to: '/search', label: 'Search Cases' },
    { to: '/database', label: 'Browse Database' },
    { to: '/about', label: 'About' },
  ]

  return (
    <>
      <header className="navbar">
        <NavLink to="/" className="navbar-brand">
          <div className="navbar-brand-icon"><Microscope size={18} color="#fff" /></div>
          <span className="navbar-brand-text">Derm<span>Finder</span></span>
        </NavLink>

        <nav className="navlinks">
          {links.map(l => (
            <NavLink key={l.to} to={l.to} end={l.exact} className={({ isActive }) => isActive ? 'active' : ''}>
              {l.label}
            </NavLink>
          ))}
          {user && <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>My Activity</NavLink>}
          {canManageUsers && <NavLink to="/admin-dashboard" className={({ isActive }) => isActive ? 'active' : ''}>Management</NavLink>}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {user ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setUserMenuOpen(o => !o)}
                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', borderRadius: 10, background: 'var(--surface)', border: '1px solid var(--border)', cursor: 'pointer', color: 'var(--text)' }}
              >
                <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, color: 'white' }}>
                  {user.name?.charAt(0).toUpperCase()}
                </div>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--white)', lineHeight: 1.2 }}>{user.name}</div>
                  <div style={{ fontSize: 11, color: LEVEL_COLORS[user.level] || 'var(--text3)' }}>
                    {user.role === 'admin' ? 'Admin' : LEVEL_LABELS[user.level]}
                  </div>
                </div>
                <ChevronDown size={14} color="var(--text3)" />
              </button>

              {userMenuOpen && (
                <div
                  style={{ position: 'absolute', right: 0, top: '110%', background: 'var(--surface)', border: '1px solid var(--border2)', borderRadius: 12, padding: 8, minWidth: 180, zIndex: 200, boxShadow: 'var(--shadow-lg)' }}
                  onMouseLeave={() => setUserMenuOpen(false)}
                >
                  {[
                    { icon: User, label: 'My Profile', to: '/profile' },
                    { icon: History, label: 'My Activity', to: '/history' },
                    ...(canManageUsers ? [{ icon: Shield, label: 'Management', to: '/admin-dashboard' }] : []),
                  ].map(item => {
                    const Icon = item.icon
                    return (
                      <button key={item.to} onClick={() => { navigate(item.to); setUserMenuOpen(false) }}
                        style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px', borderRadius: 8, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text2)', fontSize: 14, fontWeight: 500, textAlign: 'left' }}
                        onMouseEnter={e => e.currentTarget.style.background = 'var(--surface2)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'none'}
                      >
                        <Icon size={15} /> {item.label}
                      </button>
                    )
                  })}
                  <div style={{ height: 1, background: 'var(--border)', margin: '6px 0' }} />
                  <button onClick={handleLogout}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px', borderRadius: 8, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--red)', fontSize: 14, fontWeight: 500 }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--red-bg)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}
                  >
                    <LogOut size={15} /> Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <NavLink to="/login" className="btn btn-primary btn-sm">Sign In</NavLink>
            </div>
          )}

          <button className="nav-hamburger" onClick={() => setMobileOpen(o => !o)}>
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </header>

      {mobileOpen && (
        <nav className="nav-mobile">
          {links.map(l => (
            <NavLink key={l.to} to={l.to} end={l.exact} className={({ isActive }) => isActive ? 'active' : ''} onClick={() => setMobileOpen(false)}>{l.label}</NavLink>
          ))}
          {user && <NavLink to="/history" onClick={() => setMobileOpen(false)}>My Activity</NavLink>}
          {user && <NavLink to="/profile" onClick={() => setMobileOpen(false)}>Profile</NavLink>}
          {canManageUsers && <NavLink to="/admin-dashboard" onClick={() => setMobileOpen(false)}>Management</NavLink>}
          {user
            ? <button onClick={handleLogout} style={{ background: 'none', border: 'none', color: 'var(--red)', padding: '10px 14px', textAlign: 'left', cursor: 'pointer', fontSize: 14, fontWeight: 500 }}>Sign Out</button>
            : <NavLink to="/login" onClick={() => setMobileOpen(false)}>Sign In</NavLink>
          }
        </nav>
      )}
    </>
  )
}
