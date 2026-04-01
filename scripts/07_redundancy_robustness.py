
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from config import FIGURE_FILES, TABLE_FILES
from common import (
    CRITERIA,
    GROUPS,
    HIGH_CORR_THRESHOLD,
    checkpoint_path,
    figure_path,
    load_percentage_data,
    run_topsis,
    run_vikor,
    top_k_overlap,
    write_json,
    write_table,
)


def build_original_equal_weights() -> np.ndarray:
    return np.array([1 / 18] * 18, dtype=float)


def build_group_balanced_weights() -> np.ndarray:
    from common import build_group_weights
    return build_group_weights([0.25, 0.25, 0.25, 0.25])


def build_correlation_adjusted_weights(X_df: pd.DataFrame, threshold: float = HIGH_CORR_THRESHOLD) -> tuple[np.ndarray, pd.DataFrame]:
    base = build_group_balanced_weights()
    base_map = dict(zip(CRITERIA, base))
    corr = X_df[CRITERIA].corr(method="pearson")
    link_count = {c: 0 for c in CRITERIA}
    for i, c1 in enumerate(CRITERIA):
        for c2 in CRITERIA[i + 1:]:
            if abs(corr.loc[c1, c2]) >= threshold:
                link_count[c1] += 1
                link_count[c2] += 1
    raw = {c: base_map[c] / (1 + link_count[c]) for c in CRITERIA}
    total = sum(raw.values())
    adjusted = np.array([raw[c] / total for c in CRITERIA], dtype=float)
    details = pd.DataFrame(
        {
            "criterion": CRITERIA,
            "base_weight": [base_map[c] for c in CRITERIA],
            "high_corr_link_count": [link_count[c] for c in CRITERIA],
            "adjusted_weight": [adjusted[i] for i in range(len(CRITERIA))],
        }
    ).sort_values(["high_corr_link_count", "criterion"], ascending=[False, True]).reset_index(drop=True)
    return adjusted, details


def make_rank_change_plot(merged: pd.DataFrame, method: str, save_path):
    import matplotlib.pyplot as plt
    merged_plot = merged.sort_values("rank_M0").copy()
    x = np.arange(len(merged_plot))
    plt.figure(figsize=(12, 6))
    plt.plot(x, merged_plot["rank_M0"].values, marker="o", label="M0_OriginalEqual")
    plt.plot(x, merged_plot["rank_M1"].values, marker="o", label="M1_GroupBalanced")
    plt.plot(x, merged_plot["rank_M2"].values, marker="o", label="M2_CorrelationAdjusted")
    plt.xticks(x, merged_plot["Country"].tolist(), rotation=90)
    plt.ylabel("Rank")
    plt.title(f"{method}: Rank Changes Under Redundancy Robustness Models")
    plt.gca().invert_yaxis()
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    df = load_percentage_data()
    w_m0 = build_original_equal_weights()
    w_m1 = build_group_balanced_weights()
    w_m2, details = build_correlation_adjusted_weights(df[CRITERIA])

    weight_table = pd.DataFrame(
        {"criterion": CRITERIA, "M0_OriginalEqual": w_m0, "M1_GroupBalanced": w_m1, "M2_CorrelationAdjusted": w_m2}
    )
    weight_table.to_csv(checkpoint_path("redundancy_weights.csv"), index=False)
    details.to_csv(checkpoint_path("redundancy_correlation_adjustment_details.csv"), index=False)

    summary_rows = []
    for method in ["TOPSIS", "VIKOR"]:
        res_m0 = (run_topsis(df, w_m0) if method == "TOPSIS" else run_vikor(df, w_m0)).rename(columns={"CountryCode": "Country", "TOPSIS_rank": "rank_M0", "VIKOR_rank": "rank_M0"})
        res_m1 = (run_topsis(df, w_m1) if method == "TOPSIS" else run_vikor(df, w_m1)).rename(columns={"CountryCode": "Country", "TOPSIS_rank": "rank_M1", "VIKOR_rank": "rank_M1"})
        res_m2 = (run_topsis(df, w_m2) if method == "TOPSIS" else run_vikor(df, w_m2)).rename(columns={"CountryCode": "Country", "TOPSIS_rank": "rank_M2", "VIKOR_rank": "rank_M2"})
        merged = res_m0[["Country", "rank_M0"]].merge(res_m1[["Country", "rank_M1"]], on="Country").merge(res_m2[["Country", "rank_M2"]], on="Country")
        merged["abs_diff_M0_M1"] = (merged["rank_M0"] - merged["rank_M1"]).abs()
        merged["abs_diff_M0_M2"] = (merged["rank_M0"] - merged["rank_M2"]).abs()
        merged["abs_diff_M1_M2"] = (merged["rank_M1"] - merged["rank_M2"]).abs()
        order_m0 = merged.sort_values("rank_M0")["Country"].tolist()
        order_m1 = merged.sort_values("rank_M1")["Country"].tolist()
        order_m2 = merged.sort_values("rank_M2")["Country"].tolist()
        for comp, left, right, col in [
            ("M0_vs_M1", "M0", "M1", "abs_diff_M0_M1"),
            ("M0_vs_M2", "M0", "M2", "abs_diff_M0_M2"),
            ("M1_vs_M2", "M1", "M2", "abs_diff_M1_M2"),
        ]:
            left_rank = merged[f"rank_{left}"]
            right_rank = merged[f"rank_{right}"]
            rho, _ = spearmanr(left_rank, right_rank)
            tau, _ = kendalltau(left_rank, right_rank)
            left_order = merged.sort_values(f"rank_{left}")["Country"].tolist()
            right_order = merged.sort_values(f"rank_{right}")["Country"].tolist()
            summary_rows.append(
                {
                    "method": method,
                    "comparison": comp,
                    "top_1_left": left_order[0],
                    "top_1_right": right_order[0],
                    "top_5_overlap": int(top_k_overlap(left_order, right_order, 5)),
                    "top_10_overlap": int(top_k_overlap(left_order, right_order, 10)),
                    "spearman_rho": float(rho),
                    "kendall_tau": float(tau),
                    "mean_abs_rank_diff": float(merged[col].mean()),
                    "max_abs_rank_diff": int(merged[col].max()),
                }
            )
        if method == "TOPSIS":
            make_rank_change_plot(merged, method, figure_path(FIGURE_FILES["figure_7a"]))
        else:
            make_rank_change_plot(merged, method, figure_path(FIGURE_FILES["figure_7b"]))

    write_table(pd.DataFrame(summary_rows), TABLE_FILES["table_11"])
    write_json({"threshold": HIGH_CORR_THRESHOLD}, "redundancy_robustness_summary.json")


if __name__ == "__main__":
    main()
