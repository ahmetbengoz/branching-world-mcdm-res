
from __future__ import annotations

import numpy as np
import pandas as pd

from config import FIGURE_FILES, TABLE_FILES
from common import (
    GROUPS,
    SCENARIOS,
    checkpoint_path,
    figure_path,
    load_percentage_data,
    make_heatmap,
    run_topsis,
    run_vikor,
    write_json,
    write_table,
)


def main() -> None:
    df = load_percentage_data()

    scenario_rows = []
    topsis_rank_table = pd.DataFrame({"CountryCode": df["CountryCode"]})
    vikor_rank_table = pd.DataFrame({"CountryCode": df["CountryCode"]})
    topsis_top10_rows = []
    vikor_top10_rows = []
    topsis_top5_summary = []

    for scenario_name, group_weights in SCENARIOS.items():
        scenario_rows.append(
            {
                "Scenario": scenario_name,
                "G1 Electricity": group_weights[0],
                "G2 Transport": group_weights[1],
                "G3 Heating/Cooling": group_weights[2],
                "G4 Gross Final Consumption": group_weights[3],
            }
        )
        # local import to avoid circular if helper renamed later
        from common import build_group_weights
        weights = build_group_weights(group_weights)
        topsis_res = run_topsis(df, weights)
        vikor_res = run_vikor(df, weights)

        topsis_rank_table = topsis_rank_table.merge(
            topsis_res[["CountryCode", "TOPSIS_rank"]].rename(columns={"TOPSIS_rank": scenario_name}),
            on="CountryCode",
            how="left",
        )
        vikor_rank_table = vikor_rank_table.merge(
            vikor_res[["CountryCode", "VIKOR_rank"]].rename(columns={"VIKOR_rank": scenario_name}),
            on="CountryCode",
            how="left",
        )

        for _, row in topsis_res.head(10).iterrows():
            topsis_top10_rows.append(
                {"scenario": scenario_name, "method": "TOPSIS", "rank": int(row["TOPSIS_rank"]), "CountryCode": row["CountryCode"], "score": float(row["TOPSIS_score"])}
            )
        for _, row in vikor_res.head(10).iterrows():
            vikor_top10_rows.append(
                {"scenario": scenario_name, "method": "VIKOR", "rank": int(row["VIKOR_rank"]), "CountryCode": row["CountryCode"], "Q": float(row["VIKOR_Q"]), "S": float(row["VIKOR_S"]), "R": float(row["VIKOR_R"])}
            )
        topsis_top5_summary.append(
            {
                "Scenario": scenario_name,
                "TOPSIS top-5": ", ".join(topsis_res.head(5)["CountryCode"].tolist()),
                "VIKOR top-5": ", ".join(vikor_res.head(5)["CountryCode"].tolist()),
            }
        )

    write_table(pd.DataFrame(scenario_rows), TABLE_FILES["table_04"])
    write_table(pd.DataFrame(topsis_top5_summary), TABLE_FILES["table_05"])
    write_table(pd.DataFrame(topsis_top10_rows), TABLE_FILES["table_S3"])
    write_table(pd.DataFrame(vikor_top10_rows), TABLE_FILES["table_S4"])

    topsis_rank_table.to_csv(checkpoint_path("topsis_scenario_ranks.csv"), index=False)
    vikor_rank_table.to_csv(checkpoint_path("vikor_scenario_ranks.csv"), index=False)

    scenario_cols = list(SCENARIOS.keys())
    balanced_order = topsis_rank_table.sort_values("S0_Balanced")["CountryCode"].tolist()
    topsis_matrix = topsis_rank_table.set_index("CountryCode").loc[balanced_order, scenario_cols].to_numpy()
    vikor_matrix = vikor_rank_table.set_index("CountryCode").loc[balanced_order, scenario_cols].to_numpy()
    make_heatmap(topsis_matrix, scenario_cols, balanced_order, "TOPSIS Rank Shift Across Policy Scenarios", figure_path(FIGURE_FILES["figure_2a"]))
    make_heatmap(vikor_matrix, scenario_cols, balanced_order, "VIKOR Rank Shift Across Policy Scenarios", figure_path(FIGURE_FILES["figure_2b"]))

    write_json({"n_scenarios": len(SCENARIOS), "scenario_names": list(SCENARIOS.keys())}, "policy_scenario_summary.json")


if __name__ == "__main__":
    main()
