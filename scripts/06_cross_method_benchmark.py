
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from config import FIGURE_FILES, TABLE_FILES
from common import checkpoint_path, figure_path, plot_line_with_labels, top_k_overlap, write_json, write_table

SCENARIOS = [
    "S0_Balanced",
    "S1_ElectricityPriority",
    "S2_TransportPriority",
    "S3_HeatingCoolingPriority",
    "S4_FinalConsumptionPriority",
]


def main() -> None:
    scenario_rows = []
    balanced_merge = None
    for scenario in SCENARIOS:
        topsis_df = pd.read_csv(checkpoint_path(f"robust_metrics_{scenario}_TOPSIS.csv"))
        vikor_df = pd.read_csv(checkpoint_path(f"robust_metrics_{scenario}_VIKOR.csv"))
        merged = topsis_df[["Country", "robust_rank", "ER", "WWR", "WCR", "RV"]].merge(
            vikor_df[["Country", "robust_rank", "ER", "WWR", "WCR", "RV"]],
            on="Country",
            suffixes=("_TOPSIS", "_VIKOR"),
        )
        merged["abs_rank_diff"] = (merged["robust_rank_TOPSIS"] - merged["robust_rank_VIKOR"]).abs()
        merged = merged.sort_values(["robust_rank_TOPSIS", "robust_rank_VIKOR"]).reset_index(drop=True)
        rho, _ = spearmanr(merged["robust_rank_TOPSIS"], merged["robust_rank_VIKOR"])
        tau, _ = kendalltau(merged["robust_rank_TOPSIS"], merged["robust_rank_VIKOR"])
        topsis_order = merged.sort_values("robust_rank_TOPSIS")["Country"].tolist()
        vikor_order = merged.sort_values("robust_rank_VIKOR")["Country"].tolist()
        scenario_rows.append(
            {
                "Scenario": scenario,
                "TOPSIS top-1": topsis_order[0],
                "VIKOR top-1": vikor_order[0],
                "Top-5 overlap": int(top_k_overlap(topsis_order, vikor_order, 5)),
                "Top-10 overlap": int(top_k_overlap(topsis_order, vikor_order, 10)),
                "Spearman rho": float(rho),
                "Kendall tau": float(tau),
                "Mean absolute rank difference": float(merged["abs_rank_diff"].mean()),
            }
        )
        if scenario == "S0_Balanced":
            balanced_merge = merged.copy()

    scenario_summary = pd.DataFrame(scenario_rows)
    write_table(scenario_summary, TABLE_FILES["table_10"])

    labels = scenario_summary["Scenario"].tolist()
    values = scenario_summary["Top-10 overlap"].tolist()
    plot_line_with_labels(values, labels, "TOPSIS vs VIKOR Top-10 Overlap", "Scenario-wise Cross-Method Top-10 Overlap", figure_path(FIGURE_FILES["figure_6"]))

    write_json({"n_scenarios": len(SCENARIOS)}, "cross_method_benchmark_summary.json")


if __name__ == "__main__":
    main()
