
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, skew, spearmanr

from config import CHECKPOINT_DIR, FIG_DIR, INPUT_FILE, TABLE_DIR

COUNTRY_CODE_MAP = {
    "Austria": "AT",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Czechia": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "GR",
    "Hungary": "HU",
    "Iceland": "IS",
    "Ireland": "IE",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Netherlands": "NL",
    "The Netherlands": "NL",
    "Norway": "NO",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
}

CRITERIA = [f"C{i}" for i in range(1, 19)]
GROUPS = {
    "G1_Electricity": ["C1", "C2", "C3", "C4", "C5"],
    "G2_Transport": ["C6", "C7", "C8", "C9"],
    "G3_HeatingCooling": ["C10", "C11", "C12", "C13", "C14", "C15"],
    "G4_GrossFinalConsumption": ["C16", "C17", "C18"],
}
SCENARIOS = {
    "S0_Balanced": [0.25, 0.25, 0.25, 0.25],
    "S1_ElectricityPriority": [0.40, 0.20, 0.20, 0.20],
    "S2_TransportPriority": [0.20, 0.40, 0.20, 0.20],
    "S3_HeatingCoolingPriority": [0.20, 0.20, 0.40, 0.20],
    "S4_FinalConsumptionPriority": [0.20, 0.20, 0.20, 0.40],
}
METHODS = ["TOPSIS", "VIKOR"]
VIKOR_V = 0.5
HIGH_CORR_THRESHOLD = 0.80
RANDOM_SEED = 42
BRANCHING_DEFAULTS = {
    "n_worlds": 5000,
    "alpha": 20.0,
    "noise_low": 0.90,
    "noise_high": 1.10,
}
FRAMEWORK_GRID = {
    "alphas": [5.0, 20.0, 50.0],
    "noise_bands": [0.05, 0.10, 0.15],
    "world_counts": [1000, 5000, 10000],
}


def table_path(stem: str, suffix: str = ".csv") -> Path:
    return TABLE_DIR / f"{stem}{suffix}"


def figure_path(filename: str) -> Path:
    return FIG_DIR / filename


def checkpoint_path(name: str) -> Path:
    return CHECKPOINT_DIR / name


def write_table(df: pd.DataFrame, stem: str, index: bool = False) -> None:
    csv_path = table_path(stem, ".csv")
    xlsx_path = table_path(stem, ".xlsx")
    df.to_csv(csv_path, index=index)
    df.to_excel(xlsx_path, index=index)


def write_json(obj: dict, name: str) -> None:
    with open(checkpoint_path(name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def load_percentage_data(path: Path = INPUT_FILE, code_col_name: str = "CountryCode") -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    country_col = None
    for candidate in ["Country", "country", "Country Name"]:
        if candidate in df.columns:
            country_col = candidate
            break
    if country_col is None:
        raise KeyError(f"Country column not found. Columns: {df.columns.tolist()}")
    df[code_col_name] = df[country_col].astype(str).str.strip().map(COUNTRY_CODE_MAP)
    if df[code_col_name].isna().any():
        bad = df.loc[df[code_col_name].isna(), [country_col]]
        raise ValueError("Unmapped country names:\n" + bad.to_string(index=False))
    missing_criteria = [c for c in CRITERIA if c not in df.columns]
    if missing_criteria:
        raise ValueError(f"Missing criteria columns: {missing_criteria}")
    return df[[country_col, code_col_name] + CRITERIA].copy()


def validate_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 1 or len(weights) != len(CRITERIA):
        raise ValueError("Invalid weight vector shape.")
    if np.any(weights < 0):
        raise ValueError("Weights must be non-negative.")
    s = weights.sum()
    if s <= 0:
        raise ValueError("Weights must sum to a positive value.")
    return weights / s


def build_group_weights(group_weights: list[float]) -> np.ndarray:
    if len(group_weights) != len(GROUPS):
        raise ValueError("group_weights length mismatch.")
    if not np.isclose(sum(group_weights), 1.0):
        raise ValueError("group weights must sum to 1.")
    w = {}
    for g_name, g_weight in zip(GROUPS.keys(), group_weights):
        members = GROUPS[g_name]
        per_criterion = g_weight / len(members)
        for c in members:
            w[c] = per_criterion
    return validate_weights(np.array([w[c] for c in CRITERIA], dtype=float))


def normalize_vector_topsis(X: np.ndarray) -> np.ndarray:
    denom = np.sqrt((X ** 2).sum(axis=0))
    denom = np.where(denom == 0, 1.0, denom)
    return X / denom


def run_topsis(df: pd.DataFrame, weights: np.ndarray, code_col: str = "CountryCode") -> pd.DataFrame:
    X = df[CRITERIA].to_numpy(dtype=float)
    w = validate_weights(weights)
    X_norm = normalize_vector_topsis(X)
    X_weighted = X_norm * w
    ideal_best = X_weighted.max(axis=0)
    ideal_worst = X_weighted.min(axis=0)
    d_plus = np.sqrt(((X_weighted - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((X_weighted - ideal_worst) ** 2).sum(axis=1))
    closeness = d_minus / (d_plus + d_minus + 1e-12)
    out = pd.DataFrame({code_col: df[code_col], "TOPSIS_score": closeness}).sort_values(
        "TOPSIS_score", ascending=False, kind="mergesort"
    ).reset_index(drop=True)
    out["TOPSIS_rank"] = np.arange(1, len(out) + 1)
    return out


def run_vikor(df: pd.DataFrame, weights: np.ndarray, code_col: str = "CountryCode", v: float = VIKOR_V) -> pd.DataFrame:
    X = df[CRITERIA].to_numpy(dtype=float)
    w = validate_weights(weights)
    f_star = X.max(axis=0)
    f_minus = X.min(axis=0)
    denom = f_star - f_minus
    denom = np.where(denom == 0, 1.0, denom)
    weighted_gap = w * (f_star - X) / denom
    S = weighted_gap.sum(axis=1)
    R = weighted_gap.max(axis=1)
    S_star, S_minus = S.min(), S.max()
    R_star, R_minus = R.min(), R.max()
    S_denom = (S_minus - S_star) if (S_minus - S_star) != 0 else 1.0
    R_denom = (R_minus - R_star) if (R_minus - R_star) != 0 else 1.0
    Q = v * (S - S_star) / S_denom + (1 - v) * (R - R_star) / R_denom
    out = pd.DataFrame({code_col: df[code_col], "VIKOR_S": S, "VIKOR_R": R, "VIKOR_Q": Q}).sort_values(
        ["VIKOR_Q", "VIKOR_S", "VIKOR_R"], ascending=[True, True, True], kind="mergesort"
    ).reset_index(drop=True)
    out["VIKOR_rank"] = np.arange(1, len(out) + 1)
    return out


def topsis_rank_matrix(X: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    X_norm = normalize_vector_topsis(X)
    X_weighted = X_norm * validate_weights(weights)
    ideal_best = X_weighted.max(axis=0)
    ideal_worst = X_weighted.min(axis=0)
    d_plus = np.sqrt(((X_weighted - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((X_weighted - ideal_worst) ** 2).sum(axis=1))
    scores = d_minus / (d_plus + d_minus + 1e-12)
    order = np.argsort(-scores, kind="mergesort")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(scores) + 1)
    return scores, ranks


def vikor_rank_matrix(X: np.ndarray, weights: np.ndarray, v: float = VIKOR_V) -> tuple[np.ndarray, np.ndarray]:
    w = validate_weights(weights)
    f_star = X.max(axis=0)
    f_minus = X.min(axis=0)
    denom = f_star - f_minus
    denom = np.where(denom == 0, 1.0, denom)
    weighted_gap = w * (f_star - X) / denom
    S = weighted_gap.sum(axis=1)
    R = weighted_gap.max(axis=1)
    S_star, S_minus = S.min(), S.max()
    R_star, R_minus = R.min(), R.max()
    S_denom = (S_minus - S_star) if (S_minus - S_star) != 0 else 1.0
    R_denom = (R_minus - R_star) if (R_minus - R_star) != 0 else 1.0
    Q = v * (S - S_star) / S_denom + (1 - v) * (R - R_star) / R_denom
    order = np.argsort(Q, kind="mergesort")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(Q) + 1)
    return Q, ranks


def run_method_matrix(X: np.ndarray, weights: np.ndarray, method: str) -> tuple[np.ndarray, np.ndarray]:
    if method == "TOPSIS":
        return topsis_rank_matrix(X, weights)
    if method == "VIKOR":
        return vikor_rank_matrix(X, weights, v=VIKOR_V)
    raise ValueError(f"Unknown method: {method}")


def compute_metrics(rank_matrix: np.ndarray) -> pd.DataFrame:
    n_worlds, n_alt = rank_matrix.shape
    ER = rank_matrix.mean(axis=0)
    WCR = rank_matrix.max(axis=0)
    RV = rank_matrix.std(axis=0, ddof=1)
    WWR = np.zeros(n_alt, dtype=float)
    for i in range(n_worlds):
        best_rank = rank_matrix[i].min()
        winners = np.where(rank_matrix[i] == best_rank)[0]
        WWR[winners] += 1.0 / len(winners)
    WWR = WWR / n_worlds
    return pd.DataFrame({"ER": ER, "WWR": WWR, "WCR": WCR, "RV": RV})


def sort_robust(metrics_df: pd.DataFrame, rule: list[tuple[str, bool]] | None = None) -> pd.DataFrame:
    if rule is None:
        rule = [("ER", True), ("WWR", False), ("RV", True)]
    by = [name for name, _ in rule]
    ascending = [is_asc for _, is_asc in rule]
    out = metrics_df.sort_values(by=by, ascending=ascending, kind="mergesort").reset_index(drop=True)
    out["robust_rank"] = np.arange(1, len(out) + 1)
    return out


def simulate_worlds(
    X: np.ndarray,
    base_weights: np.ndarray,
    n_worlds: int,
    alpha: float,
    noise_low: float,
    noise_high: float,
    method: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    n_alt, _ = X.shape
    all_scores = np.zeros((n_worlds, n_alt), dtype=float)
    all_ranks = np.zeros((n_worlds, n_alt), dtype=int)
    concentration = np.where(base_weights * alpha <= 0, 1e-8, base_weights * alpha)
    for i in range(n_worlds):
        sampled_weights = rng.dirichlet(concentration)
        sampled_noise = rng.uniform(noise_low, noise_high, size=X.shape)
        X_perturbed = X * sampled_noise
        scores, ranks = run_method_matrix(X_perturbed, sampled_weights, method)
        all_scores[i, :] = scores
        all_ranks[i, :] = ranks
    return all_scores, all_ranks


def top_k_overlap(order_a: list[str], order_b: list[str], k: int) -> int:
    return len(set(order_a[:k]).intersection(set(order_b[:k])))


def iqr_outlier_count(series: pd.Series) -> int:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((series < lower) | (series > upper)).sum())


def minmax_normalize(df: pd.DataFrame) -> pd.DataFrame:
    denom = df.max() - df.min()
    denom = denom.replace(0, np.nan)
    return ((df - df.min()) / denom).fillna(0.0)


def make_boxplot(df: pd.DataFrame, save_path: Path) -> None:
    plt.figure(figsize=(14, 6))
    df.boxplot(rot=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def make_heatmap(matrix: np.ndarray, xticks: list[str], yticks: list[str], title: str, save_path: Path, vmin=None, vmax=None) -> None:
    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(matrix, aspect="auto", vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(xticks)))
    ax.set_xticklabels(xticks, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(yticks)))
    ax.set_yticklabels(yticks)
    ax.set_title(title)
    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_rank_scatter(x: Iterable[float], y: Iterable[float], labels: list[str], xlabel: str, ylabel: str, title: str, save_path: Path) -> None:
    x = np.asarray(list(x), dtype=float)
    y = np.asarray(list(y), dtype=float)
    plt.figure(figsize=(8, 8))
    plt.scatter(x, y)
    for xi, yi, label in zip(x, y, labels):
        plt.text(xi + 0.1, yi + 0.1, label, fontsize=8)
    max_rank = int(max(x.max(), y.max()))
    plt.plot([1, max_rank], [1, max_rank], linestyle="--")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.gca().invert_xaxis()
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_line_with_labels(values: list[float], labels: list[str], ylabel: str, title: str, save_path: Path) -> None:
    x = np.arange(len(values))
    plt.figure(figsize=(10, 6))
    plt.plot(x, values, marker="o")
    plt.xticks(x, labels, rotation=90)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def mean_kendall_spearman(rank_a: pd.Series, rank_b: pd.Series) -> tuple[float, float]:
    rho, _ = spearmanr(rank_a, rank_b)
    tau, _ = kendalltau(rank_a, rank_b)
    return float(rho), float(tau)
