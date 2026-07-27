"""
UK Small/Mid-Cap Takeover Likelihood Screener
-----------------------------------------------
Production version of the scoring model demonstrated in the interactive
front-end (index.html). This script defines the data schema, scoring
methodology, and pulls live fundamentals via yfinance as a free-tier
proxy for a Bloomberg/FactSet/Capital IQ feed.

Author: Aaron Kark
"""

import yfinance as yf
import pandas as pd

UNIVERSE = [
    "ATG.L",   # Auction Technology Group
    "HFD.L",   # Halfords Group
    "PAG.L",   # Paragon Banking Group
    "PHNX.L",  # Phoenix Group Holdings
    "WIX.L",   # Wickes Group
    "MER.L",   # Mears Group
    "WG..L",   # Wood Group
    "DFS.L",   # DFS Furniture
    "GFTU.L",  # Grafton Group
]

SECTOR_MAP = {
    "ATG.L": "Business Services",
    "HFD.L": "Retail",
    "PAG.L": "Financial Services",
    "PHNX.L": "Insurance",
    "WIX.L": "Retail",
    "MER.L": "Support Services",
    "WG..L": "Energy Services",
    "DFS.L": "Retail",
    "GFTU.L": "Building Materials",
}

WEIGHTS = {
    "valuation": 0.25,
    "leverage": 0.20,
    "ownership": 0.20,
    "margin": 0.20,
    "mna_heat": 0.15,
}


def fetch_fundamentals(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info

    ev = info.get("enterpriseValue")
    ebitda = info.get("ebitda")
    total_debt = info.get("totalDebt", 0)
    cash = info.get("totalCash", 0)
    held_by_insiders = info.get("heldPercentInsiders", 0)
    revenue = info.get("totalRevenue")

    ev_ebitda = (ev / ebitda) if ev and ebitda else None
    net_debt_ebitda = ((total_debt - cash) / ebitda) if ebitda else None
    ebitda_margin = (ebitda / revenue * 100) if ebitda and revenue else None
    free_float = (1 - held_by_insiders) * 100 if held_by_insiders is not None else None

    return {
        "ticker": ticker,
        "name": info.get("shortName"),
        "sector": SECTOR_MAP.get(ticker, "Unclassified"),
        "ev_ebitda": ev_ebitda,
        "net_debt_ebitda": net_debt_ebitda,
        "ebitda_margin": ebitda_margin,
        "free_float": free_float,
    }


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def score_universe(rows: list[dict], mna_heat_overrides: dict) -> pd.DataFrame:
    df = pd.DataFrame(rows)

    sector_avg_ev_ebitda = df.groupby("sector")["ev_ebitda"].transform("mean")
    sector_avg_margin = df.groupby("sector")["ebitda_margin"].transform("mean")

    df["valuation_score"] = (
        50 + ((sector_avg_ev_ebitda - df["ev_ebitda"]) / sector_avg_ev_ebitda) * 150
    ).apply(clamp)

    df["leverage_score"] = (100 - df["net_debt_ebitda"] * 20).apply(clamp)

    df["ownership_score"] = df["free_float"].apply(clamp)

    df["margin_score"] = (
        50 + (df["ebitda_margin"] - sector_avg_margin) * 5
    ).apply(clamp)

    df["mna_heat_score"] = df["ticker"].map(mna_heat_overrides).fillna(50).apply(clamp)

    df["composite_score"] = (
        df["valuation_score"] * WEIGHTS["valuation"]
        + df["leverage_score"] * WEIGHTS["leverage"]
        + df["ownership_score"] * WEIGHTS["ownership"]
        + df["margin_score"] * WEIGHTS["margin"]
        + df["mna_heat_score"] * WEIGHTS["mna_heat"]
    )

    return df.sort_values("composite_score", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    mna_heat_overrides = {
        "ATG.L": 97, "HFD.L": 85, "PAG.L": 72, "PHNX.L": 70,
        "WIX.L": 52, "MER.L": 48, "WG..L": 60, "DFS.L": 40, "GFTU.L": 45,
    }

    rows = [fetch_fundamentals(t) for t in UNIVERSE]
    ranked = score_universe(rows, mna_heat_overrides)

    print(ranked[["name", "ticker", "sector", "composite_score"]].to_string(index=False))