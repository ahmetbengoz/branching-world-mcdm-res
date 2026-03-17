# Branching-World Sensitivity Analysis for Robust Ranking in MCDM

This repository contains the reproducible materials for the manuscript:

**Branching-World Sensitivity Analysis for Robust Ranking in Multi-Criteria Decision Making: Evidence from Renewable Energy Performance of European Countries**

## Repository purpose

This repository supports the empirical analysis presented in the paper and documents the workflow used to generate the main and supplementary outputs. The repository is intended to improve transparency, reproducibility, and reusability of the proposed branching-world sensitivity analysis framework.

The repository covers:

- baseline TOPSIS ranking
- branching-world generation under perturbation
- robustness metrics, including World Win Rate (WWR), Expected Rank (ER), Worst-Case Rank (WCR), and Rank Volatility (RV)
- main-text tables and figures
- supplementary tables and figures
- country-code based output versions used in the final manuscript

## Data source

The empirical application uses the following open dataset:

Bączkiewicz, A. (2025). *Decision matrices including performance values of alternatives for evaluation European countries regarding sustainable RES share* (Version 2) [Dataset]. Mendeley Data. https://doi.org/10.17632/hyggsrh68c.2

The repository structure is organized so that the original dataset archive can be placed in `data/raw/`, while extracted or processed files can be stored in `data/processed/`.

## Repository structure

```text
branching-world-mcdm-res/
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── src/
│   ├── extract_dataset.py
│   ├── generate_analysis_outputs.py
│   └── generate_countrycode_package.py
├── outputs/
│   ├── figures/
│   └── tables/
└── paper_assets/
    ├── suggested_data_availability_statement.txt
    ├── suggested_code_availability_statement.txt
    └── supplementary_note.txt

# How to run

Install the required Python packages:
pip install -r requirements.txt

Extract the dataset:
python src/extract_dataset.py

Generate the main analysis outputs:
python src/generate_analysis_outputs.py

Generate the country-code package used in the final manuscript:
python src/generate_countrycode_package.py

# Main analytical components

The proposed framework evaluates alternatives across multiple branching worlds generated through structured perturbations in criterion weights and performance values. Instead of relying only on a single deterministic ranking, the approach interprets results through cross-world robustness behaviour.

The main metrics used in the repository are:

WWR: World Win Rate

ER: Expected Rank

WCR: Worst-Case Rank

RV: Rank Volatility

Country code note

Country codes are used in selected main-text tables and figures for consistency with the source dataset and to avoid unnecessary political interpretation. The code CY* is retained strictly for traceability and does not imply any political recognition or institutional position of the author.

Reproducibility note

This repository is intended to accompany the manuscript and provide a transparent record of the empirical workflow, output structure, and supporting materials used in the study.
