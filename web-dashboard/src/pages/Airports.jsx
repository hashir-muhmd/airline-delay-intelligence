import RouteMap from '../components/RouteMap'
import { useState, useEffect, useMemo } from 'react'
import { fetchJSON } from '../api'
import './Airports.css'

function Airports() {
  const [airports, setAirports] = useState(null)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [showMap, setShowMap] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchJSON('/airports')
      .then((data) => {
        if (!cancelled) setAirports(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const { enriched, unenrichedCount } = useMemo(() => {
    if (!airports) return { enriched: [], unenrichedCount: 0 }

    const withNames = airports.filter((a) => a.name)
    const withoutNames = airports.filter((a) => !a.name)

    const q = search.trim().toUpperCase()
    const filtered = q
      ? withNames.filter((a) => {
          const haystack = `${a.code} ${a.name} ${a.city} ${a.country}`.toUpperCase()
          return haystack.includes(q)
        })
      : withNames

    // DOH hub first, then alphabetical by code
    const sorted = [...filtered].sort((a, b) => {
      if (a.is_hub) return -1
      if (b.is_hub) return 1
      return a.code.localeCompare(b.code)
    })

    return { enriched: sorted, unenrichedCount: withoutNames.length }
  }, [airports, search])

  if (error) {
    return (
      <div>
        <h2>Airports</h2>
        <p className="airports-error">
          Couldn't reach the API — is the backend running on localhost:8000?
        </p>
      </div>
    )
  }

  if (!airports) {
    return (
      <div>
        <h2>Airports</h2>
        <p className="page-placeholder">Loading airport data…</p>
      </div>
    )
  }

  return (
    <div>
      <h2>Airports</h2>
      <p className="airports-count">
        {enriched.length} airports
        {unenrichedCount > 0 && ` · ${unenrichedCount} referenced but not yet enriched`}
      </p>

      <div className="airports-search-row">
        <div className="airports-search-wrap">
          <input
            className="airports-search"
            type="text"
            placeholder="Search by code, name, city, or country"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <span className="airports-search-icon">⌕</span>
        </div>

        <button
          className={`airports-map-toggle ${showMap ? 'airports-map-toggle-active' : ''}`}
          onClick={() => setShowMap((s) => !s)}
        >
          {showMap ? 'Hide route map' : 'Show route map'}
        </button>
      </div>

      {showMap && enriched.length > 1 && (
        <RouteMap
          hub={enriched.find((a) => a.is_hub)}
          destinations={enriched.filter((a) => !a.is_hub)}
        />
      )}

      {enriched.length === 0 ? (
        <p className="page-placeholder">No airports match your search.</p>
      ) : (
        <div className="airports-grid">
          {enriched.map((a) => (
            <div
              key={a.code}
              className={`airport-card ${a.is_hub ? 'airport-card-hub' : ''}`}
            >
              <div className="airport-card-top">
                <span className="airport-code">{a.code}</span>
                {a.is_hub && <span className="airport-hub-badge">HUB</span>}
              </div>
              <span className="airport-name">{a.name}</span>
              <span className="airport-location">
                {a.city}{a.city && a.country ? ', ' : ''}{a.country}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Airports