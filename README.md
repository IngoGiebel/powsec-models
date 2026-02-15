# PoW Security Models (`powsec-models`)

Quantitative models analyzing Bitcoin's Proof-of-Work security from multiple angles: miner economics, content pollution, hashrate concentration, and institutional compliance risk.

## Modules

| Module | Description | Key Output |
|--------|-------------|------------|
| `miner_stress.py` | Miner Capitulation & Network Security Degradation | Break-even prices, capitulation probabilities, security degradation score |
| `content_pollution.py` | Blockchain Pollution Probability Model | Toxic block probability, saturation curve, fee displacement ratio |
| `hashrate_concentration.py` | Censorship Risk Model | Nakamoto Coefficient, Censorship-Resistance Score, censorship cost estimates |
| `institutional_exit.py` | ETF/Institutional Compliance Model | Time-to-trigger, cascade simulation, BTC price impact |

## Quick Start

Each module is standalone — run directly:

```bash
python miner_stress.py
python content_pollution.py
python hashrate_concentration.py
python institutional_exit.py
```

Results (plots + CSV) are saved to `output/`.

## Requirements

```
pandas
numpy
matplotlib
scipy
requests
```

Install: `pip install -r requirements.txt`

## Architecture

All modules follow the same pattern:
- **Dataclasses** for structured input (type-hinted, documented)
- **Core functions** for analysis (pure, testable)
- **Visualization** via matplotlib (saved to `output/`)
- **CSV export** for downstream use
- **`if __name__ == "__main__"`** with formatted console output

## Model Summaries

### 1. Miner Stress (`miner_stress.py`)
Models individual miner capitulation under BTC price crashes using real Q3 2025 financials. Logistic model combining energy break-even, debt pressure, and cash runway.

### 2. Content Pollution (`content_pollution.py`)
Tracks Ordinals/inscription growth and estimates the probability that random blocks contain "toxic" content. Fits a logistic saturation curve to project when institutional thresholds are breached.

### 3. Hashrate Concentration (`hashrate_concentration.py`)
Analyzes mining pool and entity concentration. Computes Nakamoto Coefficient, HHI, geographic risk, and estimates the dollar cost of achieving transaction censorship at various hashrate thresholds.

### 4. Institutional Exit (`institutional_exit.py`)
Models when ETFs and institutional holders hit compliance triggers due to rising pollution rates. Simulates a cascade of forced exits and the resulting BTC price impact (Almgren-Chriss optimal execution model with separate temporary and permanent impact).

## Output Files

After running all modules, `output/` contains:
- `stress_test.png` + `stress_test_data.csv`
- `content_pollution.png` + `content_pollution_data.csv`
- `hashrate_concentration.png` + `hashrate_concentration_data.csv`
- `institutional_exit.png` + `institutional_exit_risk.csv` + `institutional_exit_cascade.csv`

## License

Internal research — Inanna ⚔️ / Alpha Auriga
