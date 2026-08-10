# ML

Training scripts and saved model artifacts.

## Contents

- `train_classifier.py` — delay classifier (delayed vs on-time). **Built and
  running.** See status below.
- `train_regressor.py` — delay-duration regressor (predicts delay_minutes
  as a continuous value). **Built and running.** See status below.
- `cascade_link_diagnostic.py` — diagnostic script checking whether any
  real cascade-link candidates (same-aircraft arrival→departure pairs)
  currently exist in the data. **Built and running.** See status below.
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
volume, and unchanged even as raw flight volume grew to 6,826 — recent
ingestion has mostly added still-`scheduled` flights without delay data
yet, not completed ones). Naive baseline accuracy: 0.85. Model accuracy:
0.74 — lower than the baseline, which is expected and intentional given the
class-balancing tradeoff (the model favors correctly catching on-time
flights over maximizing raw accuracy on this heavily imbalanced, still-small
sample).

**This is a pipeline-validation checkpoint, not a production model.** Below
~200 labeled rows (see `MIN_ROWS_FOR_REASONABLE_METRICS` in the script), any
metric produced is a sanity check that the code works, not a trustworthy
estimate of real-world performance. Retrain once delay-labeled data volume
grows meaningfully — either through continued daily accumulation or an
AviationStack Historical Flights backfill (currently locked on the free
tier).

## `train_regressor.py` — status

**Pipeline built, tested, and validated end-to-end.** Deliberately reuses
`train_classifier.py`'s data loading, de-duplication, weather-joining, and
feature-engineering functions directly (via import) rather than duplicating
that logic, so both scripts stay in sync with any future fix to the shared
pipeline. Where the classifier predicts delayed/not-delayed, this predicts
`delay_minutes` itself as a continuous value — same pre-departure-only
feature constraint applies (no `actual_departure`/`actual_arrival` used).

Uses `Ridge` regression rather than plain linear regression — a small L2
penalty helps stability given the sample is small relative to the number of
one-hot-encoded categorical columns (many distinct origins, destinations,
and airlines). Also applies the same plausible-delay bounds
(`-60` to `720` minutes) used in `backend/routers/flights.py`'s
`/stats/delays` endpoint, excluding anomalous rows before training rather
than letting a single bad data point distort a small sample.

### Current real numbers (informational, not a performance claim)

As of the most recent run: **89 labeled flights** (1 excluded as
implausible), delay range **-35 to +60 minutes**, mean **28.6**, median
**28.0**. Naive baseline (always predict the training mean): **10.0 min
MAE**. Model: **12.2 min MAE, RMSE 14.2 min, R² = -0.337**.

**Honest read of this result**: the model currently performs *worse* than
simply guessing the average delay every time — the negative R² confirms it
isn't finding usable signal in the available features yet. This is a
genuine, informative negative result, not a broken pipeline. With delays
clustered fairly tightly (mostly 0–60 minutes) and only 89 rows, there
isn't much variance left for scheduled-hour/weather/route features to
meaningfully explain. Ridge regression correctly shrinks toward the mean
under weak signal rather than overfitting noise, which is exactly what this
result reflects.

**This is a pipeline-validation checkpoint, not a production model** — more
so than the classifier, given it currently underperforms the simplest
possible baseline. Do not present these specific numbers as a working
prediction system. Retrain once delay-labeled data volume grows
meaningfully; a negative R² at 89 rows says nothing definitive about
whether the underlying relationship is learnable with more data — most
likely it is, this sample just isn't large enough yet to show it.

## `cascade_link_diagnostic.py` — status

**Built and running, currently returns zero cascade-link candidates.**
Checks whether any two flights share the same `aircraft_icao24` with a
plausible turnaround pattern: flight A arrives somewhere, flight B departs
from that same airport, with a 30-minute-to-6-hour gap between them
(physically plausible turnaround window).

As of the most recent run (2026-08-06): **219 flights have a non-null
`aircraft_icao24`**, across **84 distinct aircraft** — up substantially
from the previous check (97 flights / 29 aircraft on 2026-08-05) — but
still **0 valid arrival→departure pairs** were found.

This more-than-doubling of aircraft coverage with the result staying at
zero strengthens the structural explanation over a "just needs more time"
explanation: if this were purely a volume problem, some candidates would be
expected to start appearing by now. The most likely explanation remains
structural: since only DOH is tracked, an aircraft's full rotation is only
visible to us if **both** its inbound leg to DOH and its outbound leg from
DOH happen to be captured in the same data pull — if either leg is a
flight to/from an airport we don't track, that half of the chain is
invisible, and no link can be formed even if `icao24` matches correctly on
both sides. Adding more tracked airports would directly address this (at
the cost of AviationStack quota — see `ingestion/README.md`), and is now
the more clearly indicated next step if cascade modeling is to become
viable, rather than simply waiting longer on the current DOH-only setup.

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
python train_regressor.py
python cascade_link_diagnostic.py
```

Requires the same `DATABASE_URL` used by `backend/` and `ingestion/` (loaded
from `../ingestion/.env` by default — see each script's `load_dotenv` call
if your `.env` lives elsewhere).