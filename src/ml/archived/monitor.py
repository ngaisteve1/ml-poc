import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def quantify_features(csv_path: str, out_path: str):
    df = pd.read_csv(csv_path)
    cols = [
        "total_files", "avg_file_size_mb", "pct_pdf", "pct_docx", "pct_xlsx",
        "archive_frequency_per_day"
    ]
    stats = {}
    for c in cols:
        s = df[c].dropna()
        stats[c] = {
            "p10": float(np.percentile(s, 10)),
            "p50": float(np.percentile(s, 50)),
            "p90": float(np.percentile(s, 90))
        }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Wrote feature quantiles to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", default="ml-poc/models/feature_quantiles.json")
    args = parser.parse_args()
    quantify_features(args.csv, args.out)
