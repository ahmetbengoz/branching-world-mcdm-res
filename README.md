# Branching-World Sensitivity Analysis for Robust Renewable Energy Benchmarking

This repository contains the reproducible code, input data structure, output tables and figures for the manuscript:

**Robust renewable energy performance benchmarking under planning uncertainty: A branching-world sensitivity analysis of European countries**

The study develops a branching-world sensitivity analysis framework for robust multi-criteria decision-making (MCDM) benchmarking. The empirical application evaluates renewable-energy performance for 29 European countries using the 2022 percentage-based SHARES decision matrix and compares TOPSIS and VIKOR under deterministic, scenario-based, stochastic and redundancy-adjusted specifications.

## Repository purpose

This repository is intended to support transparency, reproducibility and independent verification of the manuscript results. It provides the workflow used to generate the main-text tables, supplementary tables, figures and robustness diagnostics reported in the revised manuscript.

The pipeline covers:

* dataset audit and redundancy diagnostics;
* deterministic TOPSIS and VIKOR baseline rankings;
* policy-priority scenario analysis;
* branching-world simulation under simultaneous weight and performance perturbation;
* framework-sensitivity analysis;
* cross-method benchmarking;
* redundancy-robustness analysis;
* ordering-rule sensitivity analysis;
* naive deterministic aggregation comparison;
* C15 exclusion robustness analysis added during revision;
* VIKOR compromise-parameter sensitivity at `v = 0.3, 0.5, 0.7`;
* paired bootstrap separation of the two leading balanced-world alternatives.

## Data source

The empirical dataset used in the study is publicly available from Mendeley Data:

Bączkiewicz, A., Wątróbski, J. and Krol, R. (2025), *Decision matrix including performance values of alternatives for evaluation European countries regarding sustainable RES share*, Version 2, Mendeley Data. https://doi.org/10.17632/hyggsrh68c.2

The manuscript analysis uses the **2022 percentage-based SHARES matrix** for 29 European countries and 18 criteria.

## Required input file

The main pipeline expects the following file:

```text
data/SHARES_2022_PERCENTAGE.csv
```

This is the required input file for reproducing the manuscript analysis.

Optional auxiliary files may also be retained in the `data/` folder:

```text
data/SHARES_2022_PERCENTAGE.xlsx
data/SHARES_2022_KTOE.csv
data/SHARES_2022_KTOE.xlsx
data/SHARES_2022_POPULATION.csv
data/SHARES_2022_POPULATION.xlsx
data/population_KES2024.csv
data/population_KES2024.xlsx
data/country_names.csv
data/country_names.xlsx
```

## Repository structure

```text
branching-world-mcdm-res/
├── data/
│   ├── README.md
│   ├── SHARES_2022_PERCENTAGE.csv
│   ├── SHARES_2022_PERCENTAGE.xlsx
│   ├── SHARES_2022_KTOE.csv
│   ├── SHARES_2022_KTOE.xlsx
│   ├── SHARES_2022_POPULATION.csv
│   ├── SHARES_2022_POPULATION.xlsx
│   ├── population_KES2024.csv
│   ├── population_KES2024.xlsx
│   ├── country_names.csv
│   └── country_names.xlsx
│
├── scripts/
│   ├── 01_data_audit.py
│   ├── 02_baseline_methods.py
│   ├── 03_policy_scenarios.py
│   ├── 04_branching_worlds.py
│   ├── 05_framework_sensitivity.py
│   ├── 06_cross_method_benchmark.py
│   ├── 07_redundancy_robustness.py
│   ├── 08_ordering_rule_sensitivity.py
│   ├── 09_naive_comparator_benchmark.py
│   ├── 10_c15_exclusion_robustness.py
│   ├── 11_vikor_parameter_sensitivity.py
│   └── 12_paired_bootstrap.py
│
├── outputs/
│   ├── tables/
│   ├── figures/
│   └── checkpoints/
│
├── .zenodo.json
├── CITATION.cff
├── config.py
├── common.py
├── run_pipeline.py
├── requirements.txt
├── environment.yml
├── LICENSE
└── README.md
```

## How to run

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the full reproducible pipeline:

```bash
python run_pipeline.py
```

The pipeline writes final tables to:

```text
outputs/tables/
```

and figures to:

```text
outputs/figures/
```

Intermediate diagnostic outputs are written to:

```text
outputs/checkpoints/
```

## Pipeline order

The workflow is executed in the following order:

```text
01_data_audit.py
02_baseline_methods.py
03_policy_scenarios.py
04_branching_worlds.py
05_framework_sensitivity.py
06_cross_method_benchmark.py
07_redundancy_robustness.py
08_ordering_rule_sensitivity.py
09_naive_comparator_benchmark.py
10_c15_exclusion_robustness.py
11_vikor_parameter_sensitivity.py
12_paired_bootstrap.py
```

## Main-text tables

The pipeline generates the following main-text tables:

```text
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
table_15_c15_exclusion_summary
```

## Supplementary tables

The pipeline generates the following supplementary tables:

```text
table_S1_full_correlation_matrix
table_S2_high_correlation_pairs
table_S3_topsis_top10_by_scenario
table_S4_vikor_top10_by_scenario
table_S5_full_balanced_robust_cross_method_comparison
table_S6_country_level_ordering_rule_changes
table_S7_country_level_naive_vs_branching_comparison
table_S8_c15_exclusion_full_comparison
table_S9_no_c15_top10_robust_metrics
table_S10_c15_exclusion_deterministic_comparison
table_S11_vikor_parameter_sensitivity
vikor_v_balanced_top10_supporting
paired_bootstrap_leader_separation
c15_exclusion_outputs
```

## Figures

Main-text figures:

```text
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
```

Supplementary figures:

```text
figure_S1_criterion_boxplots.png
figure_S2_normalized_heatmap.png
figure_S3_correlation_heatmap.png
figure_S4_c15_rank_displacement.png
```

## Revision-specific C15 robustness test

During revision, an additional exclusion-based robustness test was added for criterion C15 because it had the highest zero ratio, coefficient of variation and skewness in the audited matrix.

The C15 exclusion analysis removes C15 from the 18-criterion decision matrix and recomputes:

* deterministic TOPSIS and VIKOR comparisons;
* balanced branching-world robust rankings;
* full-model versus no-C15 rank displacement;
* top-5 and top-10 overlap;
* Spearman rank correlation;
* maximum rank displacement.

The results are reported in:

```text
outputs/tables/table_15_c15_exclusion_summary.csv
outputs/tables/table_S8_c15_exclusion_full_comparison.csv
outputs/tables/table_S9_no_c15_top10_robust_metrics.csv
outputs/tables/table_S10_c15_exclusion_deterministic_comparison.csv
outputs/tables/c15_exclusion_outputs.xlsx
outputs/figures/figure_S4_c15_rank_displacement.png
```

## Revision-specific VIKOR and bootstrap tests

`scripts/11_vikor_parameter_sensitivity.py` reproduces Supplementary
Table S11. It re-estimates deterministic and branching-world VIKOR
rankings at `v = 0.3, 0.5, 0.7` and compares each non-reference result
with the scenario-specific `v = 0.5` ordering. The same sampled weights
and performance-noise matrices are reused across values of `v`.

`scripts/12_paired_bootstrap.py` reproduces the paired bootstrap reported
in the manuscript. It resamples the 5,000 balanced-world within-world
rank differences `R_NO - R_SE` 10,000 times using a fixed seed.

The corresponding outputs are:

```text
outputs/tables/table_S11_vikor_parameter_sensitivity.csv
outputs/tables/vikor_v_balanced_top10_supporting.csv
outputs/tables/paired_bootstrap_leader_separation.csv
```

## Reproducibility note

The repository is organized so that output file names match the table and figure identifiers used in the manuscript and supplementary material. After running the pipeline, no manual renaming is required.

## License

This repository is released under the MIT License.
