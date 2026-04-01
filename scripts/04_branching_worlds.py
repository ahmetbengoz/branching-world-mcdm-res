
from __future__ import annotations

import numpy as np
import pandas as pd

from config import FIGURE_FILES, TABLE_FILES
from common import (
    BRANCHING_DEFAULTS,
    METHODS,
    SCENARIOS,
    checkpoint_path,
    compute_metrics,
    figure_path,
    load_percentage_data,
    plot_rank_scatter,
    simulate_worlds,
    sort_robust,
    top_k_overlap,
    write_json,
    write_table,
)


def main() -> None:
    from common import build_group_weights
    rng = np.random.default_rng(42)
    df = load_percentage_data()
    from common import CRITERIA
    X = df[CRITERIA].to_numpy(dtype=float)
    countries = df["CountryCode"].tolist()

    robust_outputs: dict[tuple[str, str], pd.DataFrame] = {}
    leadership_rows = []

    for scenario_name, group_weights in SCENARIOS.items():
        base_weights = build_group_weights(group_weights)
        for method in METHODS:
            _, ranks_worlds = simulate_worlds(
                X=X,
                base_weights=base_weights,
                n_worlds=BRANCHING_DEFAULTS["n_worlds"],
                alpha=BRANCHING_DEFAULTS["alpha"],
                noise_low=BRANCHING_DEFAULTS["noise_low"],
                noise_high=BRANCHING_DEFAULTS["noise_high"],
                method=method,
                rng=rng,
            )
            metrics = compute_metrics(ranks_worlds)
            metrics.insert(0, "Country", countries)
            robust_df = sort_robust(metrics)
            robust_df["scenario"] = scenario_name
            robust_df["method"] = method
            robust_outputs[(scenario_name, method)] = robust_df.copy()
            robust_df.to_csv(checkpoint_path(f"robust_metrics_{scenario_name}_{method}.csv"), index=False)
            np.save(checkpoint_path(f"ranks_{scenario_name}_{method}.npy"), ranks_worlds)
            top5 = robust_df.sort_values("robust_rank").head(5)["Country"].tolist()
            leadership_rows.append(
                {
                    "Scenario": scenario_name,
                    "Method": method,
                    "Top-1 country": robust_df.sort_values("robust_rank").iloc[0]["Country"],
                    "Top-5 countries": "; ".join(top5),
                }
            )

    write_table(pd.DataFrame(leadership_rows), TABLE_FILES["table_06"])

    balanced_topsis = robust_outputs[("S0_Balanced", "TOPSIS")]
    balanced_vikor = robust_outputs[("S0_Balanced", "VIKOR")]
    robust_compare = balanced_topsis[["Country", "robust_rank", "ER", "WWR", "WCR", "RV"]].merge(
        balanced_vikor[["Country", "robust_rank", "ER", "WWR", "WCR", "RV"]],
        on="Country",
        suffixes=("_TOPSIS", "_VIKOR"),
    )
    robust_compare["Absolute rank difference"] = (robust_compare["robust_rank_TOPSIS"] - robust_compare["robust_rank_VIKOR"]).abs()
    robust_compare = robust_compare.sort_values(["robust_rank_TOPSIS", "robust_rank_VIKOR"]).reset_index(drop=True)

    write_table(robust_compare.head(10), TABLE_FILES["table_07"])
    write_table(robust_compare, TABLE_FILES["table_S5"])

    order_t = robust_compare.sort_values("robust_rank_TOPSIS")["Country"].tolist()
    order_v = robust_compare.sort_values("robust_rank_VIKOR")["Country"].tolist()
    from scipy.stats import kendalltau, spearmanr
    rho, _ = spearmanr(robust_compare["robust_rank_TOPSIS"], robust_compare["robust_rank_VIKOR"])
    tau, _ = kendalltau(robust_compare["robust_rank_TOPSIS"], robust_compare["robust_rank_VIKOR"])
    summary = pd.DataFrame(
        [
            {"Metric": "Spearman rho", "Value": float(rho)},
            {"Metric": "Kendall tau", "Value": float(tau)},
            {"Metric": "Top-5 overlap", "Value": int(top_k_overlap(order_t, order_v, 5))},
            {"Metric": "Top-10 overlap", "Value": int(top_k_overlap(order_t, order_v, 10))},
            {"Metric": "Mean absolute rank difference", "Value": float(robust_compare["Absolute rank difference"].mean())},
            {"Metric": "Maximum absolute rank difference", "Value": int(robust_compare["Absolute rank difference"].max())},
        ]
    )
    write_table(summary, TABLE_FILES["table_08"])

    plot_rank_scatter(
        robust_compare["robust_rank_TOPSIS"],
        robust_compare["robust_rank_VIKOR"],
        robust_compare["Country"].tolist(),
        "TOPSIS Robust Rank",
        "VIKOR Robust Rank",
        "Balanced Scenario: Robust Rank Comparison",
        figure_path(FIGURE_FILES["figure_5"]),
    )

    write_json(
        {
            "n_worlds": BRANCHING_DEFAULTS["n_worlds"],
            "alpha": BRANCHING_DEFAULTS["alpha"],
            "noise_low": BRANCHING_DEFAULTS["noise_low"],
            "noise_high": BRANCHING_DEFAULTS["noise_high"],
            "balanced_top_3_topsis": balanced_topsis.sort_values("robust_rank").head(3)["Country"].tolist(),
            "balanced_top_3_vikor": balanced_vikor.sort_values("robust_rank").head(3)["Country"].tolist(),
        },
        "branching_world_summary.json",
    )


if __name__ == "__main__":
    main()
