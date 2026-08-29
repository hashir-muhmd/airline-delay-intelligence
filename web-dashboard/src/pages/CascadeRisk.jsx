import { useEffect, useState } from 'react'
import { fetchJSON } from '../api'

function CascadeRisk() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchJSON('/cascade/stats')
      .then(setStats)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div>
      <h2>Cascade Risk</h2>
      <p className="page-placeholder">
        Coming soon — downstream disruption analysis.
      </p>

      {error && (
        <p className="page-placeholder-detail">
          Couldn't load live cascade stats — is the backend running? ({error})
        </p>
      )}

      {stats && (
        <p className="page-placeholder-detail">
          Cascade modeling links flights by aircraft: if an inbound flight is
          delayed, its next scheduled leg risks a knock-on delay too. Building
          this requires matched arrival→departure pairs on the same aircraft
          — currently{' '}
          <strong>
            {stats.candidate_count} such pair{stats.candidate_count === 1 ? '' : 's'}
          </strong>{' '}
          exist in the data ({stats.flights_with_icao24} flights with a known
          aircraft, {stats.distinct_aircraft} distinct aircraft tracked), since
          only DOH is tracked and an aircraft's full rotation is only visible
          when both its inbound and outbound legs touch DOH.
          {stats.candidate_count > 0 && (
            <>
              {' '}
              Of those, {stats.candidates_with_both_delays} pair
              {stats.candidates_with_both_delays === 1 ? '' : 's'} have delay
              data on both flights — the only ones usable for validating a
              cascade effect.
            </>
          )}{' '}
          This page will populate once enough matched pairs accumulate.
        </p>
      )}
    </div>
  )
}

export default CascadeRisk