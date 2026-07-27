# UK Small/Mid-Cap Takeover Screener

A proprietary screening model that ranks UK-listed small and mid-cap companies on takeover likelihood, built to replicate the kind of target-generation screen a boutique M&A or PE team would run internally.

## The problem

Deal teams need a systematic way to generate a target pipeline rather than relying purely on banker pitches or ad hoc idea generation. This project builds that screen from first principles: what actually makes a listed company an attractive, realistic takeover candidate, and how do you turn that into a repeatable, defensible score.

## Methodology

The model scores each company 0–100 on five weighted factors:

| Factor | Weight | Rationale | Metric |
|---|---|---|---|
| Valuation discount | 25% | Cheap relative to sector peers is the starting point for any bid case | EV/EBITDA vs. sector average |
| Leverage headroom | 20% | Low existing leverage means an acquirer can layer on debt (strategic or LBO) without an unrealistic capital structure | Net Debt/EBITDA |
| Ownership structure | 20% | High free float and fragmented ownership make stake-building and board pressure realistic; concentrated/founder-controlled ownership makes a bid far harder regardless of valuation | Free float % |
| Margin quality | 20% | Distinguishes a genuine mispricing from a value trap — cheap AND operationally sound is the target profile, not just cheap | EBITDA margin vs. sector average |
| Sector M&A heat | 15% | Recent comparable transactions signal active buyer appetite and realistic exit multiples in the sector | Qualitative 0–100 signal from recent deal activity |

Each factor is calculated relative to sector peers, not on an absolute basis — a 7x EV/EBITDA company isn't automatically cheap; it's only cheap if its sector trades at 11x. This peer-relative design is the core methodological decision in the model and the one most worth defending in an interview.

Factors are combined into a single weighted composite score. Weights are adjustable in the interactive tool, which lets a user see how the ranking shifts under a different investment thesis.

## What's included

- **`index.html`** — interactive front-end. Adjustable factor weights, ranked table, and a drill-down detail view per company showing the factor-level breakdown and a qualitative rationale.
- **`screener_model.py`** — the production-grade version of the scoring logic, written to pull live fundamentals via `yfinance` rather than the static snapshot used in the demo. Structured so the data source is a drop-in placeholder for a Bloomberg, FactSet, or Capital IQ feed in a real institutional setting.
- **This README** — methodology documentation.

## Data and limitations

The interactive demo uses an indicative dataset built from public market commentary (AJ Bell, Saxo Markets, MoneyWeek) as of mid-2026, not a live data feed. This is a deliberate scoping choice: live financial data sits behind institutional paywalls. The `screener_model.py` script demonstrates how the same logic would run against a real feed.

The sector M&A heat factor is currently assigned qualitatively based on known recent situations (e.g. Auction Technology Group's live defense against repeated bids from FitzWalter Capital, Halfords' history of takeover speculation). In production this would be derived systematically from a deal-tracking database rather than assigned by hand.

## Possible extensions

- Automated sector M&A heat scoring from a deals database rather than manual assignment
- Backtesting: apply the model to a historical snapshot and check whether companies that scored highly were subsequently the subject of real bids
- Expansion beyond the current 9-company watchlist to the full FTSE Small Cap and AIM universe
- A simple bid-premium estimator layered on top of the likelihood score

## Author

Aaron Kark — built as an independent project to develop and demonstrate applied M&A screening methodology.