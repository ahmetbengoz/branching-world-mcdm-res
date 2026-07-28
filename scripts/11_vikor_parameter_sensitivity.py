from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from config import TABLE_FILES
from common import (
    BRANCHING_DEFAULTS,
    CRITERIA,
    SCENARIOS,
    build_group_weights,
    compute_metrics,
    load_percentage_data,
    run_vikor,
    sort_robust,
    table_path,
    vikor_rank_matrix,
)


V_VALUES = (0.3, 0.5, 0.7)
REFERENCE_V = 0.5


def compare_orders(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
    scenario: str,
    v: float,
    layer: str,
) -> dict[str, object]:
    ref = reference.set_index("Country")
    cand = candidate.set_index("Country")
    countries = ref.index.tolist()
    ref_ranks = ref.loc[countries, "rank"].to_numpy()
    cand_ranks = cand.loc[countries, "rank"].to_numpy()
    ref_order = ref.sort_values("rank").index.tolist()
    cand_order = cand.sort_values("rank").index.tolist()
    displacement = np.abs(ref_ranks - cand_ranks)

    return {
        "Layer": layer,
        "Scenario": scenario,
        "v": v,
        "Leader": cand_order[0],
        "Reference leader (v=0.5)": ref_order[0],
        "Leader changed": int(cand_order[0] != ref_order[0]),
        "Top-5 overlap": len(set(ref_order[:5]) & set(cand_order[:5])),
        "Top-10 overlap": len(set(ref_order[:10]) & set(cand_order[:10])),
        "Spearman rho": float(spearmanr(ref_ranks, cand_ranks).statistic),
        "Kendall tau": float(kendalltau(ref_ranks, cand_ranks).statistic),
        "Mean absolute displacement": float(displacement.mean()),
        "Maximum absolute displacement": int(displacement.max()),
    }


def deterministic_results(df: pd.DataFrame) -> pd.DataFrame:
    outputs: dict[tuple[str, float], pd.DataFrame] = {}
    for scenario, group_weights in SCENARIOS.items():
        weights = build_group_weights(group_weights)
        for v in V_VALUES:
            ranking = run_vikor(df, weights, v=v)[
                ["CountryCode", "VIKOR_rank"]
            ].rename(columns={"CountryCode": "Country", "VIKOR_rank": "rank"})
            outputs[(scenario, v)] = ranking

    comparisons = []
    for scenario in SCENARIOS:
        reference = outputs[(scenario, REFERENCE_V)]
        for v in V_VALUES:
            comparisons.append(
                compare_orders(
                    reference,
                    outputs[(scenario, v)],
                    scenario,
                    v,
                    "Deterministic",
                )
            )
    return pd.DataFrame(comparisons)


def draw_worlds(
    rng: np.random.Generator,
    base_weights: np.ndarray,
    X: np.ndarray,
    keep_vikor: bool,
) -> dict[float, np.ndarray] | None:
    n_worlds = BRANCHING_DEFAULTS["n_worlds"]
    concentration = np.where(
        base_weights * BRANCHING_DEFAULTS["alpha"] <= 0,
        1e-8,
        base_weights * BRANCHING_DEFAULTS["alpha"],
    )
    rank_matrices = (
        {v: np.zeros((n_worlds, X.shape[0]), dtype=np.int16) for v in V_VALUES}
        if keep_vikor
        else None
    )

    for world in range(n_worlds):
        sampled_weights = rng.dirichlet(concentration)
        sampled_noise = rng.uniform(
            BRANCHING_DEFAULTS["noise_low"],
            BRANCHING_DEFAULTS["noise_high"],
            size=X.shape,
        )
        if keep_vikor and rank_matrices is not None:
            perturbed = X * sampled_noise
            for v in V_VALUES:
                _, ranks = vikor_rank_matrix(perturbed, sampled_weights, v=v)
                rank_matrices[v][world] = ranks

    return rank_matrices


def branching_world_results(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    X = df[CRITERIA].to_numpy(dtype=float)
    countries = df["CountryCode"].tolist()
    rng = np.random.default_rng(42)
    outputs: dict[tuple[str, float], pd.DataFrame] = {}

    for scenario, group_weights in SCENARIOS.items():
        weights = build_group_weights(group_weights)

        # Consume the exact TOPSIS random block used by script 04 so that the
        # subsequent VIKOR worlds reproduce the manuscript's original stream.
        draw_worlds(rng, weights, X, keep_vikor=False)
        matrices = draw_worlds(rng, weights, X, keep_vikor=True)
        assert matrices is not None

        for v, rank_matrix in matrices.items():
            metrics = compute_metrics(rank_matrix)
            metrics.insert(0, "Country", countries)
            robust = sort_robust(metrics).rename(columns={"robust_rank": "rank"})
            outputs[(scenario, v)] = robust

    comparisons = []
    for scenario in SCENARIOS:
        reference = outputs[(scenario, REFERENCE_V)]
        for v in V_VALUES:
            comparisons.append(
                compare_orders(
                    reference,
                    outputs[(scenario, v)],
                    scenario,
                    v,
                    "Branching-world",
                )
            )

    balanced_details = []
    for v in V_VALUES:
        table = outputs[("S0_Balanced", v)].sort_values("rank").head(10)
        for _, row in table.iterrows():
            balanced_details.append(
                {
                    "v": v,
                    "Country": row["Country"],
                    "rank": int(row["rank"]),
                    "ER": float(row["ER"]),
                    "WWR": float(row["WWR"]),
                    "WCR": int(row["WCR"]),
                    "RV": float(row["RV"]),
                }
            )

    return pd.DataFrame(comparisons), pd.DataFrame(balanced_details)


def main() -> None:
    df = load_percentage_data()
    deterministic = deterministic_results(df)
    branching, balanced_top10 = branching_world_results(df)

    exact_table_s11 = pd.concat(
        [
            deterministic[deterministic["v"] != REFERENCE_V],
            branching[branching["v"] != REFERENCE_V],
        ],
        ignore_index=True,
    )
    exact_table_s11.to_csv(table_path(TABLE_FILES["table_S11"]), index=False)
    balanced_top10.to_csv(
        table_path(TABLE_FILES["vikor_v_balanced_top10"]), index=False
    )

    print("VIKOR v-sensitivity completed.")
    print(
        exact_table_s11[
            [
                "Layer",
                "Scenario",
                "v",
                "Leader",
                "Top-5 overlap",
                "Top-10 overlap",
                "Spearman rho",
                "Mean absolute displacement",
                "Maximum absolute displacement",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
