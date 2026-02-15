"""
content_pollution.py — Blockchain Pollution Probability Model
=============================================================

Models the probability that Bitcoin blocks contain "toxic" content
(illegal material via Ordinals/inscriptions, OP_RETURN abuse, etc.)
and projects a saturation curve over time.

Institutional compliance frameworks may treat polluted blocks as
a liability — this model quantifies the risk trajectory.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.special import expit


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_BLOCK_SIZE_MB = 4.0           # SegWit theoretical max (weight units)
TYPICAL_BLOCK_SIZE_MB = 1.8       # Average observed mid-2025
BLOCKS_PER_DAY = 144
BLOCKS_PER_YEAR = BLOCKS_PER_DAY * 365
TOTAL_BLOCKS_2025 = 880_000       # Approximate block height mid-2025


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class BlockSnapshot:
    """A snapshot of blockchain content metrics for a given period.

    Attributes
    ----------
    date : str
        ISO date string (YYYY-MM-DD).
    avg_block_size_mb : float
        Average block size in megabytes.
    op_return_pct : float
        Percentage of transactions using OP_RETURN (0–100).
    inscription_count : int
        Number of Ordinals inscriptions in the period.
    inscription_size_mb : float
        Total inscription data size in megabytes.
    avg_fee_sat_vb : float
        Average transaction fee in sat/vB.
    flagged_content_count : int
        Number of inscriptions flagged as potentially problematic.
    total_transactions : int
        Total transactions in the period.
    """
    date: str
    avg_block_size_mb: float
    op_return_pct: float
    inscription_count: int
    inscription_size_mb: float
    avg_fee_sat_vb: float
    flagged_content_count: int
    total_transactions: int


@dataclass
class PollutionResult:
    """Result of pollution probability analysis for a single snapshot.

    Attributes
    ----------
    date : str
        ISO date string.
    block_utilization : float
        Fraction of max block space used (0–1).
    inscription_density : float
        Inscriptions per block.
    pollution_probability : float
        Estimated probability a random block contains toxic content (0–1).
    cumulative_tainted_pct : float
        Estimated percentage of all historical blocks that are tainted.
    fee_displacement_ratio : float
        Ratio of inscription fees to financial transaction fees.
    """
    date: str
    block_utilization: float
    inscription_density: float
    pollution_probability: float
    cumulative_tainted_pct: float
    fee_displacement_ratio: float


# ---------------------------------------------------------------------------
# Synthetic Historical Data (realistic estimates)
# ---------------------------------------------------------------------------

DEFAULT_SNAPSHOTS: List[BlockSnapshot] = [
    # Pre-Ordinals baseline
    BlockSnapshot("2022-06-01", 1.3, 1.8, 0, 0.0, 12.0, 0, 280_000),
    BlockSnapshot("2022-12-01", 1.2, 1.7, 0, 0.0, 8.0, 0, 260_000),
    # Ordinals launch wave
    BlockSnapshot("2023-02-01", 1.5, 2.0, 5_000, 15.0, 18.0, 5, 300_000),
    BlockSnapshot("2023-05-01", 2.2, 2.5, 120_000, 450.0, 85.0, 180, 450_000),
    BlockSnapshot("2023-08-01", 1.8, 2.2, 80_000, 280.0, 35.0, 120, 380_000),
    BlockSnapshot("2023-11-01", 2.0, 2.8, 200_000, 800.0, 65.0, 350, 420_000),
    # 2024: post-halving, BRC-20, Runes
    BlockSnapshot("2024-02-01", 2.3, 3.2, 350_000, 1400.0, 90.0, 600, 480_000),
    BlockSnapshot("2024-05-01", 2.5, 3.5, 500_000, 2200.0, 120.0, 950, 520_000),
    BlockSnapshot("2024-08-01", 2.1, 3.0, 280_000, 1100.0, 55.0, 500, 400_000),
    BlockSnapshot("2024-11-01", 2.4, 3.3, 420_000, 1800.0, 75.0, 780, 460_000),
    # 2025: maturation phase
    BlockSnapshot("2025-02-01", 2.6, 3.8, 550_000, 2500.0, 95.0, 1100, 500_000),
    BlockSnapshot("2025-05-01", 2.7, 4.0, 600_000, 2800.0, 110.0, 1300, 510_000),
]


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def logistic_saturation(
    t: np.ndarray,
    capacity: float,
    rate: float,
    midpoint: float,
) -> np.ndarray:
    """Logistic growth model for pollution saturation.

    Parameters
    ----------
    t : np.ndarray
        Time variable (e.g. months since start).
    capacity : float
        Maximum saturation level (asymptote).
    rate : float
        Growth rate.
    midpoint : float
        Time at which growth is at 50% of capacity.

    Returns
    -------
    np.ndarray
        Saturation values at each time point.
    """
    return capacity * expit(rate * (t - midpoint))


def calculate_pollution_probability(snapshot: BlockSnapshot) -> float:
    """Estimate the probability that a random block in this period is 'toxic'.

    Combines multiple risk factors:
    - Inscription density relative to block count
    - Flagged content ratio
    - Block utilization pressure

    Parameters
    ----------
    snapshot : BlockSnapshot
        Blockchain metrics for the period.

    Returns
    -------
    float
        Pollution probability in [0, 1].
    """
    blocks_in_period = BLOCKS_PER_DAY * 30  # ~monthly snapshots

    # Factor 1: Inscription density (inscriptions per block)
    inscription_density = snapshot.inscription_count / max(blocks_in_period, 1)
    # Normalize: 100+ inscriptions/block → high density
    density_score = min(inscription_density / 100.0, 1.0)

    # Factor 2: Flagged content ratio
    if snapshot.inscription_count > 0:
        flag_ratio = snapshot.flagged_content_count / snapshot.inscription_count
    else:
        flag_ratio = 0.0
    # Scale up: even 0.2% flagged is significant
    flag_score = min(flag_ratio * 50.0, 1.0)

    # Factor 3: Block utilization (fuller blocks = more inscription pressure)
    utilization = snapshot.avg_block_size_mb / MAX_BLOCK_SIZE_MB
    utilization_score = utilization ** 2  # Quadratic — high utilization amplifies risk

    # Factor 4: OP_RETURN abuse (above 2% is elevated)
    op_return_score = min(snapshot.op_return_pct / 8.0, 1.0)

    # Factor 5: Fee-market pushback (Easley, O'Hara & Basu, 2019)
    # Higher fees price out low-value inscriptions; block space is an auction.
    # At high fee levels, financial txs outbid pollution content.
    # Baseline: 20 sat/vB median. Above ~100 sat/vB, significant pushback.
    fee_pushback = 1.0 / (1.0 + (snapshot.avg_fee_sat_vb / 100.0) ** 2)
    # fee_pushback ≈ 1.0 at low fees, ≈ 0.5 at 100 sat/vB, → 0 at high fees

    # Weighted combination
    # Weights justified by relative importance:
    # - inscription density (0.30): direct measure of pollution volume
    # - flagged content (0.25): direct measure of toxic content
    # - block utilization (0.15): pressure indicator
    # - OP_RETURN (0.10): secondary pollution vector
    # - fee pushback (0.20): economic self-regulation mechanism (dampener)
    raw_score = (
        0.30 * density_score
        + 0.25 * flag_score
        + 0.15 * utilization_score
        + 0.10 * op_return_score
    ) * (0.5 + 0.5 * fee_pushback)  # fee market dampens pollution at high fees

    # Gate on inscription/flagged content existence: without inscriptions,
    # pollution probability should be near zero regardless of utilization/OP_RETURN.
    # Ramps linearly from 0 to 1 as inscriptions increase (saturates at 1000/period).
    inscription_gate = min(1.0, (snapshot.inscription_count + snapshot.flagged_content_count) / 1000.0)

    # Apply sigmoid for smooth probability
    # Threshold 0.3 chosen as midpoint where pollution becomes "likely"
    return float(inscription_gate * expit(6.0 * (raw_score - 0.3)))


def estimate_cumulative_tainted(
    snapshot: BlockSnapshot,
    total_blocks: int = TOTAL_BLOCKS_2025,
) -> float:
    """Estimate the cumulative percentage of all blocks that are tainted.

    A block is considered 'tainted' if it contains at least one inscription
    that could be flagged as problematic content.

    Parameters
    ----------
    snapshot : BlockSnapshot
        Current period metrics.
    total_blocks : int
        Total blockchain height.

    Returns
    -------
    float
        Percentage of all historical blocks estimated as tainted (0–100).
    """
    # Rough estimate: flagged inscriptions spread across blocks
    # Assume ~70% of flagged inscriptions are in unique blocks
    tainted_blocks_estimate = snapshot.flagged_content_count * 0.7

    # Running cumulative (simplified — in reality would aggregate)
    cumulative_pct = (tainted_blocks_estimate / total_blocks) * 100.0

    return min(cumulative_pct, 100.0)


def calculate_fee_displacement(snapshot: BlockSnapshot) -> float:
    """Calculate the ratio of block space used by inscriptions vs financial txs.

    Parameters
    ----------
    snapshot : BlockSnapshot
        Blockchain metrics.

    Returns
    -------
    float
        Fee displacement ratio (>1 means inscriptions dominate).
    """
    if snapshot.inscription_size_mb <= 0:
        return 0.0

    blocks_in_period = BLOCKS_PER_DAY * 30
    total_block_space_mb = blocks_in_period * snapshot.avg_block_size_mb

    if total_block_space_mb <= 0:
        return 0.0

    inscription_share = snapshot.inscription_size_mb / total_block_space_mb
    financial_share = 1.0 - inscription_share

    if financial_share <= 0.01:
        return 100.0

    return inscription_share / financial_share


def analyze_snapshots(
    snapshots: List[BlockSnapshot] = DEFAULT_SNAPSHOTS,
) -> pd.DataFrame:
    """Run pollution analysis across all snapshots.

    Parameters
    ----------
    snapshots : list of BlockSnapshot
        Historical blockchain metrics.

    Returns
    -------
    pd.DataFrame
        Analysis results for each snapshot period.
    """
    results = []
    for snap in snapshots:
        blocks_in_period = BLOCKS_PER_DAY * 30
        inscription_density = snap.inscription_count / max(blocks_in_period, 1)
        utilization = snap.avg_block_size_mb / MAX_BLOCK_SIZE_MB

        result = PollutionResult(
            date=snap.date,
            block_utilization=utilization,
            inscription_density=inscription_density,
            pollution_probability=calculate_pollution_probability(snap),
            cumulative_tainted_pct=estimate_cumulative_tainted(snap),
            fee_displacement_ratio=calculate_fee_displacement(snap),
        )
        results.append(result)

    records = [
        {
            "date": r.date,
            "block_utilization": r.block_utilization,
            "inscription_density": r.inscription_density,
            "pollution_probability": r.pollution_probability,
            "cumulative_tainted_pct": r.cumulative_tainted_pct,
            "fee_displacement_ratio": r.fee_displacement_ratio,
        }
        for r in results
    ]

    return pd.DataFrame(records)


def fit_saturation_curve(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Fit a logistic saturation curve to pollution probability over time.

    Parameters
    ----------
    df : pd.DataFrame
        Analysis results from analyze_snapshots().

    Returns
    -------
    tuple
        (t_forecast, y_forecast, params) — time array, fitted values,
        and fitted parameter dict.
    """
    t = np.arange(len(df), dtype=float)
    y = df["pollution_probability"].values

    try:
        popt, _ = curve_fit(
            logistic_saturation,
            t,
            y,
            p0=[0.8, 0.5, 6.0],
            bounds=([0.01, 0.01, 0.0], [1.0, 5.0, 50.0]),
            maxfev=10_000,
        )
    except RuntimeError:
        popt = np.array([0.8, 0.3, 6.0])

    params = {"capacity": popt[0], "rate": popt[1], "midpoint": popt[2]}

    # Forecast 24 months ahead
    t_forecast = np.linspace(0, len(df) + 24, 200)
    y_forecast = logistic_saturation(t_forecast, *popt)

    return t_forecast, y_forecast, params


def plot_pollution_analysis(
    df: pd.DataFrame,
    t_forecast: np.ndarray,
    y_forecast: np.ndarray,
    saturation_params: dict,
    output_path: Optional[str] = None,
) -> None:
    """Create a multi-panel visualization of blockchain pollution analysis.

    Parameters
    ----------
    df : pd.DataFrame
        Analysis results.
    t_forecast : np.ndarray
        Time array for saturation curve.
    y_forecast : np.ndarray
        Fitted saturation curve values.
    saturation_params : dict
        Fitted logistic parameters.
    output_path : str, optional
        File path to save the plot.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        "Bitcoin Blockchain Content Pollution Analysis",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    dates = pd.to_datetime(df["date"])

    # --- Panel 1: Pollution Probability + Saturation Curve ---
    ax1 = axes[0, 0]
    ax1.scatter(
        range(len(df)),
        df["pollution_probability"] * 100,
        color="#e74c3c",
        s=60,
        zorder=5,
        label="Observed",
    )
    ax1.plot(
        t_forecast,
        y_forecast * 100,
        color="#e74c3c",
        linewidth=2,
        alpha=0.7,
        linestyle="--",
        label=f"Saturation fit (cap={saturation_params['capacity']:.1%})",
    )
    ax1.axhline(
        y=saturation_params["capacity"] * 100,
        color="gray",
        linestyle=":",
        alpha=0.5,
    )
    ax1.set_ylabel("Toxic Block Probability (%)")
    ax1.set_title("Pollution Probability & Saturation Curve")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-5, 105)

    # --- Panel 2: Inscription Density ---
    ax2 = axes[0, 1]
    ax2.bar(
        range(len(df)),
        df["inscription_density"],
        color="#3498db",
        alpha=0.7,
    )
    ax2.set_ylabel("Inscriptions per Block")
    ax2.set_title("Inscription Density Over Time")
    ax2.grid(True, alpha=0.3, axis="y")

    # --- Panel 3: Block Utilization ---
    ax3 = axes[1, 0]
    ax3.fill_between(
        range(len(df)),
        df["block_utilization"] * 100,
        alpha=0.3,
        color="#2ecc71",
    )
    ax3.plot(
        range(len(df)),
        df["block_utilization"] * 100,
        color="#2ecc71",
        linewidth=2,
    )
    ax3.axhline(y=100, color="red", linestyle="--", alpha=0.5, label="Max capacity")
    ax3.set_ylabel("Block Utilization (%)")
    ax3.set_title("Block Space Utilization")
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 110)

    # --- Panel 4: Fee Displacement ---
    ax4 = axes[1, 1]
    ax4.bar(
        range(len(df)),
        df["fee_displacement_ratio"],
        color="#f39c12",
        alpha=0.7,
    )
    ax4.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, label="Parity line")
    ax4.set_ylabel("Inscription / Financial Ratio")
    ax4.set_title("Fee Displacement Ratio")
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis="y")

    # X-axis labels for all panels
    date_labels = [d.strftime("%b %y") for d in dates]
    for ax in axes.flat:
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(date_labels, rotation=45, fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"  📊 Plot saved to {output_path}")

    plt.close(fig)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("  🧪 Bitcoin Blockchain Content Pollution Analysis")
    print("  Model: powsec-models v0.2.0")
    print("=" * 72)

    # --- Run Analysis ---
    print("\n🔍 Analyzing blockchain content metrics...\n")
    df = analyze_snapshots()

    # --- Summary Table ---
    print(f"  {'Date':<12} {'Utiliz':>8} {'Insc/Blk':>10} {'Pollution':>10} "
          f"{'Tainted%':>10} {'Fee Displ':>10}")
    print(f"  {'─' * 12} {'─' * 8} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10}")

    for _, row in df.iterrows():
        print(
            f"  {row['date']:<12} "
            f"{row['block_utilization']:>7.1%} "
            f"{row['inscription_density']:>9.1f} "
            f"{row['pollution_probability']:>9.1%} "
            f"{row['cumulative_tainted_pct']:>9.4f}% "
            f"{row['fee_displacement_ratio']:>9.3f}"
        )

    # --- Saturation Curve Fit ---
    print("\n📈 Fitting saturation curve...")
    t_forecast, y_forecast, params = fit_saturation_curve(df)
    print(f"  Capacity (asymptote):  {params['capacity']:.1%}")
    print(f"  Growth rate:           {params['rate']:.3f}")
    print(f"  Midpoint (months):     {params['midpoint']:.1f}")

    # --- Institutional Threshold Analysis ---
    print("\n⚠️  Institutional Threshold Analysis:")
    thresholds = [0.10, 0.25, 0.50, 0.75]
    for thresh in thresholds:
        if params["capacity"] >= thresh:
            # Solve for time when saturation curve crosses threshold
            # expit(rate * (t - midpoint)) = thresh / capacity
            from scipy.special import logit
            target = thresh / params["capacity"]
            if 0 < target < 1:
                t_cross = params["midpoint"] + logit(target) / params["rate"]
                months_from_start = max(0, t_cross)
                print(f"  {thresh:>5.0%} pollution reached at ~month {months_from_start:.0f} "
                      f"from baseline")
            else:
                print(f"  {thresh:>5.0%} pollution: already exceeded or unreachable")
        else:
            print(f"  {thresh:>5.0%} pollution: above saturation capacity ({params['capacity']:.0%})")

    # --- Save Plot ---
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "content_pollution.png"

    print(f"\n💾 Saving visualization...")
    plot_pollution_analysis(df, t_forecast, y_forecast, params, str(output_path))

    # --- Save CSV ---
    csv_path = output_dir / "content_pollution_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"  📄 Data saved to {csv_path}")

    print(f"\n{'=' * 72}")
    print("  ✅ Content pollution analysis complete.")
    print(f"{'=' * 72}")
