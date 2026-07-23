import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Nav from './components/Nav'
import Overview from './pages/Overview'
import Flights from './pages/Flights'
import DelayStats from './pages/DelayStats'
import CascadeRisk from './pages/CascadeRisk'
import Airports from './pages/Airports'
import { fetchJSON } from './api'
import './App.css'

const API_BASE = 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState('connecting') // 'connecting' | 'online' | 'offline'

  useEffect(() => {
    let cancelled = false

    async function checkHealth() {
      try {
        const data = await fetchJSON('/health')
        if (!cancelled) {
          setStatus(data.status === 'ok' ? 'online' : 'offline')
        }
      } catch {
        if (!cancelled) setStatus('offline')
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 15000) // re-check every 15s

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const statusLabel = {
    connecting: 'CONNECTING',
    online: 'LIVE',
    offline: 'OFFLINE',
  }[status]

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">
          <span className="topbar-logo">◎</span>
          <span className="topbar-title">SkyPulse</span>
        </div>
        <div className="topbar-status">
          <span className={`status-dot status-dot-${status}`} />
          <span className="status-label">{statusLabel}</span>
        </div>
      </header>

      <Nav />

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/flights" element={<Flights />} />
          <Route path="/delays" element={<DelayStats />} />
          <Route path="/cascade" element={<CascadeRisk />} />
          <Route path="/airports" element={<Airports />} />
        </Routes>
      </main>
    </div>
  )
}

export default App