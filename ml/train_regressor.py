# ml/train_regressor.py
"""
Baseline delay-DURATION regressor for SkyPulse.

Where train_classifier.py predicts a binary delayed/not-delayed outcome,
this predicts the actual delay_minutes value -- how many minutes late (or
early, if negative) a flight is expected to be. Same feature set, same
pre-departure-only constraint (no actual_departure/actual_arrival used as
features, since that would leak the answer), same small-sample honesty
approach as the classifier.

Deliberately reuses load_data / deduplicate_to_physical_flights /
attach_nearest_weather / engineer_features / NUMERIC_FEATURES /
CATEGORICAL_FEATURES directly from train_classifier.py, rather than
duplicating that logic here -- keeps both scripts using the exact same
pipeline, so a future fix to one (e.g. the weather-matching window) doesn't
silently drift out of sync with the other.

IMPORTANT: as of this writing, only ~90 physical flights have delay data.
This script's purpose right now is to validate the regression pipeline
end-to-end, not to produce a trustworthy prediction. See the same
MIN_ROWS_FOR_REASONABLE_METRICS caveat used in train_classifier.py.

Run with:
    cd ml
    python train_regressor.py
"""

import logging
import os
import sys
from pathlib import Path

import joblib
import numpy as np
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy import create_engine

from train_classifier import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    attach_nearest_weather,
    deduplicate_to_physical_flights,
    engineer_features,
    load_data,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MIN_ROWS_FOR_REASONABLE_METRICS = 200

# Same plausibility bounds used in backend/routers/flights.py's /stats/delays
# endpoint -- excludes the kind of bad-data anomaly documented there (e.g.
# the -847 minute case traced to a mismatched actual_departure). Applying
# the same bounds here keeps the regressor's training data consistent with
# what the rest of the project already treats as "plausible."
MIN_PLAUSIBLE_DELAY_MINUTES = -60
MAX_PLAUSIBLE_DELAY_MINUTES = 720

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def build_labeled_dataset_for_regression(physical):
    """
    Unlike train_classifier.py's build_labeled_dataset (which adds a binary
    is_delayed label), this keeps delay_minutes itself as the continuous
    target, and additionally excludes anomalous values outside plausible
    bounds -- since a regressor trained on a -847 minute outlier would be
    badly distorted by a single bad data point in a sample this small.
    """
    labeled = physical.dropna(subset=["delay_minutes"]).copy()
    before = len(labeled)
    labeled = labeled[
        labeled["delay_minutes"].between(
            MIN_PLAUSIBLE_DELAY_MINUTES, MAX_PLAUSIBLE_DELAY_MINUTES
        )
    ]
    excluded = before - len(labeled)
    if excluded > 0:
        logger.info(
            f"Excluded {excluded} row(s) with implausible delay_minutes "
            f"(outside {MIN_PLAUSIBLE_DELAY_MINUTES} to {MAX_PLAUSIBLE_DELAY_MINUTES})"
        )
    return labeled


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ],
    )
    # Ridge rather than plain LinearRegression: with this few rows and
    # one-hot-encoded categoricals (many origin/destination/airline
    # columns relative to ~90 rows), a small L2 penalty helps avoid
    # wildly unstable coefficients on a dataset this small.
    model = Ridge(alpha=1.0)
    return Pipeline(steps=[("preprocess", preprocessor), ("model", model)])


def main():
    load_dotenv(dotenv_path=Path(__file__).parent.parent / "ingestion" / ".env")
    db_url = os.getenv("DATABASE_URL")
    if db_url is None:
        logger.error("DATABASE_URL not found -- check the .env path above matches")
        sys.exit(1)

    engine = create_engine(db_url)
    flights, weather = load_data(engine)
    logger.info(f"Loaded {len(flights)} raw flight records, {len(weather)} weather snapshots")

    physical = deduplicate_to_physical_flights(flights)
    physical = attach_nearest_weather(physical, weather)
    physical = engineer_features(physical)

    labeled = build_labeled_dataset_for_regression(physical)
    n = len(labeled)
    logger.info(f"Physical flights with plausible delay data (labeled rows): {n}")

    if n < 10:
        logger.error(
            f"Only {n} labeled rows -- not enough to fit or evaluate a "
            f"regressor at all. Exiting without training."
        )
        sys.exit(1)

    if n < MIN_ROWS_FOR_REASONABLE_METRICS:
        logger.warning(
            f"Only {n} labeled rows (below the {MIN_ROWS_FOR_REASONABLE_METRICS} "
            f"considered reasonable for stable metrics). Treat every metric below "
            f"as a SANITY CHECK on the pipeline, not a trustworthy estimate of "
            f"real-world prediction error."
        )

    for col in NUMERIC_FEATURES:
        if labeled[col].isna().any():
            labeled[col] = labeled[col].fillna(labeled[col].median())

    X = labeled[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = labeled["delay_minutes"]

    logger.info(
        f"delay_minutes -- mean: {y.mean():.1f}, median: {y.median():.1f}, "
        f"min: {y.min()}, max: {y.max()}"
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Naive baseline: always predict the training set's mean delay. On a
    # skewed target like delay_minutes (mostly small positive delays, a
    # few large ones), this is a meaningfully hard baseline to beat with
    # so little data -- printed alongside the model's error rather than
    # left implicit, same honesty pattern as train_classifier.py.
    baseline_pred = np.full(len(y_test), y_train.mean())
    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    model_mae = mean_absolute_error(y_test, y_pred)
    model_rmse = root_mean_squared_error(y_test, y_pred)
    model_r2 = r2_score(y_test, y_pred)

    print("\n--- Evaluation (see warnings above about sample size) ---")
    print(f"Test set size: {len(y_test)}")
    print(f"Naive baseline MAE (always predict training mean, {y_train.mean():.1f} min): {baseline_mae:.1f} min")
    print(f"Model MAE: {model_mae:.1f} min")
    print(f"Model RMSE: {model_rmse:.1f} min")
    print(f"Model R^2: {model_r2:.3f}")
    if model_mae >= baseline_mae:
        print(
            f"NOTE: model MAE is NOT better than the naive baseline. With only "
            f"{n} rows, this is a realistic and honest outcome, not necessarily a "
            f"broken model -- there may simply not be enough data yet for the "
            f"model to find a real pattern beyond 'predict the average'. Revisit "
            f"once more labeled data accumulates rather than tuning further now."
        )
    else:
        print(
            f"Model beats the naive baseline by {baseline_mae - model_mae:.1f} min MAE. "
            f"Still treat this as a pipeline-validation result given the small sample, "
            f"not a production-grade error estimate."
        )

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    artifact_path = ARTIFACTS_DIR / "delay_regressor_v1.joblib"
    joblib.dump(pipeline, artifact_path)
    logger.info(f"Saved model artifact to {artifact_path}")
    logger.info(
        "Reminder: this artifact is a pipeline-validation checkpoint, not a "
        "production model. Retrain once delay-labeled data volume grows "
        "meaningfully past a few hundred rows."
    )


if __name__ == "__main__":
    main()