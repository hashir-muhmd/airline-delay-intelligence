# ML

Training scripts and saved model artifacts.

## ⚠️ Dataset reset note (2026-08-23)

Railway's trial credit ran out while the project was on a break, taking the
live backend, ingestion, and Postgres instance offline. Rather than pay for
a new billing cycle, development moved to a **local Postgres instance**
restored from an earlier local snapshot (schema + migrations re-applied,
but only ~400 old flight rows, not the ~6,800+ that had accumulated on
Railway). Ingestion is now running locally via `scheduler.py` and
accumulating fresh data again.

**Practical effect**: the numbers below are smaller and less stable than
the pre-reset numbers documented earlier in this project's history — not
because anything broke, but because the labeled-row count restarted from a
lower base. Treat every metric below as even more of a pipeline-sanity-check
than usual, and expect these to improve as local ingestion continues to run.

## Contents

- `train_classifier.py` — delay classifier (delayed vs on-time). **Built and
  running.** See status below.
- `train_regressor.py` — delay-duration regressor (predicts delay_minutes
  as a continuous value). **Built and running.** See status below.
- `cascade_link_diagnostic.py` — diagnostic script checking whether any
  real cascade-link candidates (same-aircraft arrival→departure pairs)
  currently exist in the data. **Built and running.** See status below.
  As of this session, the same matching logic is also exposed live via
  `GET /cascade/stats` on the backend, so the dashboard's Cascade Risk page
  shows a real-time version of this same check instead of a static snapshot
  from the last manual script run.
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
`max_iter` and hoping it converges anyway).

### Current real numbers (informational, not a performance claim)

**Post-reset run (2026-08-23), on the local rebuilt dataset**: only **10
labeled flights** (9 delayed, 1 on-time — severely imbalanced, and small
enough that the stratified train/test split failed outright and the script
fell back to a plain random split). Naive baseline accuracy: 1.00 (trivial,
given the 1-row minority class landed entirely in training). Model
accuracy: 0.667 on a 3-row test set. **These numbers are not meaningful on
their own** — they confirm the pipeline still runs correctly end-to-end
after the dataset reset, nothing more. Re-run every few days as local
ingestion accumulates more labeled rows; the pre-reset run (90 labeled
rows, 0.74 model vs 0.85 baseline accuracy) is a better reference point for
what this pipeline looks like at a slightly more reasonable sample size,
though even that was still below the ~200-row bar for trustworthy metrics.

**This is a pipeline-validation checkpoint, not a production model.** Below
~200 labeled rows (see `MIN_ROWS_FOR_REASONABLE_METRICS` in the script), any
metric produced is a sanity check that the code works, not a trustworthy
estimate of real-world performance.

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

**Post-reset run (2026-08-23), on the local rebuilt dataset**: **10 labeled
flights**, delay range **13–61 minutes**, mean **34.8**, median **33.0**.
Naive baseline (always predict the training mean, 33.7 min): **15.4 min
MAE**. Model: **18.5 min MAE, RMSE 19.4 min, R² = -0.103**.

Same honest read as the pre-reset finding: the model still doesn't beat
guessing the mean, which is expected and unremarkable at 10 rows. The
pre-reset run (89 labeled rows, R² = -0.337) remains the more informative
reference point — this result mainly confirms the pipeline still functions
correctly post-reset, not that anything has changed about the underlying
signal-to-noise question.

**This is a pipeline-validation checkpoint, not a production model** — more
so than the classifier, given it currently underperforms the simplest
possible baseline. Retrain periodically as local ingestion accumulates
more labeled data; a negative R² at this sample size says nothing
definitive about whether the underlying relationship is learnable with
more data — most likely it is, this sample just isn't large enough yet to
show it.

## `cascade_link_diagnostic.py` — status

**Built and running, currently returns zero cascade-link candidates** —
consistent with every prior run, both before and after the local dataset
reset.

Checks whether any two flights share the same `aircraft_icao24` with a
plausible turnaround pattern: flight A arrives somewhere, flight B departs
from that same airport, with a 30-minute-to-6-hour gap between them
(physically plausible turnaround window).

**Post-reset run (2026-08-23)**: **123 flights have a non-null
`aircraft_icao24`**, across **29 distinct aircraft** — still **0 valid
arrival→departure pairs** found, matching the exact same structural
conclusion reached pre-reset (last pre-reset check: 219 flights / 84
aircraft, also 0 pairs). The result staying at zero across two independent
dataset builds (old Railway data and now this local rebuild) is further
evidence this is a structural limitation of DOH-only tracking, not a
data-volume or one-off artifact.

Since only DOH is tracked, an aircraft's full rotation is only visible to
us if **both** its inbound leg to DOH and its outbound leg from DOH happen
to be captured in the same data pull — if either leg is a flight to/from an
airport we don't track, that half of the chain is invisible, and no link
can be formed even if `icao24` matches correctly on both sides. Adding more
tracked airports would directly address this (at the cost of AviationStack
quota — see `ingestion/README.md`), and remains the clearly indicated next
step if cascade modeling is to become viable.

`cascade_model.py` remains un-started and correctly blocked on this. This
same matching logic is now also exposed live via the backend's
`GET /cascade/stats` endpoint (see `backend/routers/flights.py`), which the
dashboard's Cascade Risk page calls directly — so this diagnostic script
and the dashboard will always report the same number without needing a
manual re-run to stay in sync.

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
if your `.env` lives elsewhere). As of the local dataset reset, this points
at a local Postgres instance rather than Railway — see the note at the top
of this file.