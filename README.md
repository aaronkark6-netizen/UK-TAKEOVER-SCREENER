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

Factors are combined into a single weighted composite score. Weights are adjustable in the interactive tool, which lets a user see how the ranking shifts under a different investment thesis (e.g. weighting ownership structure more heavily reflects a strategy focused on stake-building activism rather than clean take-private deals).

## What's included

- **`index.html`** — interactive front-end. Adjustable factor weights, a searchable/filterable ranked table of 15 live candidates, and a drill-down detail view per company showing the factor-level breakdown and a qualitative rationale. CSV export for the current ranking.
- **`screener_model.py`** — the production-grade version of the scoring logic, written to pull live fundamentals via `yfinance` rather than the static snapshot used in the demo. Structured so the data source (`yfinance`) is a drop-in placeholder for a Bloomberg, FactSet, or Capital IQ feed in a real institutional setting.
- **This README** — methodology documentation.

## Validation cases (lightweight backtest)

Beyond the live candidate list, the tool includes five companies that have already been acquired or agreed to takeover terms during 2026: Ricardo (69% premium bid from WSP), Assura (KKR proposal at a 38% premium), Gooch & Housego (£346m private equity acquisition), Advanced Medical Solutions Group (£659m bid from H.B. Fuller), and Ramsdens Holdings (£206m acquisition by FirstCash).

Each is shown with its reconstructed pre-deal score and the actual outcome, as a rough check on whether the methodology would have flagged genuine situations in advance. This is a lightweight, retrospective sanity check rather than a rigorous backtest — pre-deal multiples are reconstructed estimates based on reported premiums, not verified point-in-time data — but it's a meaningfully stronger form of validation than the model existing in isolation.

## Data and limitations

The interactive demo uses an indicative dataset built from public market commentary (AJ Bell, Saxo Markets, MoneyWeek, Proactive Investors, ii.co.uk) as of mid-2026, not a live data feed. This is a deliberate scoping choice: live financial data (Bloomberg/FactSet/Capital IQ) sits behind institutional paywalls, and free alternatives like `yfinance` are unreliable for UK-listed tickers at production quality. The `screener_model.py` script demonstrates how the same logic would run against a real feed.

The sector M&A heat factor is currently assigned qualitatively based on known recent situations (e.g. Auction Technology Group's live defense against repeated bids from FitzWalter Capital, Halfords' history of takeover speculation). In production this would be derived systematically from a deal-tracking database rather than assigned by hand.

## Possible extensions

- Automated sector M&A heat scoring from a deals database (Mergermarket, GlobalData) rather than manual assignment
- A more rigorous backtest using verified point-in-time fundamentals rather than reconstructed estimates
- Expansion beyond the current 20-company watchlist to the full FTSE Small Cap and AIM universe
- A simple bid-premium estimator layered on top of the likelihood score, using historical average premiums by sector and the validation-case data already collected

## Author

Aaron Kark — built as an independent project to develop and demonstrate applied M&A screening methodology.
