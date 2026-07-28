from __future__ import annotations

import numpy as np
import pandas as pd

from config import TABLE_FILES
from common import checkpoint_path, load_percentage_data, table_path


N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 18
CONFIDENCE_LEVEL = 0.95


def bootstrap_mean_interval(
    differences: np.ndarray,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = np.empty(n_bootstrap, dtype=float)
    n_worlds = len(differences)
    for sample in range(n_bootstrap):
        indices = rng.integers(0, n_worlds, size=n_worlds)
        means[sample] = differences[indices].mean()
    alpha = 1.0 - CONFIDENCE_LEVEL
    low, high = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(low), float(high)


def main() -> None:
    df = load_percentage_data()
    countries = df["CountryCode"].tolist()
    se_index = countries.index("SE")
    no_index = countries.index("NO")

    rows = []
    for method in ("TOPSIS", "VIKOR"):
        ranks = np.load(checkpoint_path(f"ranks_S0_Balanced_{method}.npy"))
        differences = ranks[:, no_index] - ranks[:, se_index]
        low, high = bootstrap_mean_interval(differences)
        rows.append(
            {
                "Method": method,
                "Within-world difference": "R_NO - R_SE",
                "Number of worlds": len(differences),
                "Bootstrap resamples": N_BOOTSTRAP,
                "Bootstrap seed": BOOTSTRAP_SEED,
                "Mean difference": float(differences.mean()),
                "95% interval lower": low,
                "95% interval upper": high,
                "Interpretation": "Positive values favour SE",
            }
        )

    output = pd.DataFrame(rows)
    output.to_csv(table_path(TABLE_FILES["paired_bootstrap"]), index=False)
    print("Paired bootstrap completed.")
    print(output.to_string(index=False))


if __name__ == "__main__":
    main()
