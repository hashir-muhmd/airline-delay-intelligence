import { useState, useEffect, useMemo, useRef } from 'react'
import { fetchJSON } from '../api'
import './Flights.css'

function formatTime(iso) {
  if (!iso) return '—'
  // Ingestion now stores true UTC (fixed at the source, plus a one-time
  // historical backfill for DOH-side fields — see project log open item #1).
  // dohEventTime() below only ever reads the DOH-side field for a given
  // flight, so a flat +3h (Asia/Qatar, no DST) is always correct here.
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const doh = new Date(date.getTime() + 3 * 60 * 60 * 1000)
  const month = String(doh.getUTCMonth() + 1).padStart(2, '0')
  const day = String(doh.getUTCDate()).padStart(2, '0')
  const hour = String(doh.getUTCHours()).padStart(2, '0')
  const minute = String(doh.getUTCMinutes()).padStart(2, '0')
  return `${month} ${day} ${hour}:${minute} AST`
}

// Returns the Doha-side event time (as a sortable Date-ish string) and
// whether it's a departure from or arrival into DOH.
function dohEventTime(flight) {
  if (flight.origin === 'DOH') {
    return { time: flight.scheduled_departure, kind: 'DEP' }
  }
  if (flight.destination === 'DOH') {
    return { time: flight.scheduled_arrival, kind: 'ARR' }
  }
  return { time: flight.scheduled_departure, kind: '—' }
}

function DelayBadge({ delayMinutes, status }) {
  if (delayMinutes == null) {
    return <span className="badge badge-neutral">{status}</span>
  }
  if (delayMinutes <= 15) {
    return <span className="badge badge-green">On time</span>
  }
  if (delayMinutes <= 60) {
    return <span className="badge badge-amber">+{delayMinutes}m</span>
  }
  return <span className="badge badge-red">+{delayMinutes}m</span>
}

function FlightNumbers({ raw, count }) {
  const [expanded, setExpanded] = useState(false)
  const numbers = raw.split(',').map((s) => s.trim())
  const primary = numbers[0]

  if (count <= 1) {
    return <span className="flight-number-primary">{primary}</span>
  }

  return (
    <div className="flight-numbers">
      <span className="flight-number-primary">{primary}</span>
      <button
        className="flight-numbers-toggle"
        onClick={() => setExpanded((e) => !e)}
      >
        {expanded ? 'hide' : `+${count - 1} more`}
      </button>
      {expanded && (
        <div className="flight-numbers-list">
          {numbers.slice(1).join(', ')}
        </div>
      )}
    </div>
  )
}

function StatusDropdown({ value, options, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const label = value === 'all'
    ? 'All statuses'
    : value.charAt(0).toUpperCase() + value.slice(1)

  return (
    <div className="status-dropdown" ref={ref}>
      <button
        className="status-dropdown-trigger"
        onClick={() => setOpen((o) => !o)}
      >
        <span>{label}</span>
        <span className={`status-dropdown-caret ${open ? 'status-dropdown-caret-open' : ''}`}>▾</span>
      </button>
      {open && (
        <div className="status-dropdown-menu">
          <button
            className={`status-dropdown-item ${value === 'all' ? 'status-dropdown-item-active' : ''}`}
            onClick={() => {
              onChange('all')
              setOpen(false)
            }}
          >
            All statuses
          </button>
          {options.map((s) => (
            <button
              key={s}
              className={`status-dropdown-item ${value === s ? 'status-dropdown-item-active' : ''}`}
              onClick={() => {
                onChange(s)
                setOpen(false)
              }}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function Flights() {
  const [flights, setFlights] = useState(null)
  const [error, setError] = useState(null)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [searching, setSearching] = useState(false)
  const [directionFilter, setDirectionFilter] = useState('all') // 'all' | 'DEP' | 'ARR'
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    let cancelled = false
    fetchJSON('/flights/physical')
      .then((data) => {
        if (!cancelled) setFlights(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    setSearching(true)
    const timer = setTimeout(() => {
      setSearch(searchInput)
      setSearching(false)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const statusOptions = useMemo(() => {
    if (!flights) return []
    return [...new Set(flights.map((f) => f.status))].sort()
  }, [flights])

  const processed = useMemo(() => {
    if (!flights) return []

    const withMeta = flights.map((f) => ({
      ...f,
      _doh: dohEventTime(f),
    }))

    const q = search.trim().toUpperCase()

    const filtered = withMeta.filter((f) => {
      if (directionFilter !== 'all' && f._doh.kind !== directionFilter) return false
      if (statusFilter !== 'all' && f.status !== statusFilter) return false
      if (q) {
        const haystack = `${f.flight_numbers} ${f.origin} ${f.destination} ${f.airline_primary}`.toUpperCase()
        if (!haystack.includes(q)) return false
      }
      return true
    })

    return filtered.sort((a, b) => {
      if (!a._doh.time) return 1
      if (!b._doh.time) return -1
      return a._doh.time.localeCompare(b._doh.time)
    })
  }, [flights, search, directionFilter, statusFilter])

  if (error) {
    return (
      <div>
        <h2>Live Flights</h2>
        <p className="flights-error">
          Couldn't reach the API — is the backend running on localhost:8000?
        </p>
      </div>
    )
  }

  if (!flights) {
    return (
      <div>
        <h2>Live Flights</h2>
        <p className="page-placeholder">Loading flight data…</p>
      </div>
    )
  }

  return (
    <div>
      <h2>Live Flights</h2>
      <p className="flights-count">
        {processed.length} of {flights.length} physical flights shown
      </p>

      <div className="flights-toolbar">
        <div className="flights-search-wrap">
          <input
            className="flights-search"
            type="text"
            placeholder="Search flight, route, or airline"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {searching ? (
            <span className="flights-search-spinner" />
          ) : (
            <span className="flights-search-icon">⌕</span>
          )}
        </div>

        <div className="flights-direction-toggle">
          <button
            className={directionFilter === 'all' ? 'toggle-btn toggle-btn-active' : 'toggle-btn'}
            onClick={() => setDirectionFilter('all')}
          >
            All
          </button>
          <button
            className={directionFilter === 'DEP' ? 'toggle-btn toggle-btn-active' : 'toggle-btn'}
            onClick={() => setDirectionFilter('DEP')}
          >
            Departures
          </button>
          <button
            className={directionFilter === 'ARR' ? 'toggle-btn toggle-btn-active' : 'toggle-btn'}
            onClick={() => setDirectionFilter('ARR')}
          >
            Arrivals
          </button>
        </div>

        <StatusDropdown
          value={statusFilter}
          options={statusOptions}
          onChange={setStatusFilter}
        />
      </div>

      {processed.length === 0 ? (
        <p className="page-placeholder">No flights match your filters.</p>
      ) : (
        <div className="flights-table-wrap">
          <table className="flights-table">
            <thead>
              <tr>
                <th>DOH Time</th>
                <th>Route</th>
                <th>Flight</th>
                <th>Airline</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {processed.map((f, i) => (
                <tr key={i}>
                  <td>
                    <span className="doh-time-cell">
                      {formatTime(f._doh.time)}
                      <span className={`doh-time-kind doh-time-kind-${f._doh.kind.toLowerCase()}`}>
                        {f._doh.kind}
                      </span>
                    </span>
                  </td>
                  <td className="route-cell">
                    <span className="route-code">{f.origin}</span>
                    <span className="route-arrow">→</span>
                    <span className="route-code">{f.destination}</span>
                  </td>
                  <td>
                    <FlightNumbers raw={f.flight_numbers} count={f.num_codeshares} />
                  </td>
                  <td className="airline-cell">{f.airline_primary}</td>
                  <td>
                    <DelayBadge delayMinutes={f.delay_minutes} status={f.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Flights