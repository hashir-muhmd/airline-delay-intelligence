# ML

Training scripts and saved model artifacts.

## Contents

- `train_classifier.py` — delay classifier (delayed vs on-time). **Built and
  running.** See status below.
- `train_regressor.py` — predicted delay duration in minutes. Not yet
  started — no point building this until the classifier's data ceiling
  (below) is resolved, since the same volume constraint applies.
- `cascade_model.py` — downstream disruption propagation via aircraft
  rotation. Not yet started — blocked on `aircraft_registration` currently
  being 100% null in the database (under investigation, see
  `ingestion/README.md`), not just on data volume.
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
6. Trains a `LogisticRegression` (with `class_weight="balanced"` to avoid
   trivially predicting the majority class) inside a `scikit-learn`
   `Pipeline`
7. Evaluates against a naive "always predict the majority class" baseline,
   printed side-by-side with the model's own accuracy, so the result is
   never read in isolation
8. Saves the fitted pipeline to `artifacts/delay_classifier_v1.joblib`

### Current real numbers (informational, not a performance claim)

As of the most recent run: **55 labeled flights** (47 delayed, 8 on-time —
an ~85% delayed base rate). Naive baseline accuracy: 0.88. Model accuracy:
0.71 — lower than the baseline, which is expected and intentional given the
class-balancing tradeoff (the model favors correctly catching on-time
flights over maximizing raw accuracy on this heavily imbalanced, tiny
sample).

**This is a pipeline-validation checkpoint, not a production model.** Below
~200 labeled rows (see `MIN_ROWS_FOR_REASONABLE_METRICS` in the script), any
metric produced is a sanity check that the code works, not a trustworthy
estimate of real-world performance. Retrain once delay-labeled data volume
grows meaningfully — either through continued daily accumulation or an
AviationStack Historical Flights backfill (currently locked on the free
tier).

## Running

```bash
cd ml
pip install -r requirements.txt
python train_classifier.py
```

Requires the same `DATABASE_URL` used by `backend/` and `ingestion/` (loaded
from `../ingestion/.env` by default — see the script's `load_dotenv` call if
your `.env` lives elsewhere).