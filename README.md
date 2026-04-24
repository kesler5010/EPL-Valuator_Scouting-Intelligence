# EPL Valuator: Scouting Intelligence

> A Premier League player scouting and squad-building platform that applies **Industrial & Systems Engineering (ISE)** principles to optimize team recruitment through mathematical modeling and financial constraints.

---

## Overview

The EPL Valuator converts raw technical data into quantifiable player value scores, enabling data-driven recruitment decisions within strict wage budgets. The system scores every outfield player and goalkeeper across the Premier League (with a minimum 800 minutes played threshold), identifies market inefficiencies, and drafts the highest-utility XI for two tactical formations.

---

## Features

### Squad Builder
- Generates the highest-utility XI for **4-4-2** and **4-2-3-1** tactical systems based on a user-defined wage cap (£250,000 - £2,000,000)
- **Budget Optimization Engine:** An iterative heuristic loop that replaces over-priced assets with high-value alternatives to satisfy financial constraints
- **Specialist Selection Logic:** The Double Pivot (DM) role strictly requires a 1.1+ defensive multiplier; players with a 1.2+ "Specialist" rating receive a 15% selection boost to ensure tactical fit over raw score in DM positions

### Analytics Pages
| Page | Description |
|---|---|
| **Search Player** | Returns positional rank, value score, weekly wage, and full efficiency profile for any player |
| **Compare Players** | Side-by-side comparison of two players at the same position with color-coded metric deltas and radar chart overlap |
| **Value Graphs** | Interactive regression scatter plots for each position showing performance vs. wage |
| **Leaderboards** | Top 10 Bargains ranked by Value-Gap surplus |
| **Draft a Team** | Plotly tactical board visualization with Elite XI cost benchmarks for both formations |
| **Metric Glossary** | Definitions for all metrics used throughout the platform |

---

## Technical Methodology

### 1. Performance Modeling — The Final Score

The **Final Score** is a positional utility function: a weighted summation of normalized technical metrics with tactical multipliers applied.

$$\text{Final Score} = \left( \sum_{i=1}^{n} w_i \cdot x_{norm,i} \right) \times M_{availability} \times M_{age} \times M_{defensive}$$

- **Weights ($w_i$):** Assigned by positional priority (e.g., Goals weighted higher for forwards, defensive actions included for defenders/midfielders)
- **$M_{availability}$:** Penalizes players with low minutes to favor reliable, less injury-prone, long-term assets
- **$M_{age}$:** Rewards peak-age performance (Younger players are rated more highly compared to players past their prime age)
- **$M_{defensive}$:** Applied only to midfielders to reward defensive volume, enabling fairer comparison between DMs and AMs

### 2. Feature Scaling — Min-Max Normalization

All metrics are scaled to a common [0, 100] range before summation to ensure unit-agnostic comparison (e.g., Goals vs. Wages).

$$x_{norm} = \frac{x - x_{min}}{x_{max} - x_{min}} \times 100$$

- **Positive metrics** (Goals, Assists): higher raw value → higher normalized score
- **Inverse metrics** (Goals Against, Cards, Age): lower raw value → higher normalized score

### 3. The Value Baseline — Linear Regression

To determine whether a player is worth their wage, the system establishes a positional market baseline using Simple Linear Regression, modeling the relationship between financial investment and output.

$$\text{Expected Score} = \beta_0 + \beta_1 \cdot (\text{Weekly Wage})$$

- **$\beta_0$ (Intercept):** Baseline performance expected from a minimum-wage player
- **$\beta_1$ (Coefficient):** Performance-per-pound rate for that specific position

### 4. Value-Gap Analysis — ROI Determination

The **Value Gap** is the residual between a player's actual score and the market's expected score at their wage level.

$$\text{Value Gap} = \text{Final Score} - \text{Expected Score}$$

| Result | Label | Interpretation |
|---|---|---|
| Positive Value Gap | **Bargain** | Elite output at a below-market salary |
| Negative Value Gap | **Underperformer** | Financial cost exceeds statistical contribution |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14.3 |
| Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly (Radar, Scatter, Coordinate Mapping) |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/kesler5010/EPL-Valuator_Scouting-Intelligence.git
cd EPL-Valuator_Scouting-Intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
streamlit run dashboard.py
```
