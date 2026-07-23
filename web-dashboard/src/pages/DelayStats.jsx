import { useState, useEffect, useRef } from 'react'
import { fetchJSON } from '../api'
import './DelayStats.css'

function useCountUp(target, durationMs = 900, decimals = 0) {
  const [value, setValue] = useState(0)
  const startRef = useRef(null)

  useEffect(() => {
    if (target == null) return
    let frame

    function step(timestamp) {
      if (startRef.current === null) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / durationMs, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(target * eased)
      if (progress < 1) frame = requestAnimationFrame(step)
    }

    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [target, durationMs])

  return decimals > 0 ? value.toFixed(decimals) : Math.round(value)
}

function DelayStats() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchJSON('/stats/delays')
      .then((data) => {
        if (!cancelled) {
          setStats(data)
          requestAnimationFrame(() => setRevealed(true))
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const hasDistribution =
    stats &&
    stats.median_minutes != null &&
    stats.p25_minutes != null &&
    stats.p75_minutes != null

  const median = useCountUp(hasDistribution ? stats.median_minutes : null, 900, 1)
  const mean = useCountUp(hasDistribution ? stats.mean_minutes : null, 900, 2)
  const p25 = useCountUp(hasDistribution ? stats.p25_minutes : null, 900, 2)
  const p75 = useCountUp(hasDistribution ? stats.p75_minutes : null, 900, 2)
  const rangeMinAnim = useCountUp(hasDistribution ? stats.min_minutes : null, 900, 0)
  const rangeMaxAnim = useCountUp(hasDistribution ? stats.max_minutes : null, 900, 0)

  if (error) {
    return (
      <div>
        <h2>Delay Stats</h2>
        <p className="stats-error">
          Couldn't reach the API — is the backend running on localhost:8000?
        </p>
      </div>
    )
  }

  if (!stats) {
    return (
      <div>
        <h2>Delay Stats</h2>
        <p className="page-placeholder">Loading delay distribution…</p>
      </div>
    )
  }

  if (!hasDistribution) {
    return (
      <div>
        <h2>Delay Stats</h2>
        <p className="page-placeholder">
          {stats.message || 'Not enough delay data yet to compute a distribution.'}
        </p>
      </div>
    )
  }

  const rangeMin = Math.min(stats.min_minutes, 0)
  const rangeMax = stats.max_minutes
  const span = rangeMax - rangeMin || 1
  const pct = (v) => ((v - rangeMin) / span) * 100

  return (
    <div>
      <h2>Delay Stats</h2>
      <p className="stats-count">
        {stats.count} physical flights with usable delay data, out of{' '}
        {stats.physical_flights_total.toLocaleString()} tracked
      </p>

      <div className="stats-hero-row">
        <div className="stat-card stat-card-hero">
          <span className="stat-label">Median delay</span>
          <span className="stat-value-hero">
            {median}<span className="stat-unit-hero">m</span>
          </span>
        </div>

        <div className="stats-support-grid">
          <div className="stat-card">
            <span className="stat-label">Mean delay</span>
            <span className="stat-value">
              {mean}<span className="stat-unit">m</span>
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">P25 – P75 spread</span>
            <span className="stat-value">
              {p25}<span className="stat-unit">–{p75}m</span>
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Range</span>
            <span className="stat-value">
              {rangeMinAnim}<span className="stat-unit">m to {rangeMaxAnim}m</span>
            </span>
          </div>
        </div>
      </div>

      <div className="distribution-panel">
        <span className="distribution-title">Distribution</span>
        <div className="distribution-track">
          <div
            className={`distribution-fill ${revealed ? 'distribution-fill-in' : ''}`}
          />
          <div
            className={`distribution-iqr-band ${revealed ? 'distribution-iqr-in' : ''}`}
            style={{
              left: `${pct(stats.p25_minutes)}%`,
              width: `${pct(stats.p75_minutes) - pct(stats.p25_minutes)}%`,
            }}
          />
          <div className="distribution-zero-line" style={{ left: `${pct(0)}%` }} />
          <div
            className={`distribution-marker distribution-marker-median ${revealed ? 'distribution-marker-in' : ''}`}
            style={{ left: `${pct(stats.median_minutes)}%` }}
            title={`Median: ${stats.median_minutes}m`}
          >
            <span className="distribution-marker-label">{stats.median_minutes}m</span>
          </div>
        </div>
        <div className="distribution-labels">
          <span>{stats.min_minutes}m</span>
          <span>0m</span>
          <span>{stats.max_minutes}m</span>
        </div>
      </div>

      {stats.physical_flights_excluded_anomalous > 0 && (
        <div className={`transparency-panel ${revealed ? 'transparency-in' : ''}`}>
          <span className="transparency-icon">⚠</span>
          <div>
            <span className="transparency-title">Data quality note</span>
            <p className="transparency-text">{stats.message}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default DelayStats