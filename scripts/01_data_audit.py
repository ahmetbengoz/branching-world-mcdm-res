
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import skew

from config import FIGURE_FILES, TABLE_FILES
from common import (
    CRITERIA,
    HIGH_CORR_THRESHOLD,
    checkpoint_path,
    figure_path,
    iqr_outlier_count,
    load_percentage_data,
    make_boxplot,
    make_heatmap,
    minmax_normalize,
    write_json,
    write_table,
)


def main() -> None:
    df = load_percentage_data()
    X = df[CRITERIA].copy()
    X_norm = minmax_normalize(X)

    criterion_rows = []
    for c in CRITERIA:
        s = X[c]
        criterion_rows.append(
            {
                "criterion": c,
                "n": int(s.shape[0]),
                "missing_count": int(s.isna().sum()),
                "missing_ratio": float(s.isna().mean()),
                "zero_count": int((s == 0).sum()),
                "zero_ratio": float((s == 0).mean()),
                "min": float(s.min()),
                "max": float(s.max()),
                "mean": float(s.mean()),
                "median": float(s.median()),
                "std": float(s.std(ddof=1)),
                "cv": float(s.std(ddof=1) / s.mean()) if s.mean() != 0 else np.nan,
                "skewness": float(skew(s, bias=False)),
                "iqr_outlier_count": iqr_outlier_count(s),
            }
        )
    criterion_audit = pd.DataFrame(criterion_rows).sort_values("criterion").reset_index(drop=True)
    criterion_audit.to_csv(checkpoint_path("criterion_level_audit.csv"), index=False)

    corr = X.corr(method="pearson")
    write_table(corr, TABLE_FILES["table_S1"], index=True)

    high_corr_pairs = []
    for i, c1 in enumerate(CRITERIA):
        for c2 in CRITERIA[i + 1:]:
            value = corr.loc[c1, c2]
            if abs(value) >= HIGH_CORR_THRESHOLD:
                high_corr_pairs.append(
                    {
                        "criterion_1": c1,
                        "criterion_2": c2,
                        "pearson_r": float(value),
                        "abs_r": float(abs(value)),
                    }
                )
    high_corr_df = pd.DataFrame(high_corr_pairs).sort_values("abs_r", ascending=False).reset_index(drop=True)
    write_table(high_corr_df, TABLE_FILES["table_S2"])

    summary_rows = [
        {"Audit item": "Number of countries", "Value": int(df.shape[0])},
        {"Audit item": "Number of criteria", "Value": int(len(CRITERIA))},
        {"Audit item": "Missing cells", "Value": int(X.isna().sum().sum())},
        {"Audit item": "High-correlation pairs (|r| ≥ 0.80)", "Value": int(len(high_corr_df))},
        {"Audit item": "Criterion with highest zero ratio", "Value": criterion_audit.sort_values("zero_ratio", ascending=False).iloc[0]["criterion"]},
        {"Audit item": "Highest zero ratio", "Value": float(criterion_audit["zero_ratio"].max())},
        {"Audit item": "Criterion with highest coefficient of variation", "Value": criterion_audit.sort_values("cv", ascending=False).iloc[0]["criterion"]},
        {"Audit item": "Highest coefficient of variation", "Value": float(criterion_audit["cv"].max())},
        {"Audit item": "Criterion with highest skewness", "Value": criterion_audit.sort_values("skewness", ascending=False).iloc[0]["criterion"]},
        {"Audit item": "Highest skewness", "Value": float(criterion_audit["skewness"].max())},
        {"Audit item": "Strongest correlated pair", "Value": f"{high_corr_df.iloc[0]['criterion_1']}–{high_corr_df.iloc[0]['criterion_2']}"},
        {"Audit item": "Correlation of strongest pair", "Value": float(high_corr_df.iloc[0]["abs_r"])},
        {"Audit item": "Second strongest correlated pair", "Value": f"{high_corr_df.iloc[1]['criterion_1']}–{high_corr_df.iloc[1]['criterion_2']}"},
        {"Audit item": "Correlation of second strongest pair", "Value": float(high_corr_df.iloc[1]["abs_r"])},
        {"Audit item": "Third strongest correlated pair", "Value": f"{high_corr_df.iloc[2]['criterion_1']}–{high_corr_df.iloc[2]['criterion_2']}"},
        {"Audit item": "Correlation of third strongest pair", "Value": float(high_corr_df.iloc[2]["abs_r"])},
    ]
    summary_df = pd.DataFrame(summary_rows)
    write_table(summary_df, TABLE_FILES["table_01"])

    norm_country_df = X_norm.copy()
    norm_country_df.index = df["CountryCode"]
    norm_country_df.to_csv(checkpoint_path("normalized_matrix.csv"))

    make_boxplot(X, figure_path(FIGURE_FILES["figure_S1"]))
    make_heatmap(norm_country_df.values, CRITERIA, norm_country_df.index.tolist(), "Normalized Performance Matrix", figure_path(FIGURE_FILES["figure_S2"]))
    make_heatmap(corr.values, corr.columns.tolist(), corr.index.tolist(), "Criterion Correlation Matrix", figure_path(FIGURE_FILES["figure_S3"]), vmin=-1, vmax=1)

    write_json(
        {
            "n_countries": int(df.shape[0]),
            "n_criteria": int(len(CRITERIA)),
            "total_missing_cells": int(X.isna().sum().sum()),
            "num_high_corr_pairs": int(len(high_corr_df)),
        },
        "audit_summary.json",
    )


if __name__ == "__main__":
    main()
