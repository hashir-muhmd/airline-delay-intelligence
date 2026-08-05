# ML

Training scripts and saved model artifacts.

## Contents

- `train_classifier.py` — delay classifier (delayed vs on-time). **Built and
  running.** See status below.
- `cascade_link_diagnostic.py` — diagnostic script checking whether any
  real cascade-link candidates (same-aircraft arrival→departure pairs)
  currently exist in the data. **Built and running.** See status below.
- `train_regressor.py` — predicted delay duration in minutes. Not yet
  started — no point building this until the classifier's data ceiling
  (below) is resolved, since the same volume constraint applies.
- `cascade_model.py` — downstream disruption propagation via aircraft
  rotation. Not yet started — blocked on cascade-link data volume (see
  `cascade_link_diagnostic.py` status below), not on a missing field
  anymore (that part was resolved — see `ingestion/README.md`).
- `forecasting.py` — Prophet-based seasonal delay trends. Not yet started —
  needs much more historical volume than currently exists.
- `artifacts/` — saved model files (gitignored, not committed).

## `train_classifier.py` — status

**Pipeline built, tested, and validated end-to-end.** Given a live
`DATABASE_URL`, it will:

1. Pull `flights` and `weather_snapshots` from the database
2. De-duplicate codeshares into physical flights (same logic as
   `notebooks/01_eda.ipynb`)
3. Attach the nearest weather snapshot at the origin airport (within a
   3-hour window) to each flight
4. Engineer features using only information known **before** departure
   (scheduled hour, day of week, weekend flag, origin, destination, airline,
   weather) — deliberately excludes `actual_departure`/`actual_arrival`,
   since using those would leak the answer
5. Filters to flights with a known `delay_minutes` value (the labeled subset)
6. Scales numeric features (`StandardScaler`) and one-hot encodes
   categoricals, inside a `scikit-learn` `Pipeline`
7. Trains a `LogisticRegression` (with `class_weight="balanced"` to avoid
   trivially predicting the majority class)
8. Evaluates against a naive "always predict the majority class" baseline,
   printed side-by-side with the model's own accuracy, so the result is
   never read in isolation
9. Saves the fitted pipeline to `artifacts/delay_classifier_v1.joblib`

**Convergence fix (2026-08-05)**: once weather features (which span wide,
uneven ranges — e.g. `visibility_m` in the thousands vs. `scheduled_hour`
0–23) started being included, `LogisticRegression`'s solver began hitting
its iteration cap without converging (`ConvergenceWarning`). Fixed by adding
`StandardScaler` to the numeric feature branch of the pipeline — addresses
the root cause (badly-scaled features), not just the symptom (raising
`max_iter` and hoping it converges anyway). Re-running after this fix
produced identical metrics to before, confirming the fix only improved
numerical stability, not the model's actual behavior.

### Current real numbers (informational, not a performance claim)

As of the most recent run: **90 labeled flights** (78 delayed, 12 on-time —
an ~87% delayed base rate, essentially unchanged from earlier runs at lower
volume). Naive baseline accuracy: 0.85. Model accuracy: 0.74 — lower than
the baseline, which is expected and intentional given the class-balancing
tradeoff (the model favors correctly catching on-time flights over
maximizing raw accuracy on this heavily imbalanced, still-small sample).

**This is a pipeline-validation checkpoint, not a production model.** Below
~200 labeled rows (see `MIN_ROWS_FOR_REASONABLE_METRICS` in the script), any
metric produced is a sanity check that the code works, not a trustworthy
estimate of real-world performance. Retrain once delay-labeled data volume
grows meaningfully — either through continued daily accumulation or an
AviationStack Historical Flights backfill (currently locked on the free
tier).

## `cascade_link_diagnostic.py` — status

**Built and running, currently returns zero cascade-link candidates.**
Checks whether any two flights share the same `aircraft_icao24` with a
plausible turnaround pattern: flight A arrives somewhere, flight B departs
from that same airport, with a 30-minute-to-6-hour gap between them
(physically plausible turnaround window).

As of the most recent run (2026-08-05): **97 flights have a non-null
`aircraft_icao24`**, across **29 distinct aircraft** — but **0 valid
arrival→departure pairs** were found.

This is a genuine, informative result, not a broken script. The most
likely explanation is structural: since only DOH is tracked, an aircraft's
full rotation is only visible to us if **both** its inbound leg to DOH and
its outbound leg from DOH happen to be captured in the same data pull —
if either leg is a flight to/from an airport we don't track, that half of
the chain is invisible, and no link can be formed even if `icao24` matches
correctly on both sides. This is expected to improve as data volume grows,
but is a real, structural ceiling worth being aware of (adding more tracked
airports would help, at the cost of AviationStack quota — see
`ingestion/README.md`).

`cascade_model.py` remains un-started and correctly blocked on this —
there's no point building a model with zero training pairs. Re-run this
diagnostic periodically; the moment it finds even a handful of candidate
pairs with delay data on both sides, that's the signal to revisit
`cascade_model.py`.

## Running

```bash
cd ml
pip install -r requirements.txt
python train_classifier.py
python cascade_link_diagnostic.py
```

Requires the same `DATABASE_URL` used by `backend/` and `ingestion/` (loaded
from `../ingestion/.env` by default — see each script's `load_dotenv` call
if your `.env` lives elsewhere).