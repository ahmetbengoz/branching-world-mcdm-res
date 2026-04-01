
from __future__ import annotations

import pandas as pd
from scipy.stats import spearmanr

from config import TABLE_FILES
from common import SCENARIOS, checkpoint_path, top_k_overlap, write_json, write_table

RULES = {
    "R0_Current_ER_WWR_RV": [("ER", True), ("WWR", False), ("RV", True)],
    "R1_ER_WWR_WCR_RV": [("ER", True), ("WWR", False), ("WCR", True), ("RV", True)],
    "R2_ER_WCR_WWR_RV": [("ER", True), ("WCR", True), ("WWR", False), ("RV", True)],
    "R3_ER_only": [("ER", True)],
    "R4_WWR_ER_RV": [("WWR", False), ("ER", True), ("RV", True)],
}


def rank_by_rule(df: pd.DataFrame, rule: list[tuple[str, bool]]) -> pd.DataFrame:
    out = df.sort_values(by=[x[0] for x in rule], ascending=[x[1] for x in rule], kind="mergesort").reset_index(drop=True).copy()
    out["computed_rank"] = range(1, len(out) + 1)
    return out


def main() -> None:
    block_rows = []
    change_rows = []
    for scenario in SCENARIOS:
        for method in ["TOPSIS", "VIKOR"]:
            grp = pd.read_csv(checkpoint_path(f"robust_metrics_{scenario}_{method}.csv"))
            base = rank_by_rule(grp, RULES["R0_Current_ER_WWR_RV"])[["Country", "computed_rank"]].rename(columns={"computed_rank": "base_rank"})
            base_order = base.sort_values("base_rank")["Country"].tolist()
            base_top1 = base_order[0]
            for rule_name, rule in RULES.items():
                ranked = rank_by_rule(grp, rule)[["Country", "computed_rank"]].rename(columns={"computed_rank": "rule_rank"})
                merged = base.merge(ranked, on="Country")
                rule_order = ranked.sort_values("rule_rank")["Country"].tolist()
                block_rows.append(
                    {
                        "scenario": scenario,
                        "method": method,
                        "rule": rule_name,
                        "top_1_country": rule_order[0],
                        "top_5_overlap_vs_current": top_k_overlap(base_order, rule_order, 5),
                        "top_10_overlap_vs_current": top_k_overlap(base_order, rule_order, 10),
                        "spearman_vs_current": float(spearmanr(merged["base_rank"], merged["rule_rank"]).statistic),
                        "mean_abs_rank_diff": float((merged["base_rank"] - merged["rule_rank"]).abs().mean()),
                        "max_abs_rank_diff": int((merged["base_rank"] - merged["rule_rank"]).abs().max()),
                        "top_1_changed_vs_current": bool(rule_order[0] != base_top1),
                    }
                )
                if rule_name != "R0_Current_ER_WWR_RV":
                    changed = merged.loc[merged["base_rank"] != merged["rule_rank"]].copy()
                    for _, row in changed.iterrows():
                        change_rows.append(
                            {
                                "scenario": scenario,
                                "method": method,
                                "rule": rule_name,
                                "Country": row["Country"],
                                "current_rank": int(row["base_rank"]),
                                "alternative_rank": int(row["rule_rank"]),
                                "abs_shift": int(abs(row["base_rank"] - row["rule_rank"])),
                            }
                        )
    block_df = pd.DataFrame(block_rows)
    block_df.to_csv(checkpoint_path("order_rule_block_summary.csv"), index=False)
    changes_df = pd.DataFrame(change_rows).sort_values(["scenario", "method", "rule", "current_rank"]).reset_index(drop=True)
    write_table(changes_df, TABLE_FILES["table_S6"])

    summary_rows = []
    alt_only = block_df[block_df["rule"] != "R0_Current_ER_WWR_RV"]
    for rule in ["R1_ER_WWR_WCR_RV", "R2_ER_WCR_WWR_RV", "R3_ER_only", "R4_WWR_ER_RV"]:
        sub = alt_only[alt_only["rule"] == rule]
        summary_rows.append(
            {
                "Alternative rule": rule,
                "Top-1 changes across 10 blocks": int(sub["top_1_changed_vs_current"].sum()),
                "Top-5 overlap vs current (min-max)": f"{int(sub['top_5_overlap_vs_current'].min())}-{int(sub['top_5_overlap_vs_current'].max())}",
                "Top-10 overlap vs current (min-max)": f"{int(sub['top_10_overlap_vs_current'].min())}-{int(sub['top_10_overlap_vs_current'].max())}",
                "Spearman vs current (min-max)": f"{sub['spearman_vs_current'].min():.6f}-{sub['spearman_vs_current'].max():.6f}",
                "Mean abs. rank diff vs current (min-max)": f"{sub['mean_abs_rank_diff'].min():.6f}-{sub['mean_abs_rank_diff'].max():.6f}",
            }
        )
    write_table(pd.DataFrame(summary_rows), TABLE_FILES["table_12"])
    write_json({"rules_tested": list(RULES.keys())}, "ordering_rule_sensitivity_summary.json")


if __name__ == "__main__":
    main()
