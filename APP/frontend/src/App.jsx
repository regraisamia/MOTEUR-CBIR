import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

import Dashboard from './pages/Dashboard'
import SearchPage from './pages/SearchPage'
import DatabasePage from './pages/DatabasePage'
import ResultDetails from './pages/ResultDetails'
import About from './pages/About'
import UserGuide from './pages/UserGuide'
import ClinicalGuidelines from './pages/ClinicalGuidelines'
import Contact from './pages/Contact'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'
import History from './pages/History'
import AdminDashboard from './pages/AdminDashboard'

import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ScrollToTop from './components/ScrollToTop'
import LoadingSpinner from './components/LoadingSpinner'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AppLayout() {
  return (
    <div className="app">
      <ScrollToTop />
      <Navbar />
      <main className="page-content">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/database" element={<DatabasePage />} />
            <Route path="/result/:id" element={<ResultDetails />} />
            <Route path="/about" element={<About />} />
            <Route path="/user-guide" element={<UserGuide />} />
            <Route path="/clinical-guidelines" element={<ClinicalGuidelines />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/register" element={<Navigate to="/login" replace />} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
            <Route path="/admin-dashboard" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
          </Routes>
        </ErrorBoundary>
      </main>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/*" element={<AppLayout />} />
    </Routes>
  )
}
