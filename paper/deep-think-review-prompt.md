# Deep Think Review Prompt — PoW Security Models

Kopiere den gesamten Inhalt dieses Prompts in Gemini 3 Deep Think.

---

## PROMPT START

You are reviewing a quantitative research project on Bitcoin Proof-of-Work security risks. The project contains 4 Python simulation models (2,335 lines total). I need a rigorous, PhD-level review.

### Context
This project models systemic risks in Bitcoin's PoW security through four interconnected simulations:
1. **Miner Capitulation Stress Test** — breakeven prices, capitulation probabilities under price drops
2. **Blockchain Content Pollution** — Ordinals/inscription saturation modeling
3. **Hashrate Concentration** — Nakamoto coefficient, censorship resistance, attack costs
4. **Institutional Exit Cascade** — ETF compliance-driven selling cascades

### What I need from you

**A. Mathematical Review**
- Are the mathematical models (logistic sigmoid for capitulation, saturation curves for pollution, HHI for concentration) appropriate choices? What alternatives exist?
- Check the formulas for correctness — any edge cases, numerical instability, or boundary conditions missed?
- Is the cascade simulation methodology sound? Are the feedback loops modeled correctly?

**B. Assumptions Audit**
- List ALL implicit and explicit assumptions in each model
- Rate each assumption: (1) well-justified, (2) reasonable but needs citation, (3) questionable, (4) likely wrong
- Suggest empirical data sources to validate questionable assumptions

**C. Methodology Critique**
- What are the strongest and weakest aspects of each model?
- What important factors are NOT modeled but should be?
- How would you improve the models if you had 3 more months?

**D. Literature Gaps**
- What key academic papers should be cited for each model?
- Are there existing frameworks that do similar analysis? How does this compare?
- Suggest 10-15 essential references for the paper bibliography

**E. Results Validation**
Based on the model outputs:
- Miner breakeven: $69k-$104k range — plausible?
- Nakamoto Coefficient of 3 — consistent with current data?
- Content pollution saturation at 85.5% — reasonable?
- Institutional cascade: -45% over 14 months — realistic scenario?

**F. Paper Quality**
- Is this publishable as a working paper / preprint?
- What would elevate it to conference-paper quality?
- Suggest the most appropriate venues (arXiv categories, conferences, journals)

### Source Code

Please analyze all four modules below:

---

#### MODULE 1: miner_stress.py

```python
[PASTE CONTENT OF miner_stress.py HERE]
```

---

#### MODULE 2: content_pollution.py

```python
[PASTE CONTENT OF content_pollution.py HERE]
```

---

#### MODULE 3: hashrate_concentration.py

```python
[PASTE CONTENT OF hashrate_concentration.py HERE]
```

---

#### MODULE 4: institutional_exit.py

```python
[PASTE CONTENT OF institutional_exit.py HERE]
```

---

#### PAPER DRAFT (structure with current results)

```markdown
[PASTE CONTENT OF PAPER.md HERE]
```

---

Please provide a structured review addressing sections A through F. Be rigorous — treat this as a peer review for a top-tier venue. Point out every weakness, but also acknowledge strengths.

## PROMPT END

---

## Anleitung für Ingo

1. Öffne https://gemini.google.com/ und wähle **Deep Think** Modus
2. Kopiere alles zwischen "PROMPT START" und "PROMPT END"
3. Ersetze die `[PASTE ...]` Platzhalter mit dem tatsächlichen Dateiinhalt:
   - `cat finance/inanna/models/powsec-models/miner_stress.py`
   - `cat finance/inanna/models/powsec-models/content_pollution.py`
   - `cat finance/inanna/models/powsec-models/hashrate_concentration.py`
   - `cat finance/inanna/models/powsec-models/institutional_exit.py`
   - `cat finance/inanna/models/powsec-models/paper/PAPER.md`
4. Sende den Prompt — Deep Think wird einige Minuten brauchen
5. Kopiere die Antwort und schick sie mir (oder speichere sie als Datei)

**Alternativ:** Sag mir Bescheid und ich generiere einen fertigen Prompt mit eingebettetem Code, den du nur noch copy-pasten musst.
