
from __future__ import annotations

import pandas as pd

from config import FIGURE_FILES, TABLE_FILES
from common import (
    CRITERIA,
    checkpoint_path,
    figure_path,
    load_percentage_data,
    mean_kendall_spearman,
    plot_rank_scatter,
    run_topsis,
    run_vikor,
    top_k_overlap,
    write_json,
    write_table,
)


def main() -> None:
    df = load_percentage_data()
    weights = [1 / 18] * 18
    topsis = run_topsis(df, weights)
    vikor = run_vikor(df, weights)

    merged = topsis.merge(vikor, on="CountryCode", how="inner")
    merged["Absolute rank difference"] = (merged["TOPSIS_rank"] - merged["VIKOR_rank"]).abs()
    merged = merged.sort_values("TOPSIS_rank").reset_index(drop=True)

    top10 = merged.head(10).copy()
    top10 = top10.rename(
        columns={
            "CountryCode": "Country",
            "TOPSIS_score": "TOPSIS score",
            "TOPSIS_rank": "TOPSIS rank",
            "VIKOR_S": "VIKOR S",
            "VIKOR_R": "VIKOR R",
            "VIKOR_Q": "VIKOR Q",
            "VIKOR_rank": "VIKOR rank",
        }
    )
    write_table(top10, TABLE_FILES["table_02"])

    order_t = merged.sort_values("TOPSIS_rank")["CountryCode"].tolist()
    order_v = merged.sort_values("VIKOR_rank")["CountryCode"].tolist()
    rho, tau = mean_kendall_spearman(merged["TOPSIS_rank"], merged["VIKOR_rank"])
    summary = pd.DataFrame(
        [
            {"Metric": "Spearman rho", "Value": rho},
            {"Metric": "Kendall tau", "Value": tau},
            {"Metric": "Top-5 overlap", "Value": int(top_k_overlap(order_t, order_v, 5))},
            {"Metric": "Top-10 overlap", "Value": int(top_k_overlap(order_t, order_v, 10))},
            {"Metric": "Mean absolute rank difference", "Value": float(merged["Absolute rank difference"].mean())},
            {"Metric": "Maximum absolute rank difference", "Value": int(merged["Absolute rank difference"].max())},
        ]
    )
    write_table(summary, TABLE_FILES["table_03"])

    plot_rank_scatter(
        merged["TOPSIS_rank"],
        merged["VIKOR_rank"],
        merged["CountryCode"].tolist(),
        "TOPSIS Rank",
        "VIKOR Rank",
        "Baseline Rank Comparison: TOPSIS vs VIKOR",
        figure_path(FIGURE_FILES["figure_1"]),
    )

    merged.to_csv(checkpoint_path("baseline_method_results.csv"), index=False)
    write_json(
        {
            "spearman_rho": rho,
            "kendall_tau": tau,
            "top_5_overlap": int(top_k_overlap(order_t, order_v, 5)),
            "top_10_overlap": int(top_k_overlap(order_t, order_v, 10)),
            "best_topsis_country": order_t[0],
            "best_vikor_country": order_v[0],
        },
        "baseline_method_summary.json",
    )


if __name__ == "__main__":
    main()
