from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "SHARES_2022_PERCENTAGE.csv"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

COUNTRY_CODE = {
    "Belgium": "BE", "Bulgaria": "BG", "Czechia": "CZ", "Denmark": "DK",
    "Germany": "DE", "Estonia": "EE", "Greece": "GR", "Spain": "ES",
    "France": "FR", "Croatia": "HR", "Ireland": "IE", "Italy": "IT",
    "Cyprus": "CY", "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU",
    "Hungary": "HU", "Malta": "MT", "Netherlands": "NL", "Austria": "AT",
    "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Slovenia": "SI",
    "Slovakia": "SK", "Finland": "FI", "Sweden": "SE", "Iceland": "IS", "Norway": "NO",
}

CRITERIA = [f"C{i}" for i in range(1, 19)]
# Full-model group architecture: C1-C5, C6-C9, C10-C15, C16-C18.
GROUPS_FULL = [list(range(0, 5)), list(range(5, 9)), list(range(9, 15)), list(range(15, 18))]
# No-C15 architecture preserves groups; G3 is recalculated over C10-C14.
GROUPS_NO_C15 = [list(range(0, 5)), list(range(5, 9)), list(range(9, 14)), list(range(14, 17))]
BRANCHING_DEFAULTS = {"n_worlds": 5000, "alpha": 20, "noise_low": 0.90, "noise_high": 1.10, "seed": 42}


def build_group_weights(n_criteria: int, groups: list[list[int]]) -> np.ndarray:
    group_weights = [0.25, 0.25, 0.25, 0.25]
    w = np.zeros(n_criteria)
    for gi, group in enumerate(groups):
        for j in group:
            w[j] = group_weights[gi] / len(group)
    return w


def ranks_from_scores(scores: np.ndarray, descending: bool = True) -> np.ndarray:
    order = np.argsort(-scores if descending else scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def topsis_rank(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    denom = np.sqrt((X ** 2).sum(axis=0))
    denom[denom == 0] = 1.0
    V = X / denom * w
    ideal = V.max(axis=0)
    anti = V.min(axis=0)
    dpos = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    dneg = np.sqrt(((V - anti) ** 2).sum(axis=1))
    score = dneg / (dpos + dneg)
    return ranks_from_scores(score, descending=True)


def vikor_rank(X: np.ndarray, w: np.ndarray, v: float = 0.5) -> np.ndarray:
    fstar = X.max(axis=0)
    fminus = X.min(axis=0)
    denom = fstar - fminus
    denom[denom == 0] = 1.0
    regret = w * (fstar - X) / denom
    S = regret.sum(axis=1)
    R = regret.max(axis=1)
    Q = v * (S - S.min()) / (S.max() - S.min()) + (1 - v) * (R - R.min()) / (R.max() - R.min())
    return ranks_from_scores(Q, descending=False)


def simulate_worlds(X: np.ndarray, groups: list[list[int]], method: str, rng: np.random.Generator) -> np.ndarray:
    base_weights = build_group_weights(X.shape[1], groups)
    concentration = base_weights * BRANCHING_DEFAULTS["alpha"]
    ranks_worlds = np.empty((BRANCHING_DEFAULTS["n_worlds"], X.shape[0]), dtype=np.int16)
    for t in range(BRANCHING_DEFAULTS["n_worlds"]):
        weights = rng.dirichlet(concentration)
        perturbed = X * rng.uniform(BRANCHING_DEFAULTS["noise_low"], BRANCHING_DEFAULTS["noise_high"], size=X.shape)
        ranks_worlds[t] = topsis_rank(perturbed, weights) if method == "TOPSIS" else vikor_rank(perturbed, weights)
    return ranks_worlds


def robust_metrics(ranks_worlds: np.ndarray, countries: list[str]) -> pd.DataFrame:
    ER = ranks_worlds.mean(axis=0)
    WWR = (ranks_worlds == 1).mean(axis=0)
    WCR = ranks_worlds.max(axis=0)
    RV = ranks_worlds.std(axis=0, ddof=0)
    order = sorted(range(len(countries)), key=lambda i: (ER[i], -WWR[i], RV[i]))
    robust_rank = np.empty(len(countries), dtype=int)
    robust_rank[order] = np.arange(1, len(countries) + 1)
    return pd.DataFrame({"Country": countries, "ER": ER, "WWR": WWR, "WCR": WCR.astype(int), "RV": RV, "robust_rank": robust_rank})


def main() -> None:
    df = pd.read_csv(DATA_FILE)
    countries = [COUNTRY_CODE.get(c, c) for c in df["Country"].tolist()]
    X_full = df[CRITERIA].to_numpy(dtype=float)
    keep = [c for c in CRITERIA if c != "C15"]
    X_no_c15 = df[keep].to_numpy(dtype=float)

    outputs: dict[tuple[str, str], pd.DataFrame] = {}
    for label, X, groups in [
        ("Full 18-criterion model", X_full, GROUPS_FULL),
        ("No-C15 17-criterion model", X_no_c15, GROUPS_NO_C15),
    ]:
        rng = np.random.default_rng(BRANCHING_DEFAULTS["seed"])
        for method in ["TOPSIS", "VIKOR"]:
            ranks_worlds = simulate_worlds(X, groups, method, rng)
            outputs[(label, method)] = robust_metrics(ranks_worlds, countries)

    summary_rows = []
    comparison_rows = []
    no_c15_top10_rows = []
    for method in ["TOPSIS", "VIKOR"]:
        full = outputs[("Full 18-criterion model", method)].set_index("Country")
        no_c15 = outputs[("No-C15 17-criterion model", method)].set_index("Country")
        rank_full = np.array([full.loc[c, "robust_rank"] for c in countries])
        rank_no_c15 = np.array([no_c15.loc[c, "robust_rank"] for c in countries])
        order_full = full.sort_values("robust_rank").index.tolist()
        order_no_c15 = no_c15.sort_values("robust_rank").index.tolist()

        for c in countries:
            comparison_rows.append({
                "Country": c,
                "Method": method,
                "Full robust rank": int(full.loc[c, "robust_rank"]),
                "No-C15 robust rank": int(no_c15.loc[c, "robust_rank"]),
                "Rank change (No-C15 minus full)": int(no_c15.loc[c, "robust_rank"] - full.loc[c, "robust_rank"]),
                "Absolute displacement": int(abs(no_c15.loc[c, "robust_rank"] - full.loc[c, "robust_rank"])),
                "No-C15 ER": float(no_c15.loc[c, "ER"]),
                "No-C15 WWR": float(no_c15.loc[c, "WWR"]),
                "No-C15 WCR": int(no_c15.loc[c, "WCR"]),
                "No-C15 RV": float(no_c15.loc[c, "RV"]),
            })

        for c in order_no_c15[:10]:
            no_c15_top10_rows.append({
                "Method": method,
                "Country": c,
                "robust_rank": int(no_c15.loc[c, "robust_rank"]),
                "ER": float(no_c15.loc[c, "ER"]),
                "WWR": float(no_c15.loc[c, "WWR"]),
                "WCR": int(no_c15.loc[c, "WCR"]),
                "RV": float(no_c15.loc[c, "RV"]),
            })

        summary_rows.append({
            "Method": method,
            "Full-model leader": order_full[0],
            "No-C15 leader": order_no_c15[0],
            "Top-5 overlap": len(set(order_full[:5]) & set(order_no_c15[:5])),
            "Top-10 overlap": len(set(order_full[:10]) & set(order_no_c15[:10])),
            "Spearman rho": float(spearmanr(rank_full, rank_no_c15).statistic),
            "Kendall tau": float(kendalltau(rank_full, rank_no_c15).statistic),
            "Mean absolute displacement": float(np.mean(np.abs(rank_no_c15 - rank_full))),
            "Maximum absolute displacement": int(np.max(np.abs(rank_no_c15 - rank_full))),
            "Sweden rank change": int(rank_no_c15[countries.index("SE")] - rank_full[countries.index("SE")]),
            "Norway rank change": int(rank_no_c15[countries.index("NO")] - rank_full[countries.index("NO")]),
            "Iceland rank change": int(rank_no_c15[countries.index("IS")] - rank_full[countries.index("IS")]),
            "Malta rank change": int(rank_no_c15[countries.index("MT")] - rank_full[countries.index("MT")]),
        })

    summary = pd.DataFrame(summary_rows)
    comparison = pd.DataFrame(comparison_rows).sort_values(["Method", "Full robust rank"])
    no_c15_top10 = pd.DataFrame(no_c15_top10_rows)

    summary.to_csv(TABLE_DIR / "table_14_c15_exclusion_summary.csv", index=False)
    comparison.to_csv(TABLE_DIR / "table_S8_c15_exclusion_full_comparison.csv", index=False)
    no_c15_top10.to_csv(TABLE_DIR / "table_S9_no_c15_top10_robust_metrics.csv", index=False)

    # Deterministic full versus no-C15 comparison under the same balanced group architecture.
    deterministic_rows = []
    for label, X, groups in [
        ("Full 18-criterion model", X_full, GROUPS_FULL),
        ("No-C15 17-criterion model", X_no_c15, GROUPS_NO_C15),
    ]:
        base_w = build_group_weights(X.shape[1], groups)
        topsis_r = topsis_rank(X, base_w)
        vikor_r = vikor_rank(X, base_w)
        for c, tr, vr in zip(countries, topsis_r, vikor_r):
            deterministic_rows.append({
                "model": label,
                "Country": c,
                "TOPSIS_rank": int(tr),
                "VIKOR_rank": int(vr),
            })
    deterministic = pd.DataFrame(deterministic_rows)
    deterministic.to_csv(TABLE_DIR / "table_S10_c15_exclusion_deterministic_comparison.csv", index=False)
    with pd.ExcelWriter(TABLE_DIR / "c15_exclusion_outputs.xlsx") as writer:
        summary.to_excel(writer, sheet_name="Table_14_summary", index=False)
        comparison.to_excel(writer, sheet_name="Table_S8_full", index=False)
        no_c15_top10.to_excel(writer, sheet_name="Table_S9_top10", index=False)
        deterministic.to_excel(writer, sheet_name="Table_S10_deterministic", index=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    for method, offset in [("TOPSIS", 0.1), ("VIKOR", -0.1)]:
        d = comparison[comparison["Method"] == method]
        ax.scatter(d["Full robust rank"], d["Rank change (No-C15 minus full)"] + offset, label=method, s=28)
    ax.axhline(0, linewidth=0.8)
    ax.set_xlabel("Full-model robust rank")
    ax.set_ylabel("Rank change after excluding C15")
    ax.set_title("C15 exclusion rank displacement")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure_S4_c15_rank_displacement.png", dpi=300)


if __name__ == "__main__":
    main()
