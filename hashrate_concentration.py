"""
hashrate_concentration.py — Censorship Risk Model
===================================================

Models Bitcoin's censorship resistance by analyzing mining pool
concentration, geographic distribution, and entity control.

Computes the Nakamoto Coefficient, a Censorship-Resistance Score,
and estimates the cost of targeted transaction censorship.
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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NETWORK_HASHRATE_EH = 850         # ~850 EH/s mid-2025
BLOCK_REWARD_BTC = 3.125
BLOCKS_PER_DAY = 144
BTC_PRICE_USD = 100_000           # Reference price


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class MiningPool:
    """Profile of a Bitcoin mining pool.

    Attributes
    ----------
    name : str
        Pool name.
    hashrate_share : float
        Fraction of global hashrate (0–1).
    jurisdiction : str
        Primary legal jurisdiction (ISO country code).
    entity_group : str
        Parent entity or conglomerate (for entity consolidation).
    known_kyc : bool
        Whether the pool enforces KYC on miners.
    government_linked : bool
        Whether the pool has known government ties or obligations.
    """
    name: str
    hashrate_share: float
    jurisdiction: str
    entity_group: str
    known_kyc: bool = False
    government_linked: bool = False


@dataclass
class GeographicRegion:
    """Geographic concentration of hashrate.

    Attributes
    ----------
    region : str
        Region or country name.
    hashrate_share : float
        Fraction of global hashrate in this region (0–1).
    regulatory_risk : float
        Regulatory hostility score (0=friendly, 1=hostile).
    """
    region: str
    hashrate_share: float
    regulatory_risk: float


# ---------------------------------------------------------------------------
# Default Data (mid-2025 estimates)
# ---------------------------------------------------------------------------

DEFAULT_POOLS: List[MiningPool] = [
    MiningPool("Foundry USA", 0.30, "US", "DCG", True, False),
    MiningPool("AntPool", 0.18, "CN", "Bitmain", False, False),
    MiningPool("F2Pool", 0.12, "CN", "F2Pool", False, False),
    MiningPool("ViaBTC", 0.08, "CN", "ViaBTC", False, False),
    MiningPool("Binance Pool", 0.06, "Global", "Binance", True, False),
    MiningPool("MARA Pool", 0.05, "US", "Marathon", True, False),
    MiningPool("Braiins Pool", 0.04, "CZ", "Braiins", False, False),
    MiningPool("SpiderPool", 0.03, "CN", "SpiderPool", False, False),
    MiningPool("Luxor", 0.03, "US", "Luxor", True, False),
    MiningPool("SBI Crypto", 0.02, "JP", "SBI", True, True),
    MiningPool("Other/Unknown", 0.09, "Global", "Decentralized", False, False),
]

DEFAULT_REGIONS: List[GeographicRegion] = [
    GeographicRegion("United States", 0.38, 0.4),
    GeographicRegion("China", 0.21, 0.8),
    GeographicRegion("Russia", 0.08, 0.7),
    GeographicRegion("Kazakhstan", 0.06, 0.5),
    GeographicRegion("Canada", 0.05, 0.3),
    GeographicRegion("Germany", 0.03, 0.4),
    GeographicRegion("Malaysia", 0.03, 0.3),
    GeographicRegion("Iran", 0.02, 0.9),
    GeographicRegion("Other", 0.14, 0.3),
]


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def nakamoto_coefficient(pools: List[MiningPool]) -> int:
    """Calculate the Nakamoto Coefficient for mining pools.

    The Nakamoto Coefficient is the minimum number of entities that
    together control >50% of the network hashrate.

    Parameters
    ----------
    pools : list of MiningPool
        Mining pool profiles.

    Returns
    -------
    int
        Nakamoto Coefficient (minimum entities for 51% control).
    """
    # Group by entity
    entity_shares: dict[str, float] = {}
    for pool in pools:
        entity_shares[pool.entity_group] = (
            entity_shares.get(pool.entity_group, 0.0) + pool.hashrate_share
        )

    sorted_shares = sorted(entity_shares.values(), reverse=True)

    cumulative = 0.0
    for i, share in enumerate(sorted_shares, 1):
        cumulative += share
        if cumulative > 0.50:
            return i

    return len(sorted_shares)


def herfindahl_index(pools: List[MiningPool]) -> float:
    """Calculate the Herfindahl-Hirschman Index (HHI) for mining concentration.

    Parameters
    ----------
    pools : list of MiningPool
        Mining pool profiles.

    Returns
    -------
    float
        HHI value (0–10000). Higher = more concentrated.
    """
    entity_shares: dict[str, float] = {}
    for pool in pools:
        entity_shares[pool.entity_group] = (
            entity_shares.get(pool.entity_group, 0.0) + pool.hashrate_share
        )

    return sum((s * 100) ** 2 for s in entity_shares.values())


def geographic_concentration_risk(
    regions: List[GeographicRegion],
) -> float:
    """Calculate a geographic concentration risk score.

    Weighted by both hashrate share and regulatory risk.

    Parameters
    ----------
    regions : list of GeographicRegion
        Geographic hashrate distribution.

    Returns
    -------
    float
        Risk score in [0, 1]. Higher = more concentrated/risky.
    """
    # Geographic HHI: sum of squared shares, range [1/N, 1]
    # Normalize to [0, 1]: (HHI - 1/N) / (1 - 1/N)
    geo_hhi_raw = sum(r.hashrate_share ** 2 for r in regions)
    n = len(regions)
    if n > 1:
        geo_hhi = (geo_hhi_raw - 1.0 / n) / (1.0 - 1.0 / n)
    else:
        geo_hhi = 1.0
    geo_hhi = float(np.clip(geo_hhi, 0.0, 1.0))

    # Regulatory-weighted risk: already in [0, 1] since both factors are [0,1]
    reg_risk = sum(r.hashrate_share * r.regulatory_risk for r in regions)

    # Combine: 50% concentration, 50% regulatory — both in [0, 1]
    return 0.5 * geo_hhi + 0.5 * reg_risk


def censorship_resistance_score(
    pools: List[MiningPool],
    regions: List[GeographicRegion],
) -> float:
    """Compute an overall Censorship-Resistance Score (0–100).

    Higher = more resistant to censorship. Combines:
    - Nakamoto Coefficient (entity diversity)
    - HHI (pool concentration)
    - Geographic distribution risk
    - KYC/government exposure

    Parameters
    ----------
    pools : list of MiningPool
        Mining pool profiles.
    regions : list of GeographicRegion
        Geographic hashrate distribution.

    Returns
    -------
    float
        Score in [0, 100].
    """
    nak = nakamoto_coefficient(pools)
    hhi = herfindahl_index(pools)
    geo_risk = geographic_concentration_risk(regions)

    # KYC exposure: fraction of hashrate under KYC pools
    kyc_share = sum(p.hashrate_share for p in pools if p.known_kyc)
    gov_share = sum(p.hashrate_share for p in pools if p.government_linked)

    # Component scores (0-25 each)
    # Nakamoto: 2=worst (25→0), 10+=best (25)
    nak_score = min(25, max(0, (nak - 2) * 25 / 8))

    # HHI: 10000=monopoly(0), <1000=competitive(25)
    hhi_score = max(0, 25 * (1 - hhi / 3000))

    # Geographic: 0=low risk(25), 1=high risk(0)
    geo_score = 25 * (1 - geo_risk)

    # KYC/Gov: 0%=free(25), 100%=surveilled(0)
    compliance_exposure = 0.7 * kyc_share + 0.3 * gov_share
    compliance_score = 25 * (1 - compliance_exposure)

    total = nak_score + hhi_score + geo_score + compliance_score
    return float(np.clip(total, 0, 100))


def estimate_censorship_cost(
    pools: List[MiningPool],
    target_share: float = 0.51,
    btc_price: float = BTC_PRICE_USD,
) -> dict:
    """Estimate the cost of achieving targeted transaction censorship.

    Models the annual cost an attacker would need to pay to convince
    enough mining pools to censor specific transactions.

    Parameters
    ----------
    pools : list of MiningPool
        Mining pool profiles.
    target_share : float
        Hashrate share needed for reliable censorship (default 51%).
    btc_price : float
        Current BTC price for revenue calculations.

    Returns
    -------
    dict
        Cost estimates and methodology details.
    """
    daily_revenue_usd = BLOCK_REWARD_BTC * BLOCKS_PER_DAY * btc_price
    annual_revenue_usd = daily_revenue_usd * 365

    # Sort pools by "compliance likelihood" (KYC pools more likely to comply)
    sorted_pools = sorted(
        pools,
        key=lambda p: (p.government_linked, p.known_kyc, -p.hashrate_share),
        reverse=True,
    )

    # Calculate cost: pools need compensation for risk of losing revenue
    cumulative_share = 0.0
    total_cost = 0.0
    recruited_pools = []

    for pool in sorted_pools:
        if cumulative_share >= target_share:
            break

        # Cost multiplier based on pool characteristics
        if pool.government_linked:
            multiplier = 0.1  # Government can compel at low cost
        elif pool.known_kyc:
            multiplier = 0.5  # KYC pools have compliance infrastructure
        else:
            multiplier = 2.0  # Non-KYC pools need strong incentive

        pool_annual_revenue = pool.hashrate_share * annual_revenue_usd
        recruitment_cost = pool_annual_revenue * multiplier

        total_cost += recruitment_cost
        cumulative_share += pool.hashrate_share
        recruited_pools.append((pool.name, pool.hashrate_share, recruitment_cost))

    return {
        "target_share": target_share,
        "achieved_share": cumulative_share,
        "annual_cost_usd": total_cost,
        "recruited_pools": recruited_pools,
        "daily_network_revenue_usd": daily_revenue_usd,
        "pools_needed": len(recruited_pools),
    }


def simulate_concentration_scenarios(
    pools: List[MiningPool] = DEFAULT_POOLS,
    regions: List[GeographicRegion] = DEFAULT_REGIONS,
) -> pd.DataFrame:
    """Simulate how concentration changes affect censorship resistance.

    Models scenarios where the largest entity gains market share.

    Parameters
    ----------
    pools : list of MiningPool
        Baseline pool distribution.
    regions : list of GeographicRegion
        Geographic distribution.

    Returns
    -------
    pd.DataFrame
        Scenario results.
    """
    scenarios = []

    # Baseline
    scenarios.append({
        "scenario": "Current (Baseline)",
        "top_entity_share": max(
            sum(p.hashrate_share for p in pools if p.entity_group == eg)
            for eg in {p.entity_group for p in pools}
        ),
        "nakamoto_coeff": nakamoto_coefficient(pools),
        "hhi": herfindahl_index(pools),
        "cr_score": censorship_resistance_score(pools, regions),
    })

    # Scenario: top entity grows by 5%, 10%, 15%
    for growth in [0.05, 0.10, 0.15, 0.20]:
        modified_pools = []
        # Find top entity
        entity_shares: dict[str, float] = {}
        for p in pools:
            entity_shares[p.entity_group] = (
                entity_shares.get(p.entity_group, 0.0) + p.hashrate_share
            )
        top_entity = max(entity_shares, key=entity_shares.get)  # type: ignore

        for p in pools:
            new_share = p.hashrate_share
            if p.entity_group == top_entity:
                new_share += growth * (p.hashrate_share / entity_shares[top_entity])
            else:
                # Others lose proportionally
                other_total = 1.0 - entity_shares[top_entity]
                if other_total > 0:
                    new_share -= growth * (p.hashrate_share / other_total)
                    new_share = max(0.001, new_share)
            modified_pools.append(MiningPool(
                p.name, new_share, p.jurisdiction, p.entity_group,
                p.known_kyc, p.government_linked,
            ))

        top_share = entity_shares[top_entity] + growth
        scenarios.append({
            "scenario": f"Top entity +{growth:.0%}",
            "top_entity_share": top_share,
            "nakamoto_coeff": nakamoto_coefficient(modified_pools),
            "hhi": herfindahl_index(modified_pools),
            "cr_score": censorship_resistance_score(modified_pools, regions),
        })

    return pd.DataFrame(scenarios)


def plot_concentration_analysis(
    pools: List[MiningPool],
    regions: List[GeographicRegion],
    scenario_df: pd.DataFrame,
    output_path: Optional[str] = None,
) -> None:
    """Create a multi-panel visualization of hashrate concentration.

    Parameters
    ----------
    pools : list of MiningPool
        Mining pool profiles.
    regions : list of GeographicRegion
        Geographic distribution.
    scenario_df : pd.DataFrame
        Scenario analysis results.
    output_path : str, optional
        File path to save the plot.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        "Bitcoin Hashrate Concentration & Censorship Risk",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    # --- Panel 1: Pool Distribution (Pie) ---
    ax1 = axes[0, 0]
    pool_names = [p.name for p in pools]
    pool_shares = [p.hashrate_share for p in pools]
    colors = plt.cm.Set3(np.linspace(0, 1, len(pools)))
    wedges, texts, autotexts = ax1.pie(
        pool_shares,
        labels=pool_names,
        autopct="%1.1f%%",
        colors=colors,
        pctdistance=0.85,
        textprops={"fontsize": 8},
    )
    for t in autotexts:
        t.set_fontsize(7)
    ax1.set_title("Mining Pool Hashrate Distribution")

    # --- Panel 2: Geographic Distribution ---
    ax2 = axes[0, 1]
    region_names = [r.region for r in regions]
    region_shares = [r.hashrate_share * 100 for r in regions]
    region_risks = [r.regulatory_risk for r in regions]
    bar_colors = [plt.cm.RdYlGn_r(risk) for risk in region_risks]
    bars = ax2.barh(region_names, region_shares, color=bar_colors, alpha=0.8)
    ax2.set_xlabel("Hashrate Share (%)")
    ax2.set_title("Geographic Distribution (color=regulatory risk)")
    ax2.grid(True, alpha=0.3, axis="x")

    # --- Panel 3: Scenario Analysis ---
    ax3 = axes[1, 0]
    x = range(len(scenario_df))
    ax3.bar(x, scenario_df["cr_score"], color="#3498db", alpha=0.7)
    ax3.set_xticks(list(x))
    ax3.set_xticklabels(scenario_df["scenario"], rotation=30, ha="right", fontsize=8)
    ax3.set_ylabel("Censorship Resistance Score")
    ax3.set_title("Censorship Resistance Under Concentration Scenarios")
    ax3.axhline(y=50, color="orange", linestyle="--", alpha=0.5, label="Warning")
    ax3.axhline(y=25, color="red", linestyle="--", alpha=0.5, label="Critical")
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis="y")
    ax3.set_ylim(0, 100)

    # --- Panel 4: Entity Concentration ---
    ax4 = axes[1, 1]
    entity_shares: dict[str, float] = {}
    for p in pools:
        entity_shares[p.entity_group] = (
            entity_shares.get(p.entity_group, 0.0) + p.hashrate_share
        )
    sorted_entities = sorted(entity_shares.items(), key=lambda x: x[1], reverse=True)
    ent_names = [e[0] for e in sorted_entities]
    ent_shares = [e[1] * 100 for e in sorted_entities]
    cumulative = np.cumsum(ent_shares)

    ax4.bar(range(len(ent_names)), ent_shares, color="#2ecc71", alpha=0.7, label="Share")
    ax4_twin = ax4.twinx()
    ax4_twin.plot(range(len(ent_names)), cumulative, "r-o", linewidth=2, label="Cumulative")
    ax4_twin.axhline(y=51, color="red", linestyle="--", alpha=0.5)
    ax4_twin.set_ylabel("Cumulative %", color="red")
    ax4.set_xticks(range(len(ent_names)))
    ax4.set_xticklabels(ent_names, rotation=45, ha="right", fontsize=8)
    ax4.set_ylabel("Hashrate Share (%)")
    ax4.set_title("Entity Concentration (Nakamoto Analysis)")
    ax4.grid(True, alpha=0.3, axis="y")

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")
        print(f"  📊 Plot saved to {output_path}")

    plt.close(fig)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("  🏗️  Bitcoin Hashrate Concentration & Censorship Risk Analysis")
    print("  Model: powsec-models v0.2.0")
    print("=" * 72)

    # --- Pool Summary ---
    print("\n📋 Mining Pool Distribution:\n")
    print(f"  {'Pool':<18} {'Share':>7} {'Jurisdiction':<8} {'Entity':<15} {'KYC':>4} {'Gov':>4}")
    print(f"  {'─' * 18} {'─' * 7} {'─' * 8} {'─' * 15} {'─' * 4} {'─' * 4}")
    for p in DEFAULT_POOLS:
        print(f"  {p.name:<18} {p.hashrate_share:>6.1%} {p.jurisdiction:<8} "
              f"{p.entity_group:<15} {'✓' if p.known_kyc else '✗':>4} "
              f"{'✓' if p.government_linked else '✗':>4}")

    # --- Key Metrics ---
    nak = nakamoto_coefficient(DEFAULT_POOLS)
    hhi = herfindahl_index(DEFAULT_POOLS)
    cr = censorship_resistance_score(DEFAULT_POOLS, DEFAULT_REGIONS)
    geo_risk = geographic_concentration_risk(DEFAULT_REGIONS)

    print(f"\n📊 Key Metrics:")
    print(f"  Nakamoto Coefficient:        {nak} entities")
    print(f"  Herfindahl Index (HHI):      {hhi:.0f} (>2500 = highly concentrated)")
    print(f"  Geographic Risk Score:        {geo_risk:.3f}")
    print(f"  Censorship Resistance Score:  {cr:.1f}/100")

    # --- Censorship Cost ---
    print(f"\n💰 Censorship Cost Estimates:")
    for target in [0.33, 0.51, 0.67]:
        cost = estimate_censorship_cost(DEFAULT_POOLS, target_share=target)
        print(f"\n  Target: {target:.0%} hashrate control")
        print(f"  Pools needed: {cost['pools_needed']}")
        print(f"  Achieved share: {cost['achieved_share']:.1%}")
        print(f"  Estimated annual cost: ${cost['annual_cost_usd']:,.0f}")
        print(f"  Recruited pools:")
        for name, share, c in cost["recruited_pools"]:
            print(f"    - {name:<18} ({share:.1%}) → ${c:,.0f}/yr")

    # --- Scenario Analysis ---
    print(f"\n📈 Concentration Scenarios:")
    scenario_df = simulate_concentration_scenarios()
    print(f"\n  {'Scenario':<22} {'Top Entity':>12} {'Nakamoto':>9} {'HHI':>7} {'CR Score':>9}")
    print(f"  {'─' * 22} {'─' * 12} {'─' * 9} {'─' * 7} {'─' * 9}")
    for _, row in scenario_df.iterrows():
        print(f"  {row['scenario']:<22} {row['top_entity_share']:>11.1%} "
              f"{row['nakamoto_coeff']:>9} {row['hhi']:>7.0f} {row['cr_score']:>8.1f}")

    # --- Save Plot ---
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "hashrate_concentration.pdf"

    print(f"\n💾 Saving visualization...")
    plot_concentration_analysis(DEFAULT_POOLS, DEFAULT_REGIONS, scenario_df, str(output_path))

    # --- Save CSV ---
    csv_path = output_dir / "hashrate_concentration_data.csv"
    scenario_df.to_csv(csv_path, index=False)
    print(f"  📄 Data saved to {csv_path}")

    print(f"\n{'=' * 72}")
    print("  ✅ Hashrate concentration analysis complete.")
    print(f"{'=' * 72}")
