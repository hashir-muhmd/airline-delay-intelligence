function CascadeRisk() {
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
        currently 0 such pairs exist in the data, since only DOH is tracked
        and an aircraft's full rotation is only visible when both its
        inbound and outbound legs touch DOH. This page will populate once
        enough matched pairs accumulate.
      </p>
    </div>
  )
}

export default CascadeRisk