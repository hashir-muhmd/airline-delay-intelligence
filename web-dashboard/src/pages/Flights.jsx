import { useState, useEffect } from 'react'
import { fetchJSON } from '../api'
import './Flights.css'

function formatTime(iso) {
  if (!iso) return '—'
  // NOTE: AviationStack/ingestion appears to label Doha local time (AST) with
  // a "Z" (UTC) suffix — confirmed by cross-checking QR87 against HIA's own
  // site (raw "02:20:00Z" matches HIA's displayed "02:20" local departure).
  // Displaying the raw UTC-suffixed components directly, without conversion,
  // since converting them (as if they were true UTC) produces the wrong time.
  // Root cause belongs in ingestion/ — see project log open items.
  const match = iso.match(/T(\d{2}):(\d{2})/)
  if (!match) return iso
  const [, hour, minute] = match
  const datePart = iso.slice(5, 10).replace('-', ' ') // "MM-DD" → "MM DD"
  return `${datePart} ${hour}:${minute} AST`
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

function Flights() {
  const [flights, setFlights] = useState(null)
  const [error, setError] = useState(null)

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

  if (flights.length === 0) {
    return (
      <div>
        <h2>Live Flights</h2>
        <p className="page-placeholder">No flight data available yet.</p>
      </div>
    )
  }

  return (
    <div>
      <h2>Live Flights</h2>
      <p className="flights-count">{flights.length} physical flights tracked</p>
      <div className="flights-table-wrap">
        <table className="flights-table">
          <thead>
            <tr>
              <th>Departs</th>
              <th>Route</th>
              <th>Flight</th>
              <th>Airline</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {flights.map((f, i) => (
              <tr key={i}>
                <td>{formatTime(f.scheduled_departure)}</td>
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
    </div>
  )
}

export default Flights