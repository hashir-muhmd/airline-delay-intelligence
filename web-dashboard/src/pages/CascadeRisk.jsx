import { useState, useEffect } from 'react'
import { fetchJSON } from '../api'

function CascadeRisk() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchJSON('/cascade/stats')
      .then((data) => {
        if (!cancelled) setStats(data)
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
        <h2>Cascade Risk</h2>
        <p className="stats-error">
          Couldn't reach the API — is the backend running on localhost:8000?
        </p>
      </div>
    )
  }

  if (!stats) {
    return (
      <div>
        <h2>Cascade Risk</h2>
        <p className="page-placeholder">Loading cascade candidate data…</p>
      </div>
    )
  }

  return (
    <div>
      <h2>Cascade Risk</h2>
      <p className="page-placeholder">
        Coming soon — downstream disruption analysis.
      </p>
      <p className="page-placeholder-detail">
        Cascade modeling links flights by aircraft: if an inbound flight is
        delayed, its next scheduled leg risks a knock-on delay too. Building
        this requires matched arrival→departure pairs on the same aircraft —
        currently <strong>{stats.candidate_count} such pair{stats.candidate_count === 1 ? '' : 's'}</strong>{' '}
        exist in the data ({stats.flights_with_icao24} flights with a known
        aircraft, {stats.distinct_aircraft} distinct aircraft tracked), since
        only DOH is tracked and an aircraft's full rotation is only visible
        when both its inbound and outbound legs touch DOH.
        {stats.candidate_count > 0 && (
          <>
            {' '}Of those, {stats.candidates_with_both_delays} pair
            {stats.candidates_with_both_delays === 1 ? '' : 's'} have delay
            data on both flights — the only ones usable for validating a
            cascade effect.
          </>
        )}{' '}
        This page will populate once enough matched pairs accumulate.
      </p>
    </div>
  )
}

export default CascadeRisk