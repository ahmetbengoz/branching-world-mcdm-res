
from __future__ import annotations

import pandas as pd
from scipy.stats import kendalltau, spearmanr

from config import TABLE_FILES
from common import checkpoint_path, top_k_overlap, write_json, write_table

SCENARIOS = [
    "S0_Balanced",
    "S1_ElectricityPriority",
    "S2_TransportPriority",
    "S3_HeatingCoolingPriority",
    "S4_FinalConsumptionPriority",
]


def melt_deterministic(path: str, method: str) -> pd.DataFrame:
    wide = pd.read_csv(path)
    return wide.melt(id_vars="CountryCode", value_vars=SCENARIOS, var_name="scenario", value_name="det_rank").assign(method=method)


def main() -> None:
    det_topsis = melt_deterministic(str(checkpoint_path("topsis_scenario_ranks.csv")), "TOPSIS")
    det_vikor = melt_deterministic(str(checkpoint_path("vikor_scenario_ranks.csv")), "VIKOR")
    det_long = pd.concat([det_topsis, det_vikor], ignore_index=True)

    robust_tables = []
    for scenario in SCENARIOS:
        for method in ["TOPSIS", "VIKOR"]:
            robust_tables.append(pd.read_csv(checkpoint_path(f"robust_metrics_{scenario}_{method}.csv")))
    robust_long = pd.concat(robust_tables, ignore_index=True)[["Country", "scenario", "method", "robust_rank"]].rename(columns={"Country": "CountryCode"})

    det_avg = det_long.groupby(["CountryCode", "method"], as_index=False)["det_rank"].mean().rename(columns={"det_rank": "mean_deterministic_rank"})
    robust_avg = robust_long.groupby(["CountryCode", "method"], as_index=False)["robust_rank"].mean().rename(columns={"robust_rank": "mean_branching_world_rank"})
    compare = det_avg.merge(robust_avg, on=["CountryCode", "method"])
    compare["naive_rank"] = compare.groupby("method")["mean_deterministic_rank"].rank(method="first").astype(int)
    compare["branching_rank"] = compare.groupby("method")["mean_branching_world_rank"].rank(method="first").astype(int)
    compare["abs_rank_shift"] = (compare["naive_rank"] - compare["branching_rank"]).abs().astype(int)
    compare = compare.sort_values(["method", "naive_rank", "CountryCode"]).reset_index(drop=True)
    write_table(compare, TABLE_FILES["table_S7"])

    summary_rows = []
    for method, grp in compare.groupby("method", sort=True):
        naive_order = grp.sort_values("naive_rank")["CountryCode"].tolist()
        branching_order = grp.sort_values("branching_rank")["CountryCode"].tolist()
        rho, _ = spearmanr(grp["naive_rank"], grp["branching_rank"])
        tau, _ = kendalltau(grp["naive_rank"], grp["branching_rank"])
        summary_rows.append(
            {
                "Method": method,
                "Naive top-1": naive_order[0],
                "Branching top-1": branching_order[0],
                "Top-5 overlap": int(top_k_overlap(naive_order, branching_order, 5)),
                "Top-10 overlap": int(top_k_overlap(naive_order, branching_order, 10)),
                "Spearman rho": float(rho),
                "Kendall tau": float(tau),
                "Mean abs. rank diff": float(grp["abs_rank_shift"].mean()),
                "Max abs. rank diff": int(grp["abs_rank_shift"].max()),
            }
        )
    write_table(pd.DataFrame(summary_rows), TABLE_FILES["table_13"])
    write_json({"note": "With a fixed number of alternatives and no ties, mean-rank aggregation and equal-weight Borda aggregation are ordinally equivalent."}, "naive_vs_branching_summary.json")


if __name__ == "__main__":
    main()
