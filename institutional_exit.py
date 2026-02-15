"""
institutional_exit.py — ETF/Institutional Compliance Model
===========================================================

Models when and how institutional investors (ETFs, funds) might be
forced to exit Bitcoin positions due to compliance triggers related
to blockchain content pollution, regulatory changes, or ESG concerns.

Projects the timeline to compliance-trigger events and estimates
the resulting BTC price impact.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import expit


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BTC_TOTAL_SUPPLY = 21_000_000
BTC_CIRCULATING = 19_700_000      # Mid-2025 approximate
BTC_DAILY_VOLUME_USD = 30e9       # Average daily spot volume
BTC_MARKET_CAP_USD = 2.0e12      # At ~$100k


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class InstitutionalHolder:
    """Profile of an institutional BTC holder.

    Attributes
    ----------
    name : str
        Fund or entity name.
    ticker : str
        ETF ticker or identifier.
    btc_holdings : float
        BTC held (in BTC, not USD).
    aum_usd : float
        Total assets under management in USD (billions).
    compliance_strictness : float
        How strict the compliance framework is (0=lax, 1=very strict).
    pollution_threshold : float
        Maximum acceptable pollution rate before compliance trigger (0–1).
    regulatory_jurisdiction : str
        Primary regulatory jurisdiction.
    exit_speed_days : int
        Estimated days to fully liquidate position.
    """
    name: str
    ticker: str
    btc_holdings: float
    aum_usd: float
    compliance_strictness: float
    pollution_threshold: float
    regulatory_jurisdiction: str
    exit_speed_days: int


@dataclass
class ComplianceTrigger:
    """Result of compliance trigger analysis for a single holder.

    Attributes
    ----------
    holder_name : str
        Name of the institutional holder.
    ticker : str
        ETF ticker.
    months_to_trigger : float
        Estimated months until compliance trigger fires.
    trigger_probability : float
        Probability the trigger fires within 24 months (0–1).
    btc_at_risk : float
        BTC amount that would be sold.
    usd_at_risk : float
        USD value at risk (at current price).
    price_impact_pct : float
        Estimated BTC price impact from liquidation (%).
    """
    holder_name: str
    ticker: str
    months_to_trigger: float
    trigger_probability: float
    btc_at_risk: float
    usd_at_risk: float
    price_impact_pct: float


# ---------------------------------------------------------------------------
# Default Data (mid-2025 estimates)
# ---------------------------------------------------------------------------

DEFAULT_HOLDERS: List[InstitutionalHolder] = [
    InstitutionalHolder(
        "BlackRock iShares Bitcoin Trust", "IBIT",
        570_000, 50.0, 0.7, 0.15, "US", 90,
    ),
    InstitutionalHolder(
        "Fidelity Wise Origin", "FBTC",
        205_000, 18.0, 0.8, 0.12, "US", 60,
    ),
    InstitutionalHolder(
        "Grayscale Bitcoin Trust", "GBTC",
        195_000, 17.0, 0.5, 0.20, "US", 45,
    ),
    InstitutionalHolder(
        "ARK 21Shares Bitcoin ETF", "ARKB",
        48_000, 4.5, 0.6, 0.18, "US", 30,
    ),
    InstitutionalHolder(
        "Bitwise Bitcoin ETF", "BITB",
        42_000, 3.8, 0.6, 0.18, "US", 30,
    ),
    InstitutionalHolder(
        "VanEck Bitcoin ETF", "HODL",
        12_000, 1.1, 0.7, 0.15, "US", 20,
    ),
    InstitutionalHolder(
        "Invesco Galaxy Bitcoin ETF", "BTCO",
        8_500, 0.8, 0.7, 0.15, "US", 15,
    ),
    InstitutionalHolder(
        "Purpose Bitcoin ETF", "BTCC",
        35_000, 2.0, 0.8, 0.10, "CA", 30,
    ),
    InstitutionalHolder(
        "ETC Group Physical Bitcoin", "BTCE",
        20_000, 1.5, 0.9, 0.08, "DE", 45,
    ),
    InstitutionalHolder(
        "21Shares Bitcoin ETP", "ABTC",
        15_000, 1.0, 0.85, 0.10, "CH", 30,
    ),
]


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def estimate_pollution_trajectory(
    current_rate: float = 0.03,
    growth_rate: float = 0.15,
    months: int = 48,
    capacity: float = 0.60,
) -> np.ndarray:
    """Project blockchain pollution rate over time using logistic growth.

    Parameters
    ----------
    current_rate : float
        Current estimated pollution rate (fraction of blocks, 0–1).
    growth_rate : float
        Monthly growth rate parameter.
    months : int
        Number of months to project.
    capacity : float
        Maximum pollution capacity (asymptote).

    Returns
    -------
    np.ndarray
        Array of pollution rates for each month.
    """
    t = np.arange(months, dtype=float)

    # Find the offset that matches current_rate at t=0
    # logistic: capacity * sigmoid(growth_rate * (t - midpoint))
    # At t=0: current_rate = capacity * sigmoid(-growth_rate * midpoint)
    # Solve for midpoint
    from scipy.special import logit
    if 0 < current_rate / capacity < 1:
        midpoint = -logit(current_rate / capacity) / growth_rate
    else:
        midpoint = 12.0

    return capacity * expit(growth_rate * (t - midpoint))


def time_to_trigger(
    holder: InstitutionalHolder,
    pollution_trajectory: np.ndarray,
) -> float:
    """Estimate months until a holder's compliance trigger fires.

    Parameters
    ----------
    holder : InstitutionalHolder
        Institutional holder profile.
    pollution_trajectory : np.ndarray
        Monthly pollution rate projections.

    Returns
    -------
    float
        Months until trigger. Returns float('inf') if never triggered.
    """
    for month, rate in enumerate(pollution_trajectory):
        # Effective threshold adjusted by compliance strictness
        # Stricter compliance → trigger fires at lower rates
        effective_threshold = holder.pollution_threshold * (
            1.0 - 0.3 * holder.compliance_strictness
        )
        if rate >= effective_threshold:
            return float(month)

    return float("inf")


def trigger_probability_24m(
    holder: InstitutionalHolder,
    pollution_trajectory: np.ndarray,
) -> float:
    """Estimate probability of compliance trigger within 24 months.

    Combines pollution trajectory with regulatory uncertainty.

    Parameters
    ----------
    holder : InstitutionalHolder
        Institutional holder profile.
    pollution_trajectory : np.ndarray
        Monthly pollution rate projections.

    Returns
    -------
    float
        Probability in [0, 1].
    """
    months = time_to_trigger(holder, pollution_trajectory)

    if months <= 24:
        # Base probability from trajectory
        base_prob = expit(3.0 * (1.0 - months / 24.0))
    else:
        base_prob = 0.05  # Small residual risk

    # Regulatory jurisdiction modifier
    jurisdiction_risk = {
        "US": 0.6,
        "CA": 0.5,
        "DE": 0.8,  # EU is stricter
        "CH": 0.7,
    }
    reg_mod = jurisdiction_risk.get(holder.regulatory_jurisdiction, 0.5)

    # Compliance strictness amplifies probability
    adjusted = base_prob * (0.5 + 0.5 * holder.compliance_strictness) * (0.5 + 0.5 * reg_mod)

    return float(np.clip(adjusted, 0.0, 0.99))


def estimate_price_impact(
    btc_to_sell: float,
    exit_days: int,
    btc_price: float = 100_000,
) -> float:
    """Estimate the BTC price impact from institutional liquidation.

    Implements a simplified Almgren-Chriss (2001) optimal execution model,
    separating temporary impact (decays intraday) from permanent impact
    (structural supply overhang that shifts the equilibrium price).

    Parameters
    ----------
    btc_to_sell : float
        Amount of BTC to liquidate.
    exit_days : int
        Number of days over which the liquidation occurs.
    btc_price : float
        Current BTC price.

    Returns
    -------
    float
        Estimated percentage price decline.

    References
    ----------
    Almgren, R. & Chriss, N. (2001). Optimal execution of portfolio
    transactions. Journal of Risk, 3(2), 5–39.
    """
    exit_days = max(exit_days, 1)
    daily_btc_volume = BTC_DAILY_VOLUME_USD / btc_price
    daily_sell_amount = btc_to_sell / exit_days

    # Participation rate: fraction of daily volume per day
    participation = daily_sell_amount / daily_btc_volume

    # --- Temporary impact (per-day, decays) ---
    # Scales with sqrt of participation rate (Kyle's lambda model)
    # eta calibrated: 10 bps temporary impact at 1% participation
    eta = 0.10  # temporary impact coefficient
    daily_temporary_impact = eta * np.sqrt(participation)

    # --- Permanent impact (cumulative, structural) ---
    # Each day's trading permanently shifts the price by gamma * participation
    # gamma calibrated: 5 bps permanent impact at 1% participation
    gamma = 0.05  # permanent impact coefficient
    daily_permanent_impact = gamma * participation

    # Total permanent impact accumulates over all trading days
    cumulative_permanent_pct = daily_permanent_impact * exit_days * 100

    # Temporary impact: only the peak matters for total price decline
    # (it decays, but the worst intraday dip scales with max daily trade)
    peak_temporary_pct = daily_temporary_impact * 100

    # Total impact: permanent (structural) + peak temporary
    # Note: faster execution → higher daily participation → higher temporary
    # but fewer days → less cumulative permanent. This creates a real tradeoff.
    total_impact_pct = cumulative_permanent_pct + peak_temporary_pct

    # Cap at reasonable maximum
    return float(min(total_impact_pct, 60.0))


def analyze_institutional_risk(
    holders: List[InstitutionalHolder] = DEFAULT_HOLDERS,
    pollution_current: float = 0.03,
    pollution_growth: float = 0.15,
    btc_price: float = 100_000,
) -> pd.DataFrame:
    """Run full institutional exit risk analysis.

    Parameters
    ----------
    holders : list of InstitutionalHolder
        Institutional holder profiles.
    pollution_current : float
        Current pollution rate.
    pollution_growth : float
        Monthly pollution growth rate.
    btc_price : float
        Current BTC price.

    Returns
    -------
    pd.DataFrame
        Analysis results per holder.
    """
    trajectory = estimate_pollution_trajectory(
        current_rate=pollution_current,
        growth_rate=pollution_growth,
    )

    results = []
    for holder in holders:
        months = time_to_trigger(holder, trajectory)
        prob = trigger_probability_24m(holder, trajectory)
        impact = estimate_price_impact(
            holder.btc_holdings, holder.exit_speed_days, btc_price
        )
        usd_val = holder.btc_holdings * btc_price

        results.append({
            "holder": holder.name,
            "ticker": holder.ticker,
            "btc_holdings": holder.btc_holdings,
            "usd_at_risk": usd_val,
            "compliance_strictness": holder.compliance_strictness,
            "pollution_threshold": holder.pollution_threshold,
            "months_to_trigger": months if months != float("inf") else 999,
            "trigger_prob_24m": prob,
            "price_impact_pct": impact,
            "jurisdiction": holder.regulatory_jurisdiction,
        })

    return pd.DataFrame(results)


def simulate_cascade(
    holders: List[InstitutionalHolder] = DEFAULT_HOLDERS,
    pollution_current: float = 0.03,
    pollution_growth: float = 0.15,
    btc_price: float = 100_000,
    months: int = 36,
) -> pd.DataFrame:
    """Simulate a cascade of institutional exits over time.

    Parameters
    ----------
    holders : list of InstitutionalHolder
        Institutional holder profiles.
    pollution_current : float
        Starting pollution rate.
    pollution_growth : float
        Monthly pollution growth rate.
    btc_price : float
        Starting BTC price.
    months : int
        Simulation duration in months.

    Returns
    -------
    pd.DataFrame
        Monthly cascade simulation with price trajectory.
    """
    trajectory = estimate_pollution_trajectory(
        current_rate=pollution_current,
        growth_rate=pollution_growth,
        months=months,
    )

    price = btc_price
    exited = set()
    records = []

    total_institutional_btc = sum(h.btc_holdings for h in holders)

    for month in range(months):
        month_exits = []
        month_btc_sold = 0.0

        for holder in holders:
            if holder.ticker in exited:
                continue

            effective_threshold = holder.pollution_threshold * (
                1.0 - 0.3 * holder.compliance_strictness
            )
            if trajectory[month] >= effective_threshold:
                exited.add(holder.ticker)
                month_exits.append(holder.ticker)
                month_btc_sold += holder.btc_holdings

        # Price impact from this month's exits
        if month_btc_sold > 0:
            impact = estimate_price_impact(month_btc_sold, 30, price)
            price *= (1.0 - impact / 100.0)

        remaining_btc = sum(
            h.btc_holdings for h in holders if h.ticker not in exited
        )

        records.append({
            "month": month,
            "pollution_rate": trajectory[month],
            "btc_price": price,
            "exits_this_month": ", ".join(month_exits) if month_exits else "",
            "btc_sold_this_month": month_btc_sold,
            "remaining_institutional_btc": remaining_btc,
            "institutional_pct_remaining": remaining_btc / total_institutional_btc * 100,
        })

    return pd.DataFrame(records)


def plot_institutional_analysis(
    risk_df: pd.DataFrame,
    cascade_df: pd.DataFrame,
    output_path: Optional[str] = None,
) -> None:
    """Create a multi-panel visualization of institutional exit risk.

    Parameters
    ----------
    risk_df : pd.DataFrame
        Per-holder risk analysis.
    cascade_df : pd.DataFrame
        Cascade simulation results.
    output_path : str, optional
        File path to save the plot.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        "Institutional BTC Exit Risk — Compliance Trigger Analysis",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    # --- Panel 1: BTC at Risk by Holder ---
    ax1 = axes[0, 0]
    sorted_risk = risk_df.sort_values("btc_holdings", ascending=True)
    colors = [plt.cm.RdYlGn_r(p) for p in sorted_risk["trigger_prob_24m"]]
    ax1.barh(
        sorted_risk["ticker"],
        sorted_risk["btc_holdings"] / 1000,
        color=colors,
        alpha=0.8,
    )
    ax1.set_xlabel("BTC Holdings (thousands)")
    ax1.set_title("BTC at Risk by Holder (color=trigger probability)")
    ax1.grid(True, alpha=0.3, axis="x")

    # --- Panel 2: Trigger Timeline ---
    ax2 = axes[0, 1]
    finite = risk_df[risk_df["months_to_trigger"] < 999].copy()
    if not finite.empty:
        finite_sorted = finite.sort_values("months_to_trigger")
        ax2.barh(
            finite_sorted["ticker"],
            finite_sorted["months_to_trigger"],
            color="#e74c3c",
            alpha=0.7,
        )
        ax2.set_xlabel("Months to Compliance Trigger")
        ax2.set_title("Time to Trigger (by Holder)")
        ax2.grid(True, alpha=0.3, axis="x")
    else:
        ax2.text(0.5, 0.5, "No triggers within projection",
                 ha="center", va="center", transform=ax2.transAxes)
        ax2.set_title("Time to Trigger (by Holder)")

    # --- Panel 3: Cascade — Price + Pollution ---
    ax3 = axes[1, 0]
    ax3.plot(
        cascade_df["month"],
        cascade_df["btc_price"] / 1000,
        color="#3498db",
        linewidth=2,
        label="BTC Price ($k)",
    )
    ax3.set_xlabel("Month")
    ax3.set_ylabel("BTC Price ($k)", color="#3498db")
    ax3.tick_params(axis="y", labelcolor="#3498db")

    ax3_twin = ax3.twinx()
    ax3_twin.plot(
        cascade_df["month"],
        cascade_df["pollution_rate"] * 100,
        color="#e74c3c",
        linewidth=2,
        linestyle="--",
        label="Pollution Rate (%)",
    )
    ax3_twin.set_ylabel("Pollution Rate (%)", color="#e74c3c")
    ax3_twin.tick_params(axis="y", labelcolor="#e74c3c")
    ax3.set_title("BTC Price vs Pollution Rate (Cascade)")
    ax3.grid(True, alpha=0.3)

    # --- Panel 4: Institutional Holdings Remaining ---
    ax4 = axes[1, 1]
    ax4.fill_between(
        cascade_df["month"],
        cascade_df["institutional_pct_remaining"],
        alpha=0.3,
        color="#2ecc71",
    )
    ax4.plot(
        cascade_df["month"],
        cascade_df["institutional_pct_remaining"],
        color="#2ecc71",
        linewidth=2,
    )
    ax4.set_xlabel("Month")
    ax4.set_ylabel("Institutional Holdings Remaining (%)")
    ax4.set_title("Institutional Exit Cascade")
    ax4.set_ylim(0, 105)
    ax4.grid(True, alpha=0.3)

    # Mark exit events
    exits = cascade_df[cascade_df["exits_this_month"] != ""]
    for _, row in exits.iterrows():
        ax4.axvline(x=row["month"], color="red", linestyle=":", alpha=0.4)
        ax4.annotate(
            row["exits_this_month"],
            xy=(row["month"], row["institutional_pct_remaining"]),
            fontsize=6,
            rotation=90,
            va="bottom",
        )

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
    print("  🏦 Institutional BTC Exit Risk — Compliance Trigger Analysis")
    print("  Model: powsec-models v0.1.0")
    print("=" * 72)

    # --- Holder Summary ---
    print("\n📋 Institutional BTC Holdings:\n")
    total_btc = sum(h.btc_holdings for h in DEFAULT_HOLDERS)
    total_usd = total_btc * 100_000

    print(f"  {'Ticker':<8} {'Name':<35} {'BTC':>10} {'USD ($B)':>10} "
          f"{'Strict':>7} {'Thresh':>7} {'Jur':>4}")
    print(f"  {'─' * 8} {'─' * 35} {'─' * 10} {'─' * 10} "
          f"{'─' * 7} {'─' * 7} {'─' * 4}")

    for h in DEFAULT_HOLDERS:
        usd_b = h.btc_holdings * 100_000 / 1e9
        print(f"  {h.ticker:<8} {h.name:<35} {h.btc_holdings:>10,.0f} "
              f"${usd_b:>8.1f}B {h.compliance_strictness:>6.1f} "
              f"{h.pollution_threshold:>6.0%} {h.regulatory_jurisdiction:>4}")

    print(f"\n  Total: {total_btc:,.0f} BTC (${total_usd / 1e9:.1f}B) "
          f"= {total_btc / BTC_CIRCULATING:.1%} of circulating supply")

    # --- Risk Analysis ---
    print("\n🔍 Running compliance trigger analysis...")
    risk_df = analyze_institutional_risk()

    print(f"\n  {'Ticker':<8} {'Months→Trigger':>15} {'Prob 24m':>10} "
          f"{'Price Impact':>13} {'BTC at Risk':>12}")
    print(f"  {'─' * 8} {'─' * 15} {'─' * 10} {'─' * 13} {'─' * 12}")

    for _, row in risk_df.iterrows():
        months_str = (f"{row['months_to_trigger']:.0f}"
                      if row["months_to_trigger"] < 999 else "∞")
        print(f"  {row['ticker']:<8} {months_str:>15} "
              f"{row['trigger_prob_24m']:>9.1%} "
              f"{row['price_impact_pct']:>12.1f}% "
              f"{row['btc_holdings']:>11,.0f}")

    # --- Cascade Simulation ---
    print("\n🌊 Running cascade simulation (36 months)...")
    cascade_df = simulate_cascade()

    exits = cascade_df[cascade_df["exits_this_month"] != ""]
    if not exits.empty:
        print("\n  Exit Events:")
        for _, row in exits.iterrows():
            print(f"  Month {row['month']:>2}: {row['exits_this_month']:<30} "
                  f"({row['btc_sold_this_month']:,.0f} BTC sold, "
                  f"price → ${row['btc_price']:,.0f})")

    final = cascade_df.iloc[-1]
    print(f"\n  Final state (month 36):")
    print(f"    BTC Price:     ${final['btc_price']:,.0f} "
          f"({(final['btc_price'] / 100_000 - 1) * 100:+.1f}%)")
    print(f"    Pollution:     {final['pollution_rate']:.1%}")
    print(f"    Holdings left: {final['institutional_pct_remaining']:.1f}%")

    # --- Save Plot ---
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "institutional_exit.png"

    print(f"\n💾 Saving visualization...")
    plot_institutional_analysis(risk_df, cascade_df, str(output_path))

    # --- Save CSV ---
    csv_path = output_dir / "institutional_exit_risk.csv"
    risk_df.to_csv(csv_path, index=False)
    print(f"  📄 Risk data saved to {csv_path}")

    cascade_csv = output_dir / "institutional_exit_cascade.csv"
    cascade_df.to_csv(cascade_csv, index=False)
    print(f"  📄 Cascade data saved to {cascade_csv}")

    print(f"\n{'=' * 72}")
    print("  ✅ Institutional exit analysis complete.")
    print(f"{'=' * 72}")
