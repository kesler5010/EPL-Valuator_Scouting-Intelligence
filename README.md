# ⚽ EPL Valuator: Scouting Intelligence

## Description
An advanced football scouting and squad-building platform built with **Python** and **Streamlit**. This project applies **Industrial & Systems Engineering (ISE)** principles to optimize team recruitment through mathematical modeling and financial constraints, converting raw technical data into usable insights to determine the value of players.

## Key Features
1. *Draft a Team:* Generates the highest-utility XI for 4-4-2 and 4-2-3-1 tactical systems based on user's wage input
2. *Budget Optimization Engine:* An iterative heuristic loop that replaces "luxury" assets with high-value alternatives to meet strict wage caps.
3. *Specialist Selection Logic:* Double Pivot (DM) Filter: Strictly requires a 1.1+ defensive multiplier. 
    *Specialist Priority:* 1.2 multiplier "Specialists" receive a 15% selection boost to ensure tactical fit over raw "Elite Generalists" in the DM roles in the 4-2-3-1 Squad Builder
1. Visual Analytics:
1. *Search Player*
    1. Displays Positional Rank, Value Score, Weekly Wage and Full Efficiency Profile when users search for specific players
2. *Compare Players*
    1. Allow users to compare 2 players in the same position with position-relevant metrics, `Green` is Better, `Grey` is equal, `Red` is Worse
    2. Radar Charts to view player profile overlap
3. *Value Graphs*
    1. Interactive regression analysis graph for each position
4. *Leaderboards* 
    1. Information tables ranking the "Top 10 Bargains" using a custom Value-Gap surplus metric.
5. *Draft a Team*
    1. Plotly Tactical Board for clearer visualization
    2. Identifying cost of "Elite XI" for both formation choices as a benchmark for users
6. *Metric Glossary*
    1. Allow users to understand the meaning of metrics used

## Technical Methodology
1. Performance Modeling (The "Final Score")
**The Final_Score is a positional utility function. It is calculated by taking a *weighted summation of normalized technical metrics (x_{norm}) and applying tactical multipliers (M):***
$$\text{Final Score} = \left( \sum_{i=1}^{n} w_i \cdot x_{norm,i} \right) \times M_{availability} \times M_{age} \times M_{defensive}$$
    Logic: Weights($w_i$) are assigned based on `positional priority.` Multipliers are used to "penalize" players with low availability or reward them for "peak-age" performance, ensuring the model picks reliable, long-term assets rather than one-season wonders.($M_{defensive}$ is only for midfielders, rewarding defensive midfielders for fairer comparison with attacking midfielders)

2. Feature Scaling (Min-Max Normalization)
**To ensure an "apples-to-apples" comparison between disparate units (e.g., Goals vs. Wages), we employ Min-Max scaling:**
$$x_{norm} = \left( \frac{x - x_{min}}{x_{max} - x_{min}} \right) \times 100$$
    Positive Metrics: Higher raw values (e.g. Goals, Assists) map toward 100.
    Inverse Metrics: Lower raw values (e.g., Goals Against, Cards, Age) map toward 100 to represent higher efficiency.

3. The Value Baseline (Linear Regression)
**To determine if a player is "worth their wage," the system establishes a positional market baseline using Simple Linear Regression. We model the relationship between financial investment (Weekly Wage) and output (Final Score):**
$$Expected\ Score = \beta_0 + \beta_1 \cdot (Weekly\ Wage)$$
    $\beta_0$ (Intercept): The baseline performance expected from a minimum-wage player.
    $\beta_1$ (Coefficient): The "Performance-per-Pound" rate for that specific position.

4. Value-Gap Analysis (ROI Determination)
**The Value Gap is the residual value between a player’s actual performance and the market's expected performance:**
$$Value\ Gap = Final\ Score - Expected\ Score$$
    Surplus (Above the Line): Players with a positive Value Gap are "Bargains." They provide elite output for a below-market-rate salary.
    Deficit (Below the Line): Players with a negative Value Gap are "Underperformers." Their financial cost exceeds their statistical contribution.

## Tech Stack
Language: Python 3.14.3
Framework: Streamlit
Data Science: Pandas, NumPy
Visualization: Plotly (Radar, Scatter, Coordinate Mapping)

## Installation
1. Clone the Repo: git clone https://github.com/kesler5010/EPL-Valuator_Scouting-Intelligence.git
2. Install Dependencies: pip install -r requirements.txt
3. Launch App: streamlit run dashboard.py