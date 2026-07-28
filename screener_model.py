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

# ---------------------------------------------------------------------------
# 1. UNIVERSE DEFINITION
# ---------------------------------------------------------------------------
# In production this would be pulled dynamically (e.g. all FTSE Small Cap +
# AIM constituents via an index membership feed). For this prototype the
# universe is a fixed watchlist of UK small/mid-cap tickers.

# Live candidates -- companies not currently the subject of an agreed deal.
LIVE_UNIVERSE = [
    "ATG.L",   # Auction Technology Group
    "HFD.L",   # Halfords Group
    "PAG.L",   # Paragon Banking Group
    "PHNX.L",  # Phoenix Group Holdings
    "WIX.L",   # Wickes Group
    "MER.L",   # Mears Group
    "WG..L",   # Wood Group
    "DFS.L",   # DFS Furniture
    "GFTU.L",  # Grafton Group
    "EVPL.L",  # Everplay Group
    "CRW.L",   # Craneware
    "BRK.L",   # Brooks Macdonald Group
    "NET.L",   # Netcall
    "SWG.L",   # Shearwater Group
    "FLK.L",   # Fletcher King
]

# Validation cases -- companies already acquired or subject to an agreed
# takeover during 2026. Used to backtest the scoring methodology against
# real outcomes rather than only ranking still-open candidates.
RESOLVED_UNIVERSE = [
    "RCDO.L",  # Ricardo -- agreed £281m WSP offer, 69% premium
    "AGR.L",   # Assura -- recommended KKR proposal, 38% premium
    "GHH.L",   # Gooch & Housego -- acquired for £346m
    "AMS.L",   # Advanced Medical Solutions Group -- agreed £659m H.B. Fuller bid
    "RFX.L",   # Ramsdens Holdings -- acquired for £206m by FirstCash
]

UNIVERSE = LIVE_UNIVERSE + RESOLVED_UNIVERSE

# Sector mapping used to compute peer-relative valuation and margin scores.
# In production, sector peer sets would be pulled from a classification
# feed (GICS/ICB) rather than hardcoded.
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
    "EVPL.L": "Gaming / Digital Media",
    "CRW.L": "Business Services",
    "BRK.L": "Financial Services",
    "NET.L": "Technology",
    "SWG.L": "Technology",
    "FLK.L": "Real Estate Services",
    "RCDO.L": "Energy Services",
    "AGR.L": "Real Estate",
    "GHH.L": "Technology",
    "AMS.L": "Healthcare",
    "RFX.L": "Consumer Finance",
}

# Status of each ticker as of mid-2026 -- used to separate live candidates
# from validation cases in reporting.
STATUS_MAP = {t: "live" for t in LIVE_UNIVERSE}
STATUS_MAP.update({
    "RCDO.L": "agreed",
    "AGR.L": "agreed",
    "GHH.L": "completed",
    "AMS.L": "agreed",
    "RFX.L": "completed",
})

# ---------------------------------------------------------------------------
# 2. FACTOR WEIGHTS
# ---------------------------------------------------------------------------
WEIGHTS = {
    "valuation": 0.25,   # EV/EBITDA discount to sector average
    "leverage": 0.20,    # Net Debt / EBITDA headroom
    "ownership": 0.20,   # Free float as a proxy for ease of stake-building
    "margin": 0.20,      # EBITDA margin vs sector average
    "mna_heat": 0.15,    # Qualitative sector M&A activity signal (0-100)
}


def fetch_fundamentals(ticker: str) -> dict:
    """Pull core fundamentals for a single ticker via yfinance."""
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
    """
    Compute the five factor scores and the weighted composite for each
    company, using sector-relative comparisons.
    """
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
    # Qualitative sector M&A activity signal -- in production this would be
    # derived systematically (e.g. count of announced deals in the sector
    # over the trailing 12 months from a deals database), not assigned
    # manually. Kept manual here for transparency in the prototype.
    mna_heat_overrides = {
        "ATG.L": 97, "HFD.L": 85, "PAG.L": 72, "PHNX.L": 70,
        "WIX.L": 52, "MER.L": 48, "WG..L": 60, "DFS.L": 40, "GFTU.L": 45, "EVPL.L": 66,
        "CRW.L": 92, "BRK.L": 74, "NET.L": 58, "SWG.L": 80, "FLK.L": 45,
        "RCDO.L": 90, "AGR.L": 85, "GHH.L": 88, "AMS.L": 82, "RFX.L": 80,
    }

    rows = [fetch_fundamentals(t) for t in UNIVERSE]
    ranked = score_universe(rows, mna_heat_overrides)

    ranked["status"] = ranked["ticker"].map(STATUS_MAP)
    print(ranked[["name", "ticker", "sector", "status", "composite_score"]].to_string(index=False))
