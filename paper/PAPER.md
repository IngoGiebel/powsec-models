# Quantitative Risk Assessment of Bitcoin's Proof-of-Work Security Model

**Authors:** Ingo Giebel¹, with AI-assisted analysis by Dione 🌙 & Inanna ⚔️  
**Affiliation:** ¹ Heinrich-Heine-Universität Düsseldorf, B.Sc. Quantitative Biology  
**Date:** February 2026  
**Repository:** [github.com/IngoGiebel/powsec-models](https://github.com/IngoGiebel/powsec-models)  
**License:** MIT  

---

## Abstract

We present a quantitative framework for assessing systemic risks in Bitcoin's Proof-of-Work (PoW) security model through four interconnected simulation models. Our analysis examines (1) miner capitulation dynamics under price stress, (2) blockchain content pollution via Ordinals and OP_RETURN abuse, (3) hashrate concentration and censorship resistance, and (4) institutional exit cascades triggered by compliance concerns. Results indicate critical vulnerabilities: a Nakamoto Coefficient of only 3, content pollution approaching 85% saturation, and a potential 45% BTC price decline in an institutional exit cascade scenario. These findings suggest that Bitcoin's security guarantees may be more fragile than commonly assumed.

**Keywords:** Bitcoin, Proof-of-Work, mining economics, hashrate concentration, censorship resistance, institutional risk, content pollution, Ordinals, ETF compliance

---

## 1. Introduction

### 1.1 Motivation

Bitcoin's security model fundamentally relies on the economic incentives of Proof-of-Work mining. While the theoretical foundations are well-established (Nakamoto, 2008), the practical security landscape has evolved significantly with the emergence of industrial-scale mining operations, Bitcoin ETFs holding >5% of circulating supply, and novel block space usage patterns such as Ordinals inscriptions.

### 1.2 Research Questions

1. At what BTC price levels do major publicly traded miners face capitulation, and what are the cascading effects on network hashrate?
2. How rapidly is blockchain content pollution reaching institutional concern thresholds?
3. What is the true censorship resistance of the Bitcoin network given current hashrate concentration?
4. Could compliance-driven institutional exits create self-reinforcing price cascades?

### 1.3 Contributions

- Four open-source Python models with reproducible simulations
- Quantitative estimates for miner breakeven prices using real financial data
- A novel saturation model for blockchain content pollution
- Censorship cost estimation framework based on pool economics
- First systematic cascade simulation of ETF compliance-driven exits

---

## 2. Related Work

### 2.1 Mining Economics
- Kroll et al. (2013): Economics of Bitcoin mining
- Easley et al. (2019): Mining incentive compatibility
- [TODO: Add recent 2024-2026 literature on post-halving mining economics]

### 2.2 Network Concentration
- Gencer et al. (2018): Decentralization in Bitcoin
- [TODO: Add updated studies on mining pool concentration]

### 2.3 Content Pollution & Ordinals
- [TODO: Literature on Ordinals impact, block space economics]

### 2.4 Institutional Adoption Risks
- [TODO: ETF compliance literature, regulatory framework analysis]

---

## 3. Methodology

### 3.1 Miner Capitulation Stress Test (`miner_stress.py`)

#### 3.1.1 Model Description
We model miner capitulation probability as a function of BTC price relative to each miner's breakeven cost, incorporating:
- **Breakeven price calculation** based on energy costs, hashrate contribution, and operational expenses
- **Financial health indicators**: EBITDA margin, debt-to-cash ratio
- **Logistic sigmoid function** for capitulation probability
- **Hashrate degradation** modeling as miners exit

#### 3.1.2 Data Sources
- Yahoo Finance: Publicly traded miner financials (WULF, CIFR, CORZ, MARA, RIOT, CLSK)
- Blockchain.com: Network hashrate and difficulty data

#### 3.1.3 Key Assumptions
- [TODO: Document all model assumptions and their justifications]

### 3.2 Blockchain Content Pollution (`content_pollution.py`)

#### 3.2.1 Model Description
Logistic saturation curve fitted to historical data on:
- Block utilization rates
- Ordinals inscription frequency
- OP_RETURN usage patterns
- Fee displacement effects

#### 3.2.2 Saturation Model
```
P(t) = K / (1 + e^(-r(t - t₀)))
```
Where K = capacity asymptote, r = growth rate, t₀ = midpoint

### 3.3 Hashrate Concentration Analysis (`hashrate_concentration.py`)

#### 3.3.1 Metrics
- **Nakamoto Coefficient**: Minimum entities to reach 51%
- **Herfindahl-Hirschman Index (HHI)**: Market concentration measure
- **Censorship Resistance Score** (0-100): Composite metric
- **Censorship cost estimation**: Based on pool revenue and coordination costs

#### 3.3.2 Scenario Analysis
- Baseline concentration vs. hypothetical consolidation scenarios
- Geographic risk factoring (jurisdiction-based vulnerability)

### 3.4 Institutional Exit Cascade (`institutional_exit.py`)

#### 3.4.1 Model Description
Monte Carlo-style simulation of cascading ETF exits triggered by:
- Content pollution exceeding compliance thresholds
- Regulatory pressure (jurisdiction-specific strictness)
- Contagion effects from earlier exits

#### 3.4.2 Cascade Dynamics
Each exit event reduces BTC price proportional to holdings, which increases pollution metrics and triggers further compliance reviews.

---

## 4. Results

### 4.1 Miner Capitulation

| Miner | Breakeven Price | EBITDA Margin | Debt/Cash |
|-------|----------------|---------------|-----------|
| CleanSpark (CLSK) | $68,716 | 18.8% | 1.3x |
| Core Scientific (CORZ) | $73,600 | 19.0% | 4.0x |
| Riot Platforms (RIOT) | $78,268 | -5.4% | 0.6x |
| TeraWulf (WULF) | $84,357 | -21.0% | 1.5x |
| Marathon Digital (MARA) | $92,923 | 12.4% | 4.0x |
| Cipher Mining (CIFR) | $103,569 | -13.3% | 4.0x |

**Key Finding:** At BTC $80,000, capitulation probability ranges from 45% (CleanSpark) to 93% (Cipher Mining). At $60,000, virtually all miners face capitulation (77-97%).

### 4.2 Content Pollution

- Saturation asymptote: **85.5%**
- Growth rate: 0.434 (rapid)
- 50% pollution threshold reached within ~5 months from baseline
- Ordinals-driven pollution rose from 0% (mid-2022) to >80% (early 2025)

### 4.3 Hashrate Concentration

| Metric | Value | Assessment |
|--------|-------|------------|
| Nakamoto Coefficient | 3 | Critical |
| HHI | 1,612 | Moderate concentration |
| Censorship Resistance Score | 22.4/100 | Very low |
| 51% attack cost | ~$5.9B/yr | Achievable for nation-states |

**Key Finding:** Only 3 entities (Foundry USA 30%, AntPool 18%, F2Pool 12%) control >50% of hashrate.

### 4.4 Institutional Exit Cascade

| Timeline | Event | Cumulative BTC Sold | Price Impact |
|----------|-------|---------------------|-------------|
| Month 5 | BTCE exit | 20,000 BTC | -3.9% |
| Month 7 | BTCC + ABTC | 70,000 BTC | -9.6% |
| Month 9 | Fidelity (FBTC) | 275,000 BTC | -20.3% |
| Month 11 | BlackRock (IBIT) + others | 865,500 BTC | -35.3% |
| Month 14 | Grayscale (GBTC) | 1,150,500 BTC | -45.2% |

**Key Finding:** Complete institutional exit cascade results in BTC declining from $100,000 to ~$54,768 (-45.2%) over 14 months.

---

## 5. Discussion

### 5.1 Interconnected Risks
The four risk vectors are not independent — they form feedback loops:
- Miner capitulation → reduced hashrate → increased concentration → lower censorship resistance
- Content pollution → compliance triggers → institutional exit → price decline → miner capitulation

### 5.2 Limitations
- Models use simplified assumptions and historical/estimated data
- Miner financials are based on public filings with reporting lag
- Content pollution metrics are approximated from available blockchain data
- Institutional behavior models assume rational compliance-driven decisions
- [TODO: Expand limitations section]

### 5.3 Implications for Investors
- [TODO: Practical implications for portfolio positioning]

### 5.4 Implications for Bitcoin Governance
- [TODO: Protocol-level mitigation strategies]

---

## 6. Conclusion

Our quantitative analysis reveals that Bitcoin's PoW security model faces significant, interconnected vulnerabilities across mining economics, network centralization, content pollution, and institutional adoption. The Nakamoto Coefficient of 3 and censorship resistance score of 22.4/100 suggest that the network's decentralization guarantees are substantially weaker than commonly perceived.

These findings do not predict inevitable failure but rather quantify the risk landscape to enable informed decision-making by investors, regulators, and protocol developers.

---

## 7. Future Work

- Integration of real-time data feeds for continuous monitoring
- Extension to other PoW networks (Litecoin, Dogecoin, Kaspa)
- Game-theoretic modeling of miner-pool strategic interactions
- Regulatory scenario analysis across jurisdictions
- Review and validation with Gemini 3 Deep Think

---

## References

[TODO: Complete bibliography]

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

[TODO: Complete parameter tables for each model]

## Appendix C: Raw Data

[TODO: Reference to CSV outputs and data sources]

---

*This research was conducted with AI assistance from Claude Opus (Anthropic) for analysis coordination, OpenAI Codex CLI (gpt-5.3-codex) for code generation, and [pending] Google Gemini 3 Deep Think for review and validation.*
