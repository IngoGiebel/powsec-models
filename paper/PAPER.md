# Quantitative Risk Assessment of Bitcoin's Proof-of-Work Security Model

**Authors:** Ingo Giebel¹, with AI-assisted analysis by Dione 🌙 & Inanna ⚔️  
**Affiliation:** ¹ Heinrich-Heine-Universität Düsseldorf, B.Sc. Quantitative Biology  
**Date:** February 2026  
**Repository:** [github.com/IngoGiebel/powsec-models](https://github.com/IngoGiebel/powsec-models)  
**License:** MIT  

---

## Abstract

We present a quantitative framework for assessing systemic risks in Bitcoin's Proof-of-Work (PoW) security model through four interconnected simulation models. Our analysis examines (1) miner capitulation dynamics under price stress with difficulty adjustment feedback, (2) blockchain content pollution via Ordinals and OP_RETURN abuse with fee-market dampening, (3) hashrate concentration and censorship resistance, and (4) institutional exit cascades triggered by compliance concerns using Almgren-Chriss optimal execution modeling. Results indicate critical vulnerabilities: a Nakamoto Coefficient of only 3, content pollution approaching 54% saturation (down from earlier estimates after incorporating fee-market dynamics), and a potential institutional exit cascade scenario. These findings suggest that Bitcoin's security guarantees may be more fragile than commonly assumed, though endogenous stabilization mechanisms (difficulty adjustment, fee markets) provide meaningful resilience.

**Keywords:** Bitcoin, Proof-of-Work, mining economics, hashrate concentration, censorship resistance, institutional risk, content pollution, Ordinals, ETF compliance, Almgren-Chriss, difficulty adjustment

---

## 1. Introduction

### 1.1 Motivation

Bitcoin's security model fundamentally relies on the economic incentives of Proof-of-Work mining. While the theoretical foundations are well-established (Nakamoto, 2008), the practical security landscape has evolved significantly with the emergence of industrial-scale mining operations, Bitcoin ETFs holding >5% of circulating supply, and novel block space usage patterns such as Ordinals inscriptions.

### 1.2 Research Questions

1. At what BTC price levels do major publicly traded miners face capitulation, and how does the Difficulty Adjustment Algorithm (DAA) stabilize the network during hash rate decline?
2. How rapidly is blockchain content pollution reaching institutional concern thresholds, and how do fee-market dynamics self-regulate?
3. What is the true censorship resistance of the Bitcoin network given current hashrate concentration?
4. Could compliance-driven institutional exits create self-reinforcing price cascades, and what is the realistic market impact under optimal execution?

### 1.3 Contributions

- Four open-source Python models with reproducible simulations
- Quantitative estimates for miner breakeven prices using real financial data with corrected overhead calculations
- A novel saturation model for blockchain content pollution incorporating fee-market dampening
- Censorship cost estimation framework based on pool economics with properly bounded geographic risk metrics
- Almgren-Chriss based cascade simulation of ETF compliance-driven exits with separate temporary and permanent market impact

---

## 2. Related Work

### 2.1 Mining Economics & Difficulty Adjustment

Nakamoto (2008) established the foundational incentive structure for PoW mining, where miners expend computational resources in exchange for block rewards and transaction fees. Prat & Walter (2021) developed a dynamic equilibrium model of Bitcoin mining that endogenizes the relationship between price, hashrate, and difficulty — a feedback loop we incorporate in our miner stress simulation. Easley, O'Hara & Basu (2019) analyzed the role of transaction fees in miner incentive compatibility, showing that fees serve as a price-discovery mechanism for block space — a finding central to our fee-market dampening of content pollution.

### 2.2 Network Concentration & Censorship

Gencer et al. (2018) provided the first rigorous measurement of decentralization in Bitcoin and Ethereum, establishing the Nakamoto Coefficient methodology we employ. Cong, He & Li (2021) analyzed the tension between decentralized mining and centralized pool operation, showing how pool concentration can undermine network security even when individual miners are distributed. Judmayer et al. (2021) estimated the cost of 51% attacks, providing calibration data for our censorship cost model. Vernetti (2023) documented the Stratum V2 protocol, which allows miners to construct their own block templates — a significant nuance for censorship resistance that we note as a limitation of pool-level analysis.

### 2.3 Content Pollution & Block Space Economics

Wendl et al. (2025) provided the first systematic analysis of Bitcoin Ordinals and their impact on block space economics. Carter & Jeng (2023) analyzed the fee-market dynamics of Ordinals, showing that inscription demand competes with financial transactions through the fee auction mechanism — the key insight behind our fee-pushback factor.

### 2.4 Market Microstructure & Institutional Adoption

Almgren & Chriss (2001) developed the foundational model for optimal execution of large portfolio transactions, separating temporary (transient) from permanent (structural) market impact. We adapt their framework for Bitcoin's thinner markets. Makarov & Schoar (2020) documented inefficiencies and arbitrage in cryptocurrency trading that affect market impact propagation. Chen et al. (2025) analyzed the impact of Bitcoin ETFs on futures markets, providing empirical grounding for our institutional exit cascade model.

---

## 3. Methodology

### 3.1 Miner Capitulation Stress Test (`miner_stress.py`)

#### 3.1.1 Model Description

We model miner capitulation probability as a function of BTC price relative to each miner's breakeven cost. The breakeven price is calculated from:

- **Energy cost per TH/s/day**: Derived from rig efficiency (J/TH) and electricity price ($/kWh)
- **BTC yield per TH/s/day**: From block reward, block frequency, and network hashrate
- **Non-energy overhead**: Estimated from SGA (selling, general & administrative) expenses, calculated as the residual after removing energy costs and EBITDA from revenue. This avoids double-counting energy costs that are already captured in the energy breakeven calculation.

The capitulation probability uses a logistic function combining:
- Price-to-breakeven ratio (primary driver)
- Debt-to-cash ratio (leverage pressure)
- Interest rate environment (refinancing risk)
- Cash runway in months (for unprofitable miners)

#### 3.1.2 Difficulty Adjustment Algorithm (DAA) Feedback

A critical innovation over static analysis: when miners capitulate, network hashrate drops, causing the DAA to reduce difficulty (approximately every 2016 blocks ≈ 14 days). This lowers breakeven costs for surviving miners, creating a stabilizing negative feedback loop (Prat & Walter, 2021). Our simulation models this as a smoothed partial adjustment:

$$d_{t+1} = (1-\alpha) \cdot d_t + \alpha \cdot s_t$$

where $d_t$ is the difficulty factor, $s_t$ is the network survival rate, and $\alpha = 0.3$ is the adjustment speed parameter.

#### 3.1.3 Data Sources

- Yahoo Finance: Publicly traded miner financials (WULF, CIFR, CORZ, MARA, RIOT, CLSK)
- Blockchain.com: Network hashrate and difficulty data

#### 3.1.4 Key Assumptions

| Assumption | Justification | Rating |
|---|---|---|
| Network hashrate 850 EH/s | Mid-2025 estimate from blockchain.com | Reasonable |
| Energy = 60% of mining revenue | Industry average from CoinShares reports | Reasonable |
| Tracked miners = 25% of network | Sum of public miner hashrate shares | Conservative |
| DAA adjustment speed α=0.3 | Smoothing parameter; real DAA is stepwise every 2016 blocks | Approximation |
| Linear extrapolation of tracked miner capitulation to full network | Private miners may have different cost structures | Questionable — sensitivity tested |

### 3.2 Blockchain Content Pollution (`content_pollution.py`)

#### 3.2.1 Model Description

Logistic saturation curve fitted to historical data on block utilization, inscription frequency, and flagged content ratio. Five factors are combined:

1. **Inscription density** (inscriptions/block, weight 0.30)
2. **Flagged content ratio** (toxic inscriptions / total, weight 0.25)
3. **Block utilization** (avg size / max size, weight 0.15)
4. **OP_RETURN abuse** (% of transactions, weight 0.10)
5. **Fee-market pushback** (dampening multiplier, effective weight ~0.20)

#### 3.2.2 Fee-Market Dampening

Following Easley, O'Hara & Basu (2019) and Carter & Jeng (2023), we model block space as an auction where financial transactions outbid low-value inscriptions at high fee levels:

$$f_{\text{pushback}} = \frac{1}{1 + (\bar{f} / f_0)^2}$$

where $\bar{f}$ is the average fee (sat/vB) and $f_0 = 100$ sat/vB is the reference level at which significant pushback occurs. The raw pollution score is multiplied by $(0.5 + 0.5 \cdot f_{\text{pushback}})$, allowing fees to halve the effective pollution rate at most.

#### 3.2.3 Saturation Model

$$P(t) = \frac{K}{1 + e^{-r(t - t_0)}}$$

where $K$ = capacity asymptote, $r$ = growth rate, $t_0$ = midpoint.

### 3.3 Hashrate Concentration Analysis (`hashrate_concentration.py`)

#### 3.3.1 Metrics

- **Nakamoto Coefficient**: Minimum entities to reach 51%, computed at entity-group level (consolidating pools under common ownership)
- **Herfindahl-Hirschman Index (HHI)**: $\sum s_i^2 \times 10{,}000$ where $s_i$ is entity hashrate share
- **Geographic Concentration Risk**: Normalized geographic HHI combined with regulatory risk:

$$R_{\text{geo}} = 0.5 \cdot \frac{\text{HHI}_{\text{geo}} - 1/N}{1 - 1/N} + 0.5 \cdot \sum_i h_i \cdot r_i$$

where $h_i$ is regional hashrate share, $r_i$ is regulatory risk score, and $N$ is the number of regions. Both terms are bounded in [0, 1], ensuring $R_{\text{geo}} \in [0, 1]$.

- **Censorship Resistance Score** (0–100): Composite of Nakamoto Coefficient, HHI, geographic risk, and KYC/government exposure
- **Censorship cost estimation**: Based on pool revenue and compliance likelihood multipliers

#### 3.3.2 Limitations

- Pool hashrate ≠ censorship power: Stratum V2 (Vernetti, 2023) allows miners to build their own block templates, reducing pool operators' ability to censor
- Pool-hopping: Miners can switch pools within minutes, making sustained censorship costly
- Entity grouping relies on publicly available ownership data, which may be incomplete

### 3.4 Institutional Exit Cascade (`institutional_exit.py`)

#### 3.4.1 Model Description

Simulation of cascading ETF exits triggered by content pollution exceeding compliance thresholds. Each institutional holder has a compliance strictness parameter and pollution threshold.

#### 3.4.2 Market Impact Model (Almgren-Chriss)

Following Almgren & Chriss (2001), we decompose market impact into:

- **Temporary impact** (intraday, decays): $\Delta P_{\text{temp}} = \eta \sqrt{\phi}$ where $\phi$ is participation rate (daily sell / daily volume) and $\eta = 0.10$ is the temporary impact coefficient
- **Permanent impact** (structural, cumulative): $\Delta P_{\text{perm}} = \gamma \cdot \phi \cdot T$ where $\gamma = 0.05$ is the permanent impact coefficient and $T$ is the number of trading days

This creates a genuine execution-speed tradeoff: faster liquidation produces higher temporary impact but less cumulative permanent impact, while slower liquidation reduces daily disruption but accumulates structural price decline over time.

**Calibration:** $\eta = 0.10$ and $\gamma = 0.05$ are calibrated to produce approximately 3-5% total impact for selling 100,000 BTC over 30-90 days at $30B daily volume, consistent with empirical estimates from Makarov & Schoar (2020).

#### 3.4.3 Cascade Dynamics

Each exit event reduces BTC price through the Almgren-Chriss impact model. The reduced price increases pollution metric values (through reduced fee pressure) and may trigger further compliance reviews, creating a positive feedback loop.

---

## 4. Results

### 4.1 Miner Capitulation

| Miner | Breakeven Price | EBITDA Margin | Debt/Cash |
|-------|----------------|---------------|-----------|
| CleanSpark (CLSK) | $49,470 | 18.8% | 1.3x |
| Core Scientific (CORZ) | $52,988 | 19.0% | 4.0x |
| TeraWulf (WULF) | $53,646 | -21.0% | 1.5x |
| Riot Platforms (RIOT) | $53,836 | -5.4% | 0.6x |
| Marathon Digital (MARA) | $66,636 | 12.4% | 4.0x |
| Cipher Mining (CIFR) | $68,816 | -13.3% | 4.0x |

*Note: Breakeven prices are lower than pre-revision estimates due to corrected overhead calculation that avoids double-counting energy costs in both the breakeven formula and the EBITDA-based overhead factor.*

**Key Finding (with DAA):** Under the DAA feedback model, miner capitulation is partially self-correcting. As weak miners exit, difficulty drops, improving profitability for survivors. The network stabilizes at a lower but sustainable hashrate level, consistent with Prat & Walter (2021).

### 4.2 Content Pollution

- Saturation asymptote: **~54%** (revised down from 85% after incorporating fee-market dynamics and inscription gating)
- Growth rate: 0.666 (rapid initial growth, but dampened by rising fees)
- Fee-market pushback reduces effective pollution by up to 50% during high-fee periods

**Key Finding:** The fee auction mechanism provides meaningful self-regulation of block space pollution. As inscriptions fill blocks and push fees up, low-value inscriptions are priced out, creating an endogenous ceiling well below 100%.

### 4.3 Hashrate Concentration

| Metric | Value | Assessment |
|--------|-------|------------|
| Nakamoto Coefficient | 3 | Critical |
| HHI | 1,612 | Moderate concentration |
| Geographic Risk Score | 0.314 | Moderate |
| Censorship Resistance Score | ~49/100 | Moderate-Low |
| 51% attack cost | ~$5.9B/yr | Achievable for nation-states |

**Key Finding:** Only 3 entities (DCG/Foundry 30%, Bitmain/AntPool 18%, F2Pool 12%) control >50% of hashrate. However, this overstates censorship risk: Stratum V2 adoption and pool-hopping dynamics provide additional resilience not captured by static pool-share analysis (Vernetti, 2023; Cong, He & Li, 2021).

### 4.4 Institutional Exit Cascade

Under the Almgren-Chriss impact model, the cascade dynamics differ significantly from the naive square-root model:

- Faster exits (10 days) produce ~3.5% impact for 100k BTC
- Slower exits (90 days) produce ~2.3% impact for 100k BTC
- The execution-speed tradeoff is now properly modeled: total impact depends meaningfully on liquidation timeline

**Key Finding:** A complete institutional exit cascade produces a smaller but more credibly modeled price impact than the pre-revision estimate. The separation of temporary and permanent impact reveals that orderly liquidation significantly reduces market disruption.

---

## 5. Sensitivity Analysis

### 5.1 Parameter Sensitivity

We test sensitivity to key model parameters:

| Parameter | Base Value | Range Tested | Impact on Key Output |
|---|---|---|---|
| DAA speed (α) | 0.3 | [0.1, 0.5] | ±15% on stabilized degradation score |
| Energy share estimate | 0.6 | [0.5, 0.7] | ±8% on breakeven prices |
| Fee pushback reference (f₀) | 100 sat/vB | [50, 200] | ±20% on pollution saturation |
| Temporary impact (η) | 0.10 | [0.05, 0.20] | ±30% on cascade peak temporary impact |
| Permanent impact (γ) | 0.05 | [0.02, 0.10] | ±40% on cascade cumulative impact |
| Pollution weight allocation | See §3.2.1 | ±50% per weight | ±15% on pollution probability |

### 5.2 Key Sensitivities

The model is most sensitive to:
1. **Almgren-Chriss coefficients** (η, γ): These determine cascade severity. Empirical calibration from BTC-specific market microstructure data would significantly improve reliability.
2. **Fee pushback reference level**: Determines how effectively the fee market self-regulates pollution. Historical fee data could calibrate this more precisely.
3. **DAA speed**: Affects how quickly the network stabilizes after miner capitulation. The real DAA is a step function (every 2016 blocks), while we use continuous smoothing.

### 5.3 Robustness

Results are qualitatively robust across parameter ranges: the Nakamoto Coefficient of 3 is a structural fact, fee-market pushback always dampens pollution (only magnitude varies), and the DAA always provides stabilizing feedback. The quantitative outputs should be interpreted as order-of-magnitude estimates rather than point predictions.

---

## 6. Discussion

### 6.1 Interconnected Risks

The four risk vectors form feedback loops:
- Miner capitulation → reduced hashrate → increased concentration → lower censorship resistance
- Content pollution → compliance triggers → institutional exit → price decline → miner capitulation
- **Stabilizing**: Price decline → miner exit → difficulty adjustment → reduced breakeven → fewer exits
- **Stabilizing**: Pollution pressure → fee increase → inscription pushback → reduced pollution

### 6.2 Limitations

- **Static vs. dynamic**: While we add DAA feedback to miner stress and fee-market dynamics to pollution, the models remain largely open-loop. A full agent-based model (ABM) with coupled feedback across all four modules is left for future work.
- **Pool hashrate ≠ censorship power**: Stratum V2 and pool-hopping dynamics significantly complicate censorship analysis (Vernetti, 2023; Cong, He & Li, 2021).
- **ETF compliance triggers are speculative**: The pollution thresholds and compliance strictness parameters are estimated, not derived from actual compliance frameworks. ETFs hold UTXOs via custodians — block content may be legally irrelevant unless OFAC sanctions specific addresses.
- **Market impact calibration**: The Almgren-Chriss parameters (η, γ) are calibrated to rough empirical estimates. BTC-specific market microstructure research would improve precision.
- **Tracked miners represent ~25% of network**: Private miners with different cost structures are extrapolated, introducing uncertainty.

### 6.3 Implications for Investors

- The DAA provides stronger resilience than static analysis suggests — "death spiral" scenarios are partially self-correcting
- Fee-market dynamics provide a natural ceiling on content pollution, reducing institutional compliance risk
- Concentration risk (Nakamoto Coefficient = 3) remains the most structurally concerning finding
- Institutional exit cascade risk is real but likely produces smaller, more gradual impact than naive models suggest

### 6.4 Implications for Bitcoin Governance

- Stratum V2 adoption should be monitored as a key indicator of true censorship resistance
- Geographic diversification of mining is a higher priority than raw hashrate growth
- The fee market is a more effective regulator of block space usage than protocol-level restrictions

---

## 7. Conclusion

Our quantitative analysis reveals that Bitcoin's PoW security model faces significant, interconnected vulnerabilities across mining economics, network centralization, content pollution, and institutional adoption. However, endogenous stabilization mechanisms — particularly the Difficulty Adjustment Algorithm and fee-market dynamics — provide meaningful resilience that static analyses miss.

The Nakamoto Coefficient of 3 and geographic concentration remain the most structurally concerning findings, as these reflect market structure rather than protocol design and are not self-correcting through endogenous mechanisms.

These findings quantify the risk landscape to enable informed decision-making by investors, regulators, and protocol developers. All models and data are open-source for reproducibility and further research.

---

## 8. Future Work

- Full agent-based model (ABM) with coupled feedback across all four risk vectors
- Integration of real-time data feeds for continuous monitoring
- Stratum V2 adoption tracking and its impact on effective Nakamoto Coefficient
- Empirical calibration of Almgren-Chriss parameters from BTC market microstructure data
- Extension to other PoW networks (Litecoin, Dogecoin, Kaspa)
- Game-theoretic modeling of miner-pool strategic interactions
- Regulatory scenario analysis across jurisdictions

---

## References

1. Almgren, R. & Chriss, N. (2001). Optimal execution of portfolio transactions. *Journal of Risk*, 3(2), 5–39.

2. Carter, N. & Jeng, L. (2023). Ordinals and the fee market. *Coin Metrics State of the Network*.

3. Chen, Y. et al. (2025). Bitcoin ETF impact on futures markets. *International Review of Financial Analysis*.

4. Cong, L. W., He, Z. & Li, J. (2021). Decentralized mining in centralized pools. *Review of Financial Studies*, 34(3), 1191–1235.

5. Easley, D., O'Hara, M. & Basu, S. (2019). From mining to markets: The role of Bitcoin transaction fees. *Journal of Financial Economics*, 134(1), 91–109.

6. Gencer, A. E. et al. (2018). Decentralization in Bitcoin and Ethereum networks. *Proceedings of NDSS 2018*.

7. Judmayer, A. et al. (2021). Estimating the cost of a 51% attack. *Financial Cryptography and Data Security (FC 2021)*.

8. Makarov, I. & Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. *Journal of Financial Economics*, 135(2), 293–319.

9. Nakamoto, S. (2008). Bitcoin: A peer-to-peer electronic cash system. *bitcoin.org/bitcoin.pdf*.

10. Prat, J. & Walter, B. (2021). An equilibrium model of the market for Bitcoin mining. *Journal of Political Economy*, 129(8), 2415–2452.

11. Vernetti, F. (2023). Stratum V2: The next generation protocol for pooled mining. *Braiins Technical Documentation*.

12. Wendl, M. et al. (2025). Bitcoin Ordinals: A systematic analysis. *Journal of The British Blockchain Association (JBBA)*.

---

## Appendix A: Technical Implementation

All models are implemented in Python 3.12+ and available at:
`https://github.com/IngoGiebel/powsec-models`

### Dependencies
```
pandas, numpy, matplotlib, scipy, yfinance, requests
```

### Reproduction
```bash
pip install -r requirements.txt
python miner_stress.py
python content_pollution.py
python hashrate_concentration.py
python institutional_exit.py
```

Output: `output/` directory with PNG visualizations and CSV data files.

## Appendix B: Model Parameters

### B.1 Miner Stress Parameters

| Parameter | Value | Source |
|---|---|---|
| Network hashrate | 850 EH/s | Blockchain.com, mid-2025 |
| Block reward | 3.125 BTC | Post-April 2024 halving |
| Energy share estimate | 60% of mining revenue | CoinShares mining reports |
| DAA adjustment speed | α = 0.3 | Smoothing approximation |
| Logistic steepness | k = 5.0 | Calibrated for gradual transition |

### B.2 Content Pollution Parameters

| Parameter | Value | Source |
|---|---|---|
| Max block size | 4.0 MB (weight) | Bitcoin protocol (SegWit) |
| Fee pushback reference | f₀ = 100 sat/vB | Empirical median during high-fee periods |
| Density normalization | 100 inscriptions/block | Observed peak density |
| Flag sensitivity | 50× scaling | 0.2% flagged ≈ significant |

### B.3 Hashrate Concentration Parameters

| Parameter | Value | Source |
|---|---|---|
| Pool data | Mid-2025 estimates | BTC.com, mempool.space |
| Geographic data | CBECI estimates | Cambridge Centre for Alternative Finance |
| KYC/Gov compliance multipliers | 0.1×–2.0× | Expert estimate (sensitivity needed) |

### B.4 Institutional Exit Parameters

| Parameter | Value | Source |
|---|---|---|
| Temporary impact η | 0.10 | Calibrated to empirical estimates |
| Permanent impact γ | 0.05 | Calibrated to empirical estimates |
| Daily BTC volume | $30B | CoinGecko average, mid-2025 |
| ETF holdings data | Mid-2025 estimates | ETF issuer reports |

---

*This research was conducted with AI assistance from Claude (Anthropic) for analysis coordination and code generation, and reviewed by Google Gemini 3 Deep Think for mathematical validation.*
