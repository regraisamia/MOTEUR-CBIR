import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      fetch('http://localhost:8000/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.ok ? r.json() : null)
        .then(u => { setUser(u); setLoading(false) })
        .catch(() => { localStorage.removeItem('token'); setToken(null); setLoading(false) })
    } else {
      setLoading(false)
    }
  }, [token])

  const login = (tok, u) => {
    localStorage.setItem('token', tok)
    setToken(tok)
    setUser(u)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const updateUser = (u) => setUser(u)

  const canAnnotate   = user && (user.role === 'admin' || ['resident','senior','professor'].includes(user.level))
  const canManageUsers = user && (user.role === 'admin' || user.level === 'professor')
  const canViewAll    = user && (user.role === 'admin' || user.level === 'professor')

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, updateUser, canAnnotate, canManageUsers, canViewAll }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
