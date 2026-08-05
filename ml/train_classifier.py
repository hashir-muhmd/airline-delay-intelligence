# ml/train_classifier.py
"""
Baseline delay classifier for SkyPulse.

Predicts whether a flight will be delayed (> 15 minutes, the standard US DOT
threshold) using only information available BEFORE departure: scheduled
time features, route, airline, and nearest weather snapshot at the origin
airport. Does NOT use actual_departure/actual_arrival as features, since
those are only known after the fact and would leak the answer.

IMPORTANT: as of this writing, only ~90 physical flights have delay data.
This script is intentionally simple (LogisticRegression, not a heavier
model) because a complex model on this little data would just overfit and
produce misleadingly confident-looking metrics. Its purpose right now is to
validate the pipeline end-to-end -- feature engineering, train/test split,
evaluation, artifact saving -- so that re-running it later as data volume
grows is a one-command retrain, not a rebuild.

Run with:
    cd ml
    python train_classifier.py
"""

import logging
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Below this many labeled rows, a train/test split is close to meaningless --
# we still run one so the pipeline is exercised end-to-end, but every metric
# printed gets a loud caveat rather than being presented as reliable.
MIN_ROWS_FOR_REASONABLE_METRICS = 200

DELAY_THRESHOLD_MINUTES = 15  # US DOT standard definition of "delayed"

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def load_data(engine) -> tuple[pd.DataFrame, pd.DataFrame]:
    flights = pd.read_sql("SELECT * FROM flights", engine)
    weather = pd.read_sql("SELECT * FROM weather_snapshots", engine)
    return flights, weather


def deduplicate_to_physical_flights(flights: pd.DataFrame) -> pd.DataFrame:
    """
    Same grouping logic as notebooks/01_eda.ipynb: collapse codeshare
    records (same aircraft, same scheduled/actual times) into one row per
    physical flight.
    """
    physical = (
        flights.sort_values("flight_number")
        .groupby(
            ["scheduled_departure", "actual_departure", "origin", "destination"],
            dropna=False,
        )
        .agg(
            airline_primary=("airline", "first"),
            scheduled_arrival=("scheduled_arrival", "first"),
            status=("status", "first"),
            delay_minutes=("delay_minutes", "first"),
        )
        .reset_index()
    )
    return physical


def attach_nearest_weather(
    physical: pd.DataFrame, weather: pd.DataFrame
) -> pd.DataFrame:
    """
    For each flight, find the weather snapshot at the origin airport closest
    in time to the scheduled departure (within a 3-hour window). Flights
    with no matching snapshot get NaN weather features, handled downstream
    by the imputer implicit in how we build the feature matrix.
    """
    if weather.empty:
        for col in ["temperature_c", "wind_speed_ms", "visibility_m", "precipitation_mm"]:
            physical[col] = np.nan
        return physical

    weather = weather.copy()
    weather["recorded_at"] = pd.to_datetime(weather["recorded_at"], utc=True)
    physical = physical.copy()
    physical["scheduled_departure"] = pd.to_datetime(
        physical["scheduled_departure"], utc=True
    )

    matched_rows = []
    max_gap = pd.Timedelta(hours=3)

    for _, row in physical.iterrows():
        candidates = weather[weather["airport_code"] == row["origin"]]
        if candidates.empty:
            matched_rows.append(
                {"temperature_c": np.nan, "wind_speed_ms": np.nan,
                 "visibility_m": np.nan, "precipitation_mm": np.nan}
            )
            continue
        time_diff = (candidates["recorded_at"] - row["scheduled_departure"]).abs()
        nearest_idx = time_diff.idxmin()
        if time_diff.loc[nearest_idx] > max_gap:
            matched_rows.append(
                {"temperature_c": np.nan, "wind_speed_ms": np.nan,
                 "visibility_m": np.nan, "precipitation_mm": np.nan}
            )
            continue
        nearest = candidates.loc[nearest_idx]
        matched_rows.append(
            {
                "temperature_c": nearest["temperature_c"],
                "wind_speed_ms": nearest["wind_speed_ms"],
                "visibility_m": nearest["visibility_m"],
                "precipitation_mm": nearest["precipitation_mm"],
            }
        )

    weather_features = pd.DataFrame(matched_rows, index=physical.index)
    return pd.concat([physical, weather_features], axis=1)


def engineer_features(physical: pd.DataFrame) -> pd.DataFrame:
    df = physical.copy()
    df["scheduled_departure"] = pd.to_datetime(df["scheduled_departure"], utc=True)
    df["scheduled_hour"] = df["scheduled_departure"].dt.hour
    df["day_of_week"] = df["scheduled_departure"].dt.dayofweek  # 0=Mon
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    return df


def build_labeled_dataset(physical: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only flights that actually have a delay_minutes value (i.e. have
    completed departure) -- this is the ~90-row subset as of this writing.
    """
    labeled = physical.dropna(subset=["delay_minutes"]).copy()
    labeled["is_delayed"] = (labeled["delay_minutes"] > DELAY_THRESHOLD_MINUTES).astype(int)
    return labeled


NUMERIC_FEATURES = [
    "scheduled_hour",
    "day_of_week",
    "is_weekend",
    "temperature_c",
    "wind_speed_ms",
    "visibility_m",
    "precipitation_mm",
]
CATEGORICAL_FEATURES = ["origin", "destination", "airline_primary"]


def build_pipeline() -> Pipeline:
    # NOTE: numeric features span very different scales (e.g. scheduled_hour
    # 0-23 vs. visibility_m potentially in the thousands), which was causing
    # LogisticRegression's solver to hit its iteration cap without properly
    # converging (a ConvergenceWarning, first seen once weather features
    # with wide ranges started being included). StandardScaler fixes this
    # at the root cause -- rescaling features so no single one dominates
    # the optimization -- rather than just raising max_iter and hoping it
    # converges anyway on a badly-scaled problem.
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                StandardScaler(),
                NUMERIC_FEATURES,
            ),
        ],
    )
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
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

    labeled = build_labeled_dataset(physical)
    n = len(labeled)
    logger.info(f"Physical flights with delay data (labeled rows): {n}")

    if n < 10:
        logger.error(
            f"Only {n} labeled rows -- not enough to fit or evaluate a model "
            f"at all. Exiting without training. Re-run once more delay data "
            f"has accumulated."
        )
        sys.exit(1)

    if n < MIN_ROWS_FOR_REASONABLE_METRICS:
        logger.warning(
            f"Only {n} labeled rows (below the {MIN_ROWS_FOR_REASONABLE_METRICS} "
            f"considered reasonable for stable metrics). The pipeline below runs "
            f"end-to-end and produces real numbers, but treat every metric as a "
            f"SANITY CHECK on the pipeline, not a trustworthy estimate of real-world "
            f"performance. Do not report these numbers as production accuracy."
        )

    # Fill missing numeric values with column median (simple, transparent;
    # revisit with a proper imputer once volume/weather coverage improves)
    for col in NUMERIC_FEATURES:
        if labeled[col].isna().any():
            median_val = labeled[col].median()
            labeled[col] = labeled[col].fillna(median_val)

    X = labeled[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = labeled["is_delayed"]

    logger.info(f"Class balance -- delayed: {y.sum()}, on-time: {(1 - y).sum()}")

    # With very few positive/negative examples, stratified splitting can
    # fail outright (e.g. only 1 delayed flight). Fall back to a plain
    # random split if stratification isn't possible.
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
    except ValueError as e:
        logger.warning(f"Stratified split failed ({e}); falling back to plain random split")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    # Naive baseline: always predict the majority class. On imbalanced data
    # (which this is -- see class balance above), this baseline can look
    # deceptively strong, so we print it right next to the model's accuracy
    # rather than leaving it as something the reader has to compute by hand.
    majority_class = y_train.mode()[0]
    baseline_pred = np.full(len(y_test), majority_class)
    baseline_accuracy = accuracy_score(y_test, baseline_pred)
    model_accuracy = accuracy_score(y_test, y_pred)

    print("\n--- Evaluation (see warnings above about sample size) ---")
    print(f"Test set size: {len(y_test)}")
    print(f"Naive baseline accuracy (always predict '{majority_class}'): {baseline_accuracy:.3f}")
    print(f"Model accuracy: {model_accuracy:.3f}")
    if model_accuracy < baseline_accuracy:
        print(
            f"NOTE: model accuracy is LOWER than the naive baseline. This is "
            f"expected here -- class_weight='balanced' deliberately trades "
            f"raw accuracy for better recall on the minority class, rather "
            f"than trivially predicting the majority class every time. Read "
            f"the classification report below (especially per-class recall) "
            f"before judging this model, not the accuracy number alone."
        )
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    artifact_path = ARTIFACTS_DIR / "delay_classifier_v1.joblib"
    joblib.dump(pipeline, artifact_path)
    logger.info(f"Saved model artifact to {artifact_path}")
    logger.info(
        "Reminder: this artifact is a pipeline-validation checkpoint, not a "
        "production model. Retrain once delay-labeled data volume grows "
        "meaningfully past a few hundred rows."
    )


if __name__ == "__main__":
    main()