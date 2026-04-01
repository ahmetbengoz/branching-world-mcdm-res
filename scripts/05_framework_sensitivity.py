
from __future__ import annotations

from itertools import product

import numpy as np
import pandas as pd

from config import FIGURE_FILES, TABLE_FILES
from common import (
    FRAMEWORK_GRID,
    METHODS,
    SCENARIOS,
    checkpoint_path,
    compute_metrics,
    figure_path,
    load_percentage_data,
    plot_line_with_labels,
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
    base_weights = build_group_weights(SCENARIOS["S0_Balanced"])

    baseline_cache = {}
    for method in METHODS:
        _, baseline_ranks = simulate_worlds(
            X=X,
            base_weights=base_weights,
            n_worlds=5000,
            alpha=20.0,
            noise_low=0.90,
            noise_high=1.10,
            method=method,
            rng=rng,
        )
        metrics = compute_metrics(baseline_ranks)
        metrics.insert(0, "Country", countries)
        baseline_cache[method] = sort_robust(metrics)

    detailed_rows = []
    for method, alpha, noise_band, n_worlds in product(METHODS, FRAMEWORK_GRID["alphas"], FRAMEWORK_GRID["noise_bands"], FRAMEWORK_GRID["world_counts"]):
        _, test_ranks = simulate_worlds(
            X=X,
            base_weights=base_weights,
            n_worlds=n_worlds,
            alpha=alpha,
            noise_low=1.0 - noise_band,
            noise_high=1.0 + noise_band,
            method=method,
            rng=rng,
        )
        metrics = compute_metrics(test_ranks)
        metrics.insert(0, "Country", countries)
        robust_df = sort_robust(metrics)
        baseline_df = baseline_cache[method]
        merged = baseline_df[["Country", "robust_rank"]].merge(
            robust_df[["Country", "robust_rank"]],
            on="Country",
            suffixes=("_baseline", "_test"),
        )
        from scipy.stats import spearmanr
        rho, _ = spearmanr(merged["robust_rank_baseline"], merged["robust_rank_test"])
        order_baseline = baseline_df.sort_values("robust_rank")["Country"].tolist()
        order_test = robust_df.sort_values("robust_rank")["Country"].tolist()
        detailed_rows.append(
            {
                "method": method,
                "alpha": alpha,
                "noise_band": noise_band,
                "n_worlds": n_worlds,
                "top_1_baseline": order_baseline[0],
                "top_1_test": order_test[0],
                "top_5_overlap": top_k_overlap(order_baseline, order_test, 5),
                "top_10_overlap": top_k_overlap(order_baseline, order_test, 10),
                "spearman_rho_vs_baseline": float(rho),
                "mean_abs_rank_diff": float((merged["robust_rank_baseline"] - merged["robust_rank_test"]).abs().mean()),
                "max_abs_rank_diff": int((merged["robust_rank_baseline"] - merged["robust_rank_test"]).abs().max()),
            }
        )
    detailed = pd.DataFrame(detailed_rows).sort_values(["method", "alpha", "noise_band", "n_worlds"]).reset_index(drop=True)
    detailed.to_csv(checkpoint_path("framework_sensitivity_detailed.csv"), index=False)

    summary_rows = []
    for method in METHODS:
        sub = detailed[detailed["method"] == method]
        observed_top1 = []
        for c in sub["top_1_test"].tolist():
            if c not in observed_top1:
                observed_top1.append(c)
        summary_rows.append(
            {
                "Method": method,
                "Spearman rho vs baseline (min–max)": f"{sub['spearman_rho_vs_baseline'].min():.6f}–{sub['spearman_rho_vs_baseline'].max():.6f}",
                "Top-10 overlap (min–max)": f"{int(sub['top_10_overlap'].min())}–{int(sub['top_10_overlap'].max())}",
                "Mean absolute rank difference (min–max)": f"{sub['mean_abs_rank_diff'].min():.6f}–{sub['mean_abs_rank_diff'].max():.6f}",
                "Observed top-1 countries": ", ".join(observed_top1),
            }
        )
        labels = [f"a{int(a)}_n{int(nb*100)}_w{int(w)}" for a, nb, w in zip(sub["alpha"], sub["noise_band"], sub["n_worlds"])]
        if method == "TOPSIS":
            plot_line_with_labels(sub["top_10_overlap"].tolist(), labels, "Top-10 Overlap vs Baseline", "TOPSIS Framework Sensitivity: Top-10 Overlap", figure_path(FIGURE_FILES["figure_3a"]))
            plot_line_with_labels(sub["spearman_rho_vs_baseline"].tolist(), labels, "Spearman rho vs Baseline", "TOPSIS Framework Sensitivity: Rank Correlation", figure_path(FIGURE_FILES["figure_4a"]))
        else:
            plot_line_with_labels(sub["top_10_overlap"].tolist(), labels, "Top-10 Overlap vs Baseline", "VIKOR Framework Sensitivity: Top-10 Overlap", figure_path(FIGURE_FILES["figure_3b"]))
            plot_line_with_labels(sub["spearman_rho_vs_baseline"].tolist(), labels, "Spearman rho vs Baseline", "VIKOR Framework Sensitivity: Rank Correlation", figure_path(FIGURE_FILES["figure_4b"]))

    write_table(pd.DataFrame(summary_rows), TABLE_FILES["table_09"])
    write_json({"n_runs": int(len(detailed)), **FRAMEWORK_GRID}, "framework_sensitivity_summary.json")


if __name__ == "__main__":
    main()
