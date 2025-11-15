import argparse
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import mlflow
import joblib
import json

RANDOM_STATE = 42


def synthesize_data(n: int = 600, start_month: str = "2022-01-01") -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_STATE)
    months = pd.date_range(start=start_month, periods=n, freq="MS")
    total_files = rng.integers(5_000, 200_000, size=n)
    avg_file_size_mb = rng.uniform(0.2, 5.0, size=n)
    pct_pdf = rng.uniform(0.2, 0.6, size=n)
    pct_docx = rng.uniform(0.1, 0.4, size=n)
    pct_xlsx = rng.uniform(0.05, 0.3, size=n)
    archive_frequency_per_day = rng.uniform(20, 800, size=n)
    # Targets (some nonlinear relation)
    archived_gb_next_period = (
        (total_files * avg_file_size_mb) / 1024.0 * rng.uniform(0.4, 0.7, size=n)
        + 0.05 * archive_frequency_per_day
    )
    savings_gb_next_period = archived_gb_next_period * rng.uniform(0.5, 0.9, size=n)

    df = pd.DataFrame({
        "month": months.strftime("%Y-%m-%d"),
        "total_files": total_files,
        "avg_file_size_mb": avg_file_size_mb,
        "pct_pdf": pct_pdf,
        "pct_docx": pct_docx,
        "pct_xlsx": pct_xlsx,
        "archive_frequency_per_day": archive_frequency_per_day,
        "archived_gb_next_period": archived_gb_next_period,
        "savings_gb_next_period": savings_gb_next_period,
    })
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    months = pd.to_datetime(df["month"]).dt.month
    df["month_sin"] = np.sin(2 * np.pi * months / 12)
    df["month_cos"] = np.cos(2 * np.pi * months / 12)
    other_pct = 1.0 - (df["pct_pdf"] + df["pct_docx"] + df["pct_xlsx"])
    df["pct_other"] = other_pct.clip(lower=0.0)
    return df[[
        "total_files", "avg_file_size_mb", "pct_pdf", "pct_docx", "pct_xlsx", "pct_other",
        "archive_frequency_per_day", "month_sin", "month_cos"
    ]]


def train(df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    X = build_features(df)
    y = df[["archived_gb_next_period", "savings_gb_next_period"]]

    # Simple train/val split
    split = int(0.8 * len(df))
    X_train, X_val = X.iloc[:split], X.iloc[split:]
    y_train, y_val = y.iloc[:split], y.iloc[split:]

    preproc = ColumnTransformer([
        ("num", StandardScaler(), list(X.columns))
    ], remainder="drop")

    base_model = RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE)
    model = Pipeline([
        ("preproc", preproc),
        ("reg", MultiOutputRegressor(base_model))
    ])

    with mlflow.start_run(run_name="train-rf-multioutput"):
        mlflow.log_param("algorithm", "RandomForestRegressor")
        mlflow.log_param("n_estimators", 200)

        model.fit(X_train, y_train)
        preds = model.predict(X_val)

        mae = mean_absolute_error(y_val, preds, multioutput="raw_values")
        r2 = r2_score(y_val, preds, multioutput="variance_weighted")
        mlflow.log_metric("mae_archived_gb", float(mae[0]))
        mlflow.log_metric("mae_savings_gb", float(mae[1]))
        mlflow.log_metric("r2_weighted", float(r2))

        out_path = out_dir / "model.joblib"
        joblib.dump(model, out_path)
        mlflow.log_artifact(str(out_path), artifact_path="model")

        # Save a tiny model card and feature quantiles for monitoring
        card = {
            "model": "RandomForestRegressor (MultiOutput)",
            "features": list(X.columns),
            "targets": ["archived_gb_next_period", "savings_gb_next_period"],
            "metrics": {
                "mae_archived_gb": float(mae[0]),
                "mae_savings_gb": float(mae[1]),
                "r2_weighted": float(r2),
            },
        }
        with open(out_dir / "model_card.json", "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2)
        mlflow.log_artifact(str(out_dir / "model_card.json"), artifact_path="model")

        q = {
            c: {
                "p10": float(np.percentile(X[c], 10)),
                "p50": float(np.percentile(X[c], 50)),
                "p90": float(np.percentile(X[c], 90)),
            } for c in X.columns
        }
        with open(out_dir / "feature_quantiles.json", "w", encoding="utf-8") as f:
            json.dump(q, f, indent=2)
        mlflow.log_artifact(str(out_dir / "feature_quantiles.json"), artifact_path="model")

    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=None, help="Path to historical CSV data")
    parser.add_argument("--out_dir", type=str, default="ml-poc/models", help="Where to write model file")
    args = parser.parse_args()

    if args.csv and os.path.exists(args.csv):
        df = pd.read_csv(args.csv)
    else:
        df = synthesize_data()

    out = train(df, Path(args.out_dir))
    print(f"Model saved to {out}")


if __name__ == "__main__":
    main()
