## branching-world-mcdm-res

Reproducible code and outputs for a branching-world sensitivity analysis framework for robust multi-criteria decision-making (MCDM) ranking using renewable energy performance data for European countries.

## Overview

This repository contains the full reproducible pipeline used to evaluate renewable energy performance under planning uncertainty through a branching-world sensitivity analysis framework. The empirical application uses the 2022 SHARES-based renewable energy dataset for 29 European countries and evaluates ranking robustness with TOPSIS and VIKOR in parallel.

The pipeline generates the full set of final tables and figures used in the manuscript, together with supplementary outputs and intermediate checkpoints.

## Data sources

The repository uses publicly available renewable energy data derived from the SHARES collection for 2022.

Included input files in the data/ folder:

SHARES_2022_PERCENTAGE.csv
SHARES_2022_PERCENTAGE.xlsx
SHARES_2022_KTOE.csv
SHARES_2022_KTOE.xlsx
SHARES_2022_POPULATION.csv
SHARES_2022_POPULATION.xlsx
population_KES2024.csv
population_KES2024.xlsx
country_names.csv
country_names.xlsx
data_source_note.pdf

The analysis in the manuscript is based on the percentage-format decision matrix.

## Repository structure
data/ — raw input files used by the pipeline
scripts/ — modular analysis scripts and shared utilities
run_pipeline.py — single entry point for the full reproducible workflow
outputs/tables/ — final manuscript and supplementary tables in CSV and XLSX formats
outputs/figures/ — final manuscript and supplementary figures
outputs/checkpoints/ — intermediate outputs and diagnostic files created during execution
How to run

# Run the full pipeline with:

python run_pipeline.py

The pipeline executes all analysis stages in sequence and writes the final outputs to outputs/tables/ and outputs/figures/.

# Pipeline order

The workflow is executed in the following order:

01_data_audit.py
02_baseline_methods.py
03_policy_scenarios.py
04_branching_worlds.py
05_framework_sensitivity.py
06_cross_method_benchmark.py
07_redundancy_robustness.py
08_ordering_rule_sensitivity.py
09_naive_comparator_benchmark.py
Final output files
Main text tables
table_01_data_audit_summary
table_02_baseline_deterministic_rankings
table_03_baseline_method_agreement_summary
table_04_policy_priority_scenarios_and_weights
table_05_deterministic_scenario_top5_summary
table_06_branching_world_leadership_summary
table_07_balanced_robust_cross_method_top10
table_08_balanced_robust_cross_method_summary
table_09_framework_sensitivity_summary
table_10_scenariowise_robust_cross_method_summary
table_11_redundancy_robustness_summary
table_12_ordering_rule_sensitivity
table_13_naive_vs_branching_summary

Each table is produced in both .csv and .xlsx format.

# Supplementary tables
table_S1_full_correlation_matrix
table_S2_high_correlation_pairs
table_S3_topsis_top10_by_scenario
table_S4_vikor_top10_by_scenario
table_S5_full_balanced_robust_cross_method_comparison
table_S6_country_level_ordering_rule_changes
table_S7_country_level_naive_vs_branching_comparison

Each supplementary table is produced in both .csv and .xlsx format.

# Main text figures
figure_1_baseline_rank_comparison.png
figure_2a_topsis_rank_shifts.png
figure_2b_vikor_rank_shifts.png
figure_3a_topsis_framework_top10_overlap.png
figure_3b_vikor_framework_top10_overlap.png
figure_4a_topsis_framework_spearman.png
figure_4b_vikor_framework_spearman.png
figure_5_balanced_robust_rank_comparison.png
figure_6_scenariowise_top10_overlap.png
figure_7a_topsis_redundancy_rank_changes.png
figure_7b_vikor_redundancy_rank_changes.png
Supplementary figures
figure_S1_criterion_boxplots.png
figure_S2_normalized_heatmap.png
figure_S3_correlation_heatmap.png
Analysis scope

## The pipeline covers:

dataset audit and redundancy diagnostics
baseline deterministic comparison of TOPSIS and VIKOR
deterministic policy-priority scenarios
branching-world robust ranking under simultaneous weight and performance perturbations
framework-sensitivity analysis
cross-method benchmarking
redundancy-robustness analysis
ordering-rule sensitivity analysis
naive deterministic aggregation versus branching-world benchmark comparison
Reproducibility note

# The repository is organized so that the output file names produced by the code match the final table and figure identifiers used in the manuscript. No manual renaming is required after execution.
