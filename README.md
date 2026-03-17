Branching-World Sensitivity Analysis for Robust Ranking in MCDM

This repository contains the reproducible materials for the manuscript:

Branching-World Sensitivity Analysis for Robust Ranking in Multi-Criteria Decision Making: Evidence from Renewable Energy Performance of European Countries

Repository purpose

This repository reproduces the empirical workflow used in the paper:

baseline TOPSIS ranking

branching-world generation

robustness metrics (WWR, ER, WCR, RV)

main-text tables and figures

supplementary tables and figures

country-code package used in the final manuscript

Data source

The study uses the open Mendeley Data dataset:

Bączkiewicz, A. (2025). Decision matrices including performance values of alternatives for evaluation European countries regarding sustainable RES share (Version 2) [Dataset]. Mendeley Data. https://doi.org/10.17632/hyggsrh68c.2

Structure

data/

src/

paper_assets/

How to run
pip install -r requirements.txt
python src/extract_dataset.py
python src/generate_analysis_outputs.py
python src/generate_countrycode_package.py

pip install -r requirements.txt
python src/extract_dataset.py
python src/generate_analysis_outputs.py
python src/generate_countrycode_package.py
