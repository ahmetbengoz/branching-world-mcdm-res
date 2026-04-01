
from __future__ import annotations

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
FIG_DIR = OUTPUT_DIR / "figures"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

INPUT_FILE = DATA_DIR / "SHARES_2022_PERCENTAGE.csv"

for p in [OUTPUT_DIR, TABLE_DIR, FIG_DIR, CHECKPOINT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

TABLE_FILES = {
    "table_01": "table_01_data_audit_summary",
    "table_02": "table_02_baseline_deterministic_rankings",
    "table_03": "table_03_baseline_method_agreement_summary",
    "table_04": "table_04_policy_priority_scenarios_and_weights",
    "table_05": "table_05_deterministic_scenario_top5_summary",
    "table_06": "table_06_branching_world_leadership_summary",
    "table_07": "table_07_balanced_robust_cross_method_top10",
    "table_08": "table_08_balanced_robust_cross_method_summary",
    "table_09": "table_09_framework_sensitivity_summary",
    "table_10": "table_10_scenariowise_robust_cross_method_summary",
    "table_11": "table_11_redundancy_robustness_summary",
    "table_12": "table_12_ordering_rule_sensitivity",
    "table_13": "table_13_naive_vs_branching_summary",
    "table_S1": "table_S1_full_correlation_matrix",
    "table_S2": "table_S2_high_correlation_pairs",
    "table_S3": "table_S3_topsis_top10_by_scenario",
    "table_S4": "table_S4_vikor_top10_by_scenario",
    "table_S5": "table_S5_full_balanced_robust_cross_method_comparison",
    "table_S6": "table_S6_country_level_ordering_rule_changes",
    "table_S7": "table_S7_country_level_naive_vs_branching_comparison",
}

FIGURE_FILES = {
    "figure_1": "figure_1_baseline_rank_comparison.png",
    "figure_2a": "figure_2a_topsis_rank_shifts.png",
    "figure_2b": "figure_2b_vikor_rank_shifts.png",
    "figure_3a": "figure_3a_topsis_framework_top10_overlap.png",
    "figure_3b": "figure_3b_vikor_framework_top10_overlap.png",
    "figure_4a": "figure_4a_topsis_framework_spearman.png",
    "figure_4b": "figure_4b_vikor_framework_spearman.png",
    "figure_5": "figure_5_balanced_robust_rank_comparison.png",
    "figure_6": "figure_6_scenariowise_top10_overlap.png",
    "figure_7a": "figure_7a_topsis_redundancy_rank_changes.png",
    "figure_7b": "figure_7b_vikor_redundancy_rank_changes.png",
    "figure_S1": "figure_S1_criterion_boxplots.png",
    "figure_S2": "figure_S2_normalized_heatmap.png",
    "figure_S3": "figure_S3_correlation_heatmap.png",
}
