#!/usr/bin/env python3
"""
Create 3 infographic diagrams for the PoW Security paper Introduction section.
Figures 5-7: Bitcoin Mining Flow, Risk Vector Map, Fee Market Thermostat.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# Consistent color palette
BLUE_DARK = '#1a5276'
BLUE_MED = '#2980b9'
BLUE_LIGHT = '#85c1e9'
RED = '#c0392b'
RED_LIGHT = '#e74c3c'
GREEN = '#27ae60'
GREEN_LIGHT = '#82e0aa'
ORANGE = '#e67e22'
GRAY = '#7f8c8d'
GRAY_LIGHT = '#bdc3c7'
GRAY_DARK = '#2c3e50'
WHITE = '#ffffff'
GOLD = '#f39c12'

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def draw_box(ax, x, y, w, h, text, color=BLUE_MED, textcolor='white', fontsize=9, alpha=1.0, style='round'):
    """Draw a rounded rectangle with centered text."""
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad=0.05", 
                         facecolor=color, edgecolor=GRAY_DARK,
                         linewidth=1.2, alpha=alpha, zorder=3)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=textcolor, zorder=4, wrap=True,
            linespacing=1.3)
    return box


def draw_arrow(ax, x1, y1, x2, y2, color=GRAY_DARK, lw=1.5, style='->', mutation=20):
    """Draw an arrow between two points."""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, color=color,
                            linewidth=lw, mutation_scale=mutation,
                            zorder=2, connectionstyle='arc3,rad=0')
    ax.add_patch(arrow)
    return arrow


def draw_curved_arrow(ax, x1, y1, x2, y2, color=GRAY_DARK, lw=1.5, rad=0.3, style='->'):
    """Draw a curved arrow."""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, color=color,
                            linewidth=lw, mutation_scale=18,
                            zorder=2, connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(arrow)
    return arrow


# ============================================================
# FIGURE 5: Bitcoin Mining Flow
# ============================================================
def create_bitcoin_mining_flow():
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)

    # Title
    ax.text(5, 6.7, 'Bitcoin Proof-of-Work Mining Process', ha='center', va='center',
            fontsize=14, fontweight='bold', color=GRAY_DARK)

    # === Main flow (top row) ===
    nodes = [
        (1.2, 5.2, 1.6, 0.7, 'Transaction\nPool', BLUE_LIGHT, GRAY_DARK),
        (3.3, 5.2, 1.6, 0.7, 'Block\nAssembly', BLUE_MED, WHITE),
        (5.5, 5.2, 1.7, 0.7, 'Cryptographic\nPuzzle (PoW)', ORANGE, WHITE),
        (7.6, 5.2, 1.4, 0.7, 'Valid\nBlock', GREEN, WHITE),
        (9.2, 5.2, 1.2, 0.7, 'Chain\nExtension', BLUE_DARK, WHITE),
    ]
    for x, y, w, h, text, color, tc in nodes:
        draw_box(ax, x, y, w, h, text, color=color, textcolor=tc, fontsize=8)

    # Arrows between main flow
    arrow_pairs = [(2.0, 5.2, 2.5, 5.2), (4.1, 5.2, 4.65, 5.2),
                   (6.35, 5.2, 6.9, 5.2), (8.3, 5.2, 8.6, 5.2)]
    for x1, y1, x2, y2 in arrow_pairs:
        draw_arrow(ax, x1, y1, x2, y2, color=GRAY_DARK, lw=2)

    # === Reward mechanism (below main flow) ===
    draw_box(ax, 5.5, 3.8, 2.4, 0.55, 'Block Reward: 3.125 BTC\n+ Transaction Fees',
             color=GOLD, textcolor=GRAY_DARK, fontsize=7.5)
    draw_box(ax, 8.5, 3.8, 1.3, 0.55, 'Miner\nRevenue', color=GREEN, textcolor=WHITE, fontsize=8)
    draw_arrow(ax, 5.5, 4.85, 5.5, 4.08, color=GOLD, lw=1.5)
    draw_arrow(ax, 6.7, 3.8, 7.85, 3.8, color=GOLD, lw=2)

    # === Halving timeline (bottom left) ===
    ax.text(1.0, 2.7, 'Halving Schedule', ha='left', fontsize=10, fontweight='bold', color=GRAY_DARK)
    halvings = ['50 BTC', '25 BTC', '12.5 BTC', '6.25 BTC', '3.125 BTC']
    years = ['2009', '2012', '2016', '2020', '2024']
    for i, (h, yr) in enumerate(zip(halvings, years)):
        x = 0.8 + i * 1.45
        alpha = 0.4 + 0.15 * i
        color = BLUE_MED if i < 4 else GREEN
        draw_box(ax, x, 2.0, 1.3, 0.5, h, color=color, textcolor=WHITE, fontsize=7.5, alpha=alpha if i < 4 else 1.0)
        ax.text(x, 1.6, yr, ha='center', fontsize=7, color=GRAY)
        if i < len(halvings) - 1:
            draw_arrow(ax, x + 0.65, 2.0, x + 0.8, 2.0, color=GRAY, lw=1)
    ax.text(3.7, 1.2, '÷2 every ~210,000 blocks (~4 years)', ha='center', fontsize=7.5,
            style='italic', color=GRAY)

    # === DAA feedback loop (bottom right) ===
    ax.text(7.5, 2.7, 'Difficulty Adjustment (DAA)', ha='left', fontsize=10, fontweight='bold', color=GRAY_DARK)

    draw_box(ax, 7.6, 2.0, 1.6, 0.5, 'Blocks too fast', color=RED_LIGHT, textcolor=WHITE, fontsize=7.5)
    draw_box(ax, 9.4, 2.0, 1.0, 0.5, 'Diff ↑', color=RED, textcolor=WHITE, fontsize=8)
    draw_arrow(ax, 8.4, 2.0, 8.9, 2.0, color=RED, lw=1.5)

    draw_box(ax, 7.6, 1.2, 1.6, 0.5, 'Blocks too slow', color=GREEN_LIGHT, textcolor=GRAY_DARK, fontsize=7.5)
    draw_box(ax, 9.4, 1.2, 1.0, 0.5, 'Diff ↓', color=GREEN, textcolor=WHITE, fontsize=8)
    draw_arrow(ax, 8.4, 1.2, 8.9, 1.2, color=GREEN, lw=1.5)

    ax.text(8.5, 0.7, 'Every 2,016 blocks (~2 weeks)', ha='center', fontsize=7.5,
            style='italic', color=GRAY)

    # Feedback arrow from DAA back to puzzle
    draw_curved_arrow(ax, 9.4, 2.5, 5.5, 4.85, color=GRAY, lw=1.0, rad=-0.2, style='->')
    ax.text(8.0, 3.45, 'adjusts\ntarget', ha='center', fontsize=6.5, color=GRAY, style='italic')

    # Subtle border
    rect = plt.Rectangle((0.15, 0.4), 9.7, 6.5, fill=False, edgecolor=GRAY_LIGHT, linewidth=1)
    ax.add_patch(rect)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'bitcoin_mining_flow.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved {path}')


# ============================================================
# FIGURE 6: Risk Vector Map
# ============================================================
def create_risk_vector_map():
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-4, 4)
    ax.axis('off')
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)

    ax.text(0, 3.7, 'Interconnected Risk Vector Map', ha='center',
            fontsize=14, fontweight='bold', color=GRAY_DARK)

    # 4 main risk nodes in diamond layout
    risk_nodes = {
        'mc': (0, 2.2, 'Miner\nCapitulation', BLUE_DARK),
        'cp': (-3.2, 0, 'Content\nPollution', ORANGE),
        'hc': (3.2, 0, 'Hashrate\nConcentration', RED),
        'ie': (0, -2.2, 'Institutional\nExit', BLUE_MED),
    }
    for key, (x, y, label, color) in risk_nodes.items():
        draw_box(ax, x, y, 2.2, 0.9, label, color=color, textcolor=WHITE, fontsize=9)

    # Central node
    draw_box(ax, 0, 0, 1.8, 0.65, 'Systemic Risk\n(Interconnected)', 
             color=GRAY_DARK, textcolor=WHITE, fontsize=7.5)

    # Connection lines to center
    for key, (x, y, _, _) in risk_nodes.items():
        cx, cy = x * 0.35, y * 0.35
        draw_arrow(ax, cx, cy, x - np.sign(x) * 0.9 if x != 0 else x, 
                   y - np.sign(y) * 0.45 if y != 0 else y,
                   color=GRAY_LIGHT, lw=1, style='-')

    # === DESTABILIZING LOOPS (red) ===
    # Price decline → miner exit → concentration ↑
    draw_curved_arrow(ax, 0.9, 1.75, 2.1, 0.45, color=RED, lw=2.0, rad=-0.3)
    ax.text(2.3, 1.2, 'miner exit →\nconcentration ↑', fontsize=6.5, color=RED,
            ha='left', style='italic')

    # Pollution → compliance → institutional exit
    draw_curved_arrow(ax, -2.1, -0.45, -0.9, -1.75, color=RED, lw=2.0, rad=-0.3)
    ax.text(-3.5, -1.3, 'compliance\ntrigger', fontsize=6.5, color=RED,
            ha='center', style='italic')

    # Institutional exit → price decline → miner exit
    draw_curved_arrow(ax, -0.9, -1.75, -2.1, -0.45, color=RED, lw=2.0, rad=0.5)
    ax.text(-2.3, -1.5, 'price\ndecline', fontsize=6.5, color=RED, ha='center', style='italic')
    
    draw_curved_arrow(ax, -2.1, 0.45, -0.9, 1.75, color=RED, lw=2.0, rad=-0.3)
    ax.text(-2.5, 1.2, 'price decline\n→ miner exit', fontsize=6.5, color=RED,
            ha='center', style='italic')

    # === STABILIZING LOOPS (green) ===
    # Miner exit → DAA → lower breakeven
    draw_curved_arrow(ax, 0.9, 1.75, 2.1, 0.45, color=GREEN, lw=2.0, rad=0.4)
    ax.text(2.5, 0.6, 'DAA adjustment\n→ lower breakeven', fontsize=6.5, color=GREEN,
            ha='left', style='italic')

    # Pollution ↑ → fees ↑ → pushback → pollution ↓
    draw_curved_arrow(ax, -3.2, -0.45, -3.2, 0.0, color=GREEN, lw=2.0, rad=-2.5)
    ax.text(-4.7, -0.0, 'fees ↑ →\npushback →\npollution ↓', fontsize=6.5, color=GREEN,
            ha='center', style='italic')

    # Legend
    legend_y = -3.3
    ax.plot([-2.5, -1.8], [legend_y, legend_y], color=RED, lw=2)
    ax.annotate('', xy=(-1.8, legend_y), xytext=(-2.0, legend_y),
                arrowprops=dict(arrowstyle='->', color=RED, lw=2))
    ax.text(-1.6, legend_y, 'Destabilizing feedback', fontsize=8, color=RED, va='center')

    ax.plot([1.0, 1.7], [legend_y, legend_y], color=GREEN, lw=2)
    ax.annotate('', xy=(1.7, legend_y), xytext=(1.5, legend_y),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=2))
    ax.text(1.9, legend_y, 'Stabilizing feedback', fontsize=8, color=GREEN, va='center')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'risk_vector_map.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved {path}')


# ============================================================
# FIGURE 7: Fee Market Thermostat
# ============================================================
def create_fee_market_thermostat():
    fig = plt.figure(figsize=(10, 7))
    fig.patch.set_facecolor(WHITE)

    # Main diagram area
    ax_main = fig.add_axes([0.05, 0.25, 0.55, 0.65])
    ax_main.set_xlim(0, 10)
    ax_main.set_ylim(0, 8)
    ax_main.axis('off')
    ax_main.set_facecolor(WHITE)

    # Inset: pushback curve
    ax_inset = fig.add_axes([0.63, 0.45, 0.33, 0.35])

    # Stacked bar: block space
    ax_bar = fig.add_axes([0.05, 0.05, 0.55, 0.15])

    # Title
    ax_main.text(5, 7.7, 'Fee-Market Thermostat Mechanism', ha='center',
                 fontsize=14, fontweight='bold', color=GRAY_DARK)

    # === Thermostat cycle ===
    cycle_nodes = [
        (2.0, 6.0, 'Inscriptions\nFill Blocks', ORANGE),
        (5.0, 6.0, 'Fees\nRise', RED),
        (8.0, 6.0, 'Low-Value\nInscriptions\nPriced Out', GREEN),
        (5.0, 3.5, 'Equilibrium\n~40% Saturation', BLUE_DARK),
    ]
    for x, y, text, color in cycle_nodes:
        draw_box(ax_main, x, y, 2.0, 0.9, text, color=color, textcolor=WHITE, fontsize=8)

    # Arrows forming the cycle
    draw_arrow(ax_main, 3.0, 6.0, 4.0, 6.0, color=GRAY_DARK, lw=2)
    draw_arrow(ax_main, 6.0, 6.0, 7.0, 6.0, color=GRAY_DARK, lw=2)
    draw_curved_arrow(ax_main, 8.0, 5.55, 6.0, 3.5, color=GREEN, lw=2, rad=-0.3)
    draw_curved_arrow(ax_main, 4.0, 3.5, 2.0, 5.55, color=BLUE_MED, lw=2, rad=-0.3)

    # Labels on cycle arrows  
    ax_main.text(3.5, 6.3, 'demand ↑', fontsize=7, color=GRAY_DARK, ha='center', style='italic')
    ax_main.text(6.5, 6.3, 'pushback', fontsize=7, color=GRAY_DARK, ha='center', style='italic')
    ax_main.text(7.5, 4.5, 'dampening', fontsize=7, color=GREEN, ha='center', style='italic', rotation=-40)
    ax_main.text(2.5, 4.5, 'space freed', fontsize=7, color=BLUE_MED, ha='center', style='italic', rotation=40)

    # Block space annotation
    ax_main.text(5.0, 2.3, 'Block Space: 4M weight units (fixed)', ha='center',
                 fontsize=9, fontweight='bold', color=GRAY_DARK,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor=GRAY_LIGHT, alpha=0.3))

    # === Pushback curve inset ===
    f = np.linspace(0, 200, 500)
    f0 = 30  # reference fee
    pushback = 1 / (1 + (f / f0) ** 2)
    ax_inset.plot(f, pushback, color=BLUE_DARK, lw=2)
    ax_inset.fill_between(f, pushback, alpha=0.15, color=BLUE_MED)
    ax_inset.axhline(y=0.5, color=GRAY, ls='--', lw=0.8, alpha=0.7)
    ax_inset.axvline(x=f0, color=GRAY, ls='--', lw=0.8, alpha=0.7)
    ax_inset.set_xlabel('Average Fee Rate (sat/vB)', fontsize=8)
    ax_inset.set_ylabel('Pushback Factor', fontsize=8)
    ax_inset.set_title(r'$f_{\mathrm{pushback}} = \frac{1}{1 + (f/f_0)^2}$', fontsize=10, color=GRAY_DARK)
    ax_inset.tick_params(labelsize=7)
    ax_inset.set_ylim(0, 1.05)
    ax_inset.annotate(f'f₀ = {f0}', xy=(f0, 0.5), xytext=(80, 0.7),
                      fontsize=7, color=GRAY_DARK,
                      arrowprops=dict(arrowstyle='->', color=GRAY, lw=0.8))
    ax_inset.spines['top'].set_visible(False)
    ax_inset.spines['right'].set_visible(False)

    # Equilibrium annotation inset
    ax_eq = fig.add_axes([0.63, 0.12, 0.33, 0.25])
    saturation = np.linspace(0, 1, 200)
    fee_response = np.exp(3 * saturation) - 1
    fee_response = fee_response / fee_response.max() * 100
    dampening = 100 * (1 - saturation)
    ax_eq.plot(saturation * 100, fee_response, color=RED, lw=2, label='Fee pressure')
    ax_eq.plot(saturation * 100, dampening, color=GREEN, lw=2, label='Dampening')
    # Intersection ~ 40%
    ax_eq.axvline(x=40, color=GRAY, ls=':', lw=1)
    ax_eq.annotate('Equilibrium\n~40%', xy=(40, 50), xytext=(60, 70),
                   fontsize=7, color=GRAY_DARK, fontweight='bold',
                   arrowprops=dict(arrowstyle='->', color=GRAY_DARK, lw=0.8))
    ax_eq.set_xlabel('Pollution Saturation (%)', fontsize=8)
    ax_eq.set_ylabel('Relative Magnitude', fontsize=8)
    ax_eq.set_title('Equilibrium Point', fontsize=9, fontweight='bold', color=GRAY_DARK)
    ax_eq.tick_params(labelsize=7)
    ax_eq.legend(fontsize=7, loc='upper left')
    ax_eq.spines['top'].set_visible(False)
    ax_eq.spines['right'].set_visible(False)

    # === Stacked bar: block space competition ===
    financial = 60
    inscriptions = 35
    other = 5
    bars = ax_bar.barh(['Block Space'], [financial], color=BLUE_MED, height=0.5, label='Financial Txs')
    ax_bar.barh(['Block Space'], [inscriptions], left=[financial], color=ORANGE, height=0.5, label='Ordinals/Inscriptions')
    ax_bar.barh(['Block Space'], [other], left=[financial + inscriptions], color=GRAY_LIGHT, height=0.5, label='Other')
    ax_bar.set_xlim(0, 100)
    ax_bar.set_xlabel('Block Weight Utilization (%)', fontsize=8)
    ax_bar.legend(fontsize=7, loc='upper right', ncol=3)
    ax_bar.tick_params(labelsize=7)
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.text(financial/2, 0, f'{financial}%', ha='center', va='center', fontsize=8, fontweight='bold', color=WHITE)
    ax_bar.text(financial + inscriptions/2, 0, f'{inscriptions}%', ha='center', va='center', fontsize=8, fontweight='bold', color=WHITE)

    path = os.path.join(OUTPUT_DIR, 'fee_market_thermostat.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved {path}')


if __name__ == '__main__':
    create_bitcoin_mining_flow()
    create_risk_vector_map()
    create_fee_market_thermostat()
    print('All infographics created successfully.')
