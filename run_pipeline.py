from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
SCRIPT_ORDER = [
    "01_data_audit.py",
    "02_baseline_methods.py",
    "03_policy_scenarios.py",
    "04_branching_worlds.py",
    "05_framework_sensitivity.py",
    "06_cross_method_benchmark.py",
    "07_redundancy_robustness.py",
    "08_ordering_rule_sensitivity.py",
    "09_naive_comparator_benchmark.py",
    "10_c15_exclusion_robustness.py",
    "11_vikor_parameter_sensitivity.py",
    "12_paired_bootstrap.py",
]


def main() -> None:
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(SCRIPT_DIR))
    for script_name in SCRIPT_ORDER:
        script_path = SCRIPT_DIR / script_name
        print(f"Running {script_name} ...")
        runpy.run_path(str(script_path), run_name="__main__")
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
