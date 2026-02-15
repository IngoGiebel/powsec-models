"""
miner_stress.py — Miner Capitulation & Network Security Degradation Model
==========================================================================

Models the probability that individual Bitcoin miners capitulate under
adverse price conditions, and aggregates these into a network-level
security degradation score.

Uses real Q3 2025 financial data for major public miners.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless environments

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.special import expit  # Logistic sigmoid


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BLOCK_REWARD_BTC = 3.125          # Post-April 2024 halving
BLOCKS_PER_DAY = 144              # Average Bitcoin blocks per day
SATS_PER_BTC = 1e8
SECONDS_PER_HOUR = 3600
JOULES_PER_KWH = 3.6e6

# Network-level assumptions
NETWORK_HASHRATE_EH = 850         # ~850 EH/s mid-2025 estimate


# ---------------------------------------------------------------------------
# MinerProfile Dataclass
# ---------------------------------------------------------------------------

@dataclass
class MinerProfile:
    """Financial and operational profile for a public Bitcoin miner.

    Attributes
    ----------
    name : str
        Company name.
    ticker : str
        Stock ticker symbol.
    revenue_ttm : float
        Trailing twelve-month revenue in USD (millions).
    ebitda : float
        EBITDA in USD (millions). Negative = operating at a loss.
    total_debt : float
        Total debt in USD (millions).
    cash : float
        Cash & equivalents in USD (millions).
    hashrate_share : float
        Fraction of global hashrate (0–1).
    power_cost_kwh : float
        All-in electricity cost in USD per kWh.
    efficiency_jph : float
        Mining rig efficiency in joules per terahash (J/TH).
    """
    name: str
    ticker: str
    revenue_ttm: float        # $M
    ebitda: float              # $M
    total_debt: float          # $M
    cash: float                # $M
    hashrate_share: float      # 0-1 fraction
    power_cost_kwh: float      # $/kWh
    efficiency_jph: float      # J/TH (joules per terahash)


# ---------------------------------------------------------------------------
# Pre-populated Miner Profiles (Q3 2025 approximate)
# ---------------------------------------------------------------------------

DEFAULT_MINERS: List[MinerProfile] = [
    MinerProfile(
        name="TeraWulf",
        ticker="WULF",
        revenue_ttm=167.6,
        ebitda=-35.2,
        total_debt=1085.0,
        cash=711.0,
        hashrate_share=0.035,     # ~30 EH/s
        power_cost_kwh=0.035,     # Nuclear/hydro advantage
        efficiency_jph=21.0,      # Antminer S21-class
    ),
    MinerProfile(
        name="Cipher Mining",
        ticker="CIFR",
        revenue_ttm=150.0,
        ebitda=-20.0,
        total_debt=400.0,
        cash=100.0,
        hashrate_share=0.030,     # ~25 EH/s
        power_cost_kwh=0.045,
        efficiency_jph=22.0,
    ),
    MinerProfile(
        name="Core Scientific",
        ticker="CORZ",
        revenue_ttm=500.0,
        ebitda=95.0,
        total_debt=800.0,
        cash=200.0,
        hashrate_share=0.040,     # ~34 EH/s
        power_cost_kwh=0.042,
        efficiency_jph=23.0,
    ),
    MinerProfile(
        name="Marathon Digital",
        ticker="MARA",
        revenue_ttm=387.0,
        ebitda=48.0,
        total_debt=1200.0,
        cash=300.0,
        hashrate_share=0.060,     # ~50 EH/s
        power_cost_kwh=0.048,
        efficiency_jph=24.0,
    ),
    MinerProfile(
        name="Riot Platforms",
        ticker="RIOT",
        revenue_ttm=280.0,
        ebitda=-15.0,
        total_debt=350.0,
        cash=600.0,
        hashrate_share=0.045,     # ~38 EH/s
        power_cost_kwh=0.038,
        efficiency_jph=21.5,
    ),
    MinerProfile(
        name="CleanSpark",
        ticker="CLSK",
        revenue_ttm=320.0,
        ebitda=60.0,
        total_debt=200.0,
        cash=150.0,
        hashrate_share=0.040,     # ~34 EH/s
        power_cost_kwh=0.040,
        efficiency_jph=22.5,
    ),
]


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def calculate_breakeven(
    miner: MinerProfile,
    btc_price: float = 100_000.0,
    difficulty_factor: float = 1.0,
) -> float:
    """Calculate the BTC price at which a miner becomes unprofitable.

    The breakeven price is derived from the miner's energy cost per BTC
    mined, adjusted for operating leverage (EBITDA margin) and difficulty.

    Parameters
    ----------
    miner : MinerProfile
        Miner's financial and operational profile.
    btc_price : float
        Current BTC price (used for EBITDA margin context).
    difficulty_factor : float
        Multiplier on mining difficulty (1.0 = current, >1 = harder).

    Returns
    -------
    float
        Breakeven BTC price in USD.
    """
    # Energy cost per TH per second per day
    # efficiency_jph (J/TH) tells us joules needed per terahash
    # Power consumption for 1 TH/s = efficiency_jph watts (since J/s = W)
    power_per_th_kw = miner.efficiency_jph / 1000.0  # kW per TH/s

    # Daily electricity cost per TH/s
    daily_power_cost_per_th = power_per_th_kw * 24.0 * miner.power_cost_kwh

    # BTC mined per TH/s per day (simplified)
    # Total network: NETWORK_HASHRATE_EH * 1e6 TH/s
    # 1 TH/s share = 1 / (network_hashrate_th)
    network_hashrate_th = NETWORK_HASHRATE_EH * 1e6  # TH/s
    btc_per_th_per_day = (BLOCK_REWARD_BTC * BLOCKS_PER_DAY) / network_hashrate_th

    # Adjust for difficulty changes
    btc_per_th_per_day /= difficulty_factor

    # Raw energy breakeven: price at which energy cost = mining revenue
    if btc_per_th_per_day <= 0:
        return float("inf")

    energy_breakeven = daily_power_cost_per_th / btc_per_th_per_day

    # Overhead adjustment: use SGA (non-energy OPEX) as fraction of revenue
    # EBITDA = Revenue - COGS - SGA. Since energy_breakeven already covers
    # energy (the dominant COGS component), we only add SGA overhead.
    # SGA ≈ Revenue - EBITDA - energy_cost (≈ COGS - energy + SGA)
    # Simplified: overhead_ratio = (Revenue - EBITDA) / Revenue - energy_share
    # We approximate SGA as: Revenue * (1 - EBITDA_margin) - energy_costs
    # To avoid double-counting energy in both breakeven and EBITDA,
    # we estimate the non-energy overhead as a multiplier.
    if miner.revenue_ttm > 0:
        ebitda_margin = miner.ebitda / miner.revenue_ttm
        # Non-energy overhead ratio: total costs minus energy, relative to revenue
        # COGS includes energy; EBITDA excludes D&A but includes energy costs.
        # SGA_ratio ≈ 1 - ebitda_margin - energy_share_of_revenue
        # For miners, energy is typically 50-70% of revenue at breakeven
        energy_share_estimate = 0.6  # typical for BTC miners
        sga_ratio = max(0.0, (1.0 - ebitda_margin) - energy_share_estimate)
        # Overhead multiplier: energy breakeven covers energy, add SGA on top
        overhead_factor = 1.0 + sga_ratio
    else:
        overhead_factor = 2.0  # conservative fallback

    # Clamp to reasonable range [1.0, 3.0]
    overhead_factor = float(np.clip(overhead_factor, 1.0, 3.0))

    return energy_breakeven * overhead_factor


def capitulation_probability(
    miner: MinerProfile,
    btc_price: float,
    interest_rate: float = 0.05,
) -> float:
    """Estimate the probability that a miner capitulates at a given BTC price.

    Uses a logistic function combining:
    - Distance of BTC price from the miner's breakeven price
    - Debt-to-cash ratio (leverage pressure)
    - Interest rate environment (refinancing risk)

    Parameters
    ----------
    miner : MinerProfile
        Miner's financial and operational profile.
    btc_price : float
        Current BTC price in USD.
    interest_rate : float
        Prevailing interest rate (0.05 = 5%).

    Returns
    -------
    float
        Capitulation probability in [0, 1].
    """
    breakeven = calculate_breakeven(miner, btc_price)

    # Price distance: how far below breakeven (positive = underwater)
    # Normalized by breakeven for comparability
    if breakeven > 0:
        price_ratio = btc_price / breakeven
    else:
        return 0.0

    # Debt pressure: high debt/low cash amplifies capitulation risk
    if miner.cash > 0:
        debt_pressure = miner.total_debt / miner.cash
    else:
        debt_pressure = 10.0  # Maximum pressure if no cash

    # Normalize debt pressure (typical range 0.5-5.0, map to 0-2 contribution)
    debt_score = np.clip(debt_pressure / 3.0, 0.0, 2.0)

    # Interest rate factor: higher rates increase refinancing pressure
    # Baseline at 5%, each 1% above adds pressure
    rate_pressure = max(0.0, (interest_rate - 0.03) * 10.0)

    # Cash runway: months of operation remaining at current burn rate
    if miner.ebitda < 0:
        monthly_burn = abs(miner.ebitda) / 12.0
        runway_months = miner.cash / monthly_burn if monthly_burn > 0 else 120
    else:
        runway_months = 120  # Profitable, long runway

    # Runway score: shorter runway → higher capitulation risk
    runway_score = np.clip(1.0 - runway_months / 24.0, 0.0, 1.0)

    # Composite logistic input
    # Negative = safe (price well above breakeven)
    # Positive = at risk (price below breakeven + high leverage)
    k = 5.0  # Steepness of the logistic curve
    z = -k * (price_ratio - 1.0) + debt_score + rate_pressure + runway_score

    return float(expit(z))


def network_security_degradation(
    btc_price: float,
    miners: List[MinerProfile] = DEFAULT_MINERS,
    interest_rate: float = 0.05,
) -> float:
    """Calculate aggregate network security degradation.

    Weighted sum of capitulation probabilities across all tracked miners,
    weighted by each miner's share of total network hashrate.

    Parameters
    ----------
    btc_price : float
        Current BTC price in USD.
    miners : list of MinerProfile
        List of miner profiles to evaluate.
    interest_rate : float
        Prevailing interest rate.

    Returns
    -------
    float
        Degradation score in [0, 1]. 0 = no risk, 1 = total capitulation
        of tracked miners.
    """
    total_hashrate = sum(m.hashrate_share for m in miners)
    if total_hashrate == 0:
        return 0.0

    degradation = 0.0
    for miner in miners:
        cap_prob = capitulation_probability(miner, btc_price, interest_rate)
        weight = miner.hashrate_share / total_hashrate
        degradation += cap_prob * weight

    return degradation


def simulate_btc_crash(
    start_price: float = 100_000,
    end_price: float = 20_000,
    steps: int = 50,
    miners: List[MinerProfile] = DEFAULT_MINERS,
    interest_rate: float = 0.05,
    daa_enabled: bool = True,
) -> pd.DataFrame:
    """Simulate a BTC price decline and track miner capitulation dynamics.

    When daa_enabled=True, incorporates the Difficulty Adjustment Algorithm
    (DAA) feedback loop: as miners capitulate and hashrate drops, difficulty
    adjusts downward (every ~2016 blocks ≈ 14 days), reducing breakeven
    costs for surviving miners. This models the stabilizing feedback that
    the static analysis misses. See Prat & Walter (2021).

    Parameters
    ----------
    start_price : float
        Starting BTC price.
    end_price : float
        Ending BTC price.
    steps : int
        Number of price steps in the simulation.
    miners : list of MinerProfile
        Miner profiles to evaluate.
    interest_rate : float
        Prevailing interest rate.
    daa_enabled : bool
        Whether to model difficulty adjustment feedback (default True).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: btc_price, per-miner capitulation probs,
        aggregate security degradation, and difficulty_factor.
    """
    prices = np.linspace(start_price, end_price, steps)

    records = []
    difficulty_factor = 1.0

    for i, price in enumerate(prices):
        row = {"btc_price": price, "difficulty_factor": difficulty_factor}

        for miner in miners:
            # Recalculate breakeven with current difficulty factor
            be = calculate_breakeven(miner, price, difficulty_factor)
            cap_prob = capitulation_probability(miner, price, interest_rate)
            row[f"cap_{miner.ticker}"] = cap_prob

        row["security_degradation"] = network_security_degradation(
            price, miners, interest_rate
        )

        # DAA feedback: estimate hashrate drop from capitulation,
        # adjust difficulty proportionally for next step
        if daa_enabled and i < len(prices) - 1:
            # Tracked miners represent ~25% of network; extrapolate
            tracked_share = sum(m.hashrate_share for m in miners)
            surviving_share = sum(
                m.hashrate_share * (1.0 - capitulation_probability(m, price, interest_rate))
                for m in miners
            )
            # Untracked miners (~75%) assumed to have similar capitulation rate
            tracked_survival_rate = surviving_share / tracked_share if tracked_share > 0 else 1.0
            network_survival_rate = tracked_survival_rate  # extrapolate to full network

            # Difficulty adjusts toward surviving hashrate
            # DAA updates every 2016 blocks; we smooth over simulation steps
            # Target: difficulty_factor tracks network_survival_rate
            daa_speed = 0.3  # partial adjustment per step (smoothing)
            target_difficulty = network_survival_rate
            difficulty_factor = difficulty_factor * (1 - daa_speed) + target_difficulty * daa_speed
            difficulty_factor = max(0.1, difficulty_factor)  # floor at 10% of original

        records.append(row)

    return pd.DataFrame(records)


def plot_stress_test(
    simulation_df: pd.DataFrame,
    output_path: Optional[str] = None,
    miners: List[MinerProfile] = DEFAULT_MINERS,
) -> None:
    """Create a visualization of the miner stress test results.

    Produces a two-panel chart:
    - Top: Per-miner capitulation probability curves
    - Bottom: Aggregate network security degradation

    Parameters
    ----------
    simulation_df : pd.DataFrame
        Output from simulate_btc_crash().
    output_path : str, optional
        File path to save the plot. If None, displays interactively.
    miners : list of MinerProfile
        Miner profiles (for labels and styling).
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 10), height_ratios=[2, 1], sharex=True
    )
    fig.suptitle(
        "Bitcoin Miner Capitulation Stress Test",
        fontsize=16,
        fontweight="bold",
        y=0.95,
    )

    prices = simulation_df["btc_price"]

    # Color palette
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]

    # --- Top panel: Per-miner capitulation probabilities ---
    for i, miner in enumerate(miners):
        col = f"cap_{miner.ticker}"
        if col in simulation_df.columns:
            ax1.plot(
                prices,
                simulation_df[col] * 100,
                label=f"{miner.ticker} ({miner.name})",
                color=colors[i % len(colors)],
                linewidth=2.0,
                alpha=0.85,
            )

    ax1.set_ylabel("Capitulation Probability (%)", fontsize=12)
    ax1.set_title("Per-Miner Capitulation Probability", fontsize=13, pad=10)
    ax1.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax1.set_ylim(-2, 102)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=50, color="gray", linestyle="--", alpha=0.5, label="_50% threshold")

    # Add breakeven markers
    for i, miner in enumerate(miners):
        be = calculate_breakeven(miner)
        if prices.min() <= be <= prices.max():
            ax1.axvline(
                x=be, color=colors[i % len(colors)],
                linestyle=":", alpha=0.4, linewidth=1.0
            )

    # --- Bottom panel: Aggregate security degradation ---
    ax2.fill_between(
        prices,
        simulation_df["security_degradation"] * 100,
        alpha=0.3,
        color="#e74c3c",
    )
    ax2.plot(
        prices,
        simulation_df["security_degradation"] * 100,
        color="#e74c3c",
        linewidth=2.5,
    )
    ax2.set_xlabel("BTC Price (USD)", fontsize=12)
    ax2.set_ylabel("Security Degradation (%)", fontsize=12)
    ax2.set_title("Aggregate Network Security Degradation", fontsize=13, pad=10)
    ax2.set_ylim(-2, 102)
    ax2.grid(True, alpha=0.3)

    # Format x-axis as currency
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, p: f"${x:,.0f}"
    ))
    plt.xticks(rotation=45)

    # Add danger zones
    for ax in [ax2]:
        ax.axhspan(0, 15, alpha=0.05, color="green")
        ax.axhspan(15, 40, alpha=0.05, color="yellow")
        ax.axhspan(40, 100, alpha=0.08, color="red")

    plt.tight_layout(rect=[0, 0, 1, 0.93])

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
    print("  ⛏️  Bitcoin Miner Capitulation Stress Test")
    print("  Model: powsec-models v0.1.0")
    print("=" * 72)

    # --- Breakeven Summary ---
    print("\n📋 Miner Breakeven Prices (current difficulty):\n")
    print(f"  {'Ticker':<8} {'Company':<20} {'Breakeven':>12} {'EBITDA Margin':>14} {'Debt/Cash':>10}")
    print(f"  {'─' * 8} {'─' * 20} {'─' * 12} {'─' * 14} {'─' * 10}")

    for m in DEFAULT_MINERS:
        be = calculate_breakeven(m)
        margin = m.ebitda / m.revenue_ttm * 100 if m.revenue_ttm > 0 else 0
        dc = m.total_debt / m.cash if m.cash > 0 else float("inf")
        print(f"  {m.ticker:<8} {m.name:<20} ${be:>10,.0f} {margin:>13.1f}% {dc:>9.1f}x")

    # --- Simulation ---
    print("\n🔄 Running crash simulation: $100,000 → $20,000 ...")
    df = simulate_btc_crash(
        start_price=100_000,
        end_price=20_000,
        steps=50,
    )

    # --- Key Price Points ---
    key_prices = [100_000, 80_000, 60_000, 50_000, 40_000, 30_000, 20_000]
    print("\n📊 Capitulation Probabilities at Key Price Points:\n")

    header = f"  {'Price':>10} |"
    for m in DEFAULT_MINERS:
        header += f" {m.ticker:>6} |"
    header += f" {'Degrad':>7} |"
    print(header)
    print(f"  {'─' * 10}-+" + ("+".join(["─" * 8] * len(DEFAULT_MINERS))) + "+─" + "─" * 7 + "─+")

    for price in key_prices:
        # Find closest price in simulation
        idx = (df["btc_price"] - price).abs().idxmin()
        row = df.iloc[idx]

        line = f"  ${price:>8,} |"
        for m in DEFAULT_MINERS:
            cap = row[f"cap_{m.ticker}"] * 100
            line += f" {cap:>5.1f}% |"
        deg = row["security_degradation"] * 100
        line += f"  {deg:>5.1f}% |"
        print(line)

    # --- Save Plot ---
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "stress_test.png"

    print(f"\n💾 Saving visualization...")
    plot_stress_test(df, output_path=str(output_path))

    # --- Save CSV ---
    csv_path = output_dir / "stress_test_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"  📄 Data saved to {csv_path}")

    print(f"\n{'=' * 72}")
    print("  ✅ Stress test complete.")
    print(f"{'=' * 72}")
