# Watchlists & Fundamentals

Beyond the full 87-ETF leaderboard, Trendasy ships a few **curated watchlists**
and a lightweight **fundamentals snapshot** for drill-down. Both are described
here; both are defined in code so they're easy to edit.

## Curated watchlists

Watchlists are opinionated cross-sections of the universe — smaller, themed cuts
you might actually monitor together. They live in `WATCHLISTS` in
`streamlit_app/themes.py` and render on the dashboard's **⭐ Watchlists** tab,
sorted by momentum.

| Watchlist | ETFs | Idea |
|-----------|------|------|
| **AI & Compute** | `SOXX`, `AIQ`, `BOTZ`, `QTUM`, `IGV` | The picks-and-shovels of the AI build-out: chips, AI baskets, robotics, quantum, software. |
| **Energy Transition** | `TAN`, `ICLN`, `LIT`, `URNM`, `GRID` | Decarbonisation supply chain: solar, broad clean energy, lithium/batteries, uranium, smart grid. |
| **Defensive Real Assets** | `GDX`, `XLRE`, `JXI`, `PBJ`, `IGF` | Lower-beta, real-asset / staples tilt: gold miners, REITs, utilities, food & beverage, infrastructure. |
| **Risk-On Momentum** | `WGMI`, `BLOK`, `BETZ`, `XBI`, `JETS` | High-beta, sentiment-driven corners: bitcoin miners, blockchain, betting, biotech, airlines. |

### Editing watchlists

```python
# streamlit_app/themes.py
WATCHLISTS = {
    "My List": ["SOXX", "TAN", "GDX"],
    ...
}
```

Any ticker that isn't in the universe is simply skipped at render time, so it's
safe to reference tickers loosely.

## Fundamentals snapshot

The **🔎 Theme detail** tab shows a per-ETF snapshot. Fields:

| Field | Meaning | Source |
|-------|---------|--------|
| **Name** | Fund name | `yfinance` `shortName`, else our `ETF_META` label |
| **Sector / focus** | Sector classification | `yfinance` `sector` |
| **AUM / mkt cap** | Fund size proxy | `yfinance` `marketCap` |
| **P/E** | Trailing price/earnings of holdings | `yfinance` `trailingPE` |
| **Beta** | Sensitivity vs. market | `yfinance` `beta` |
| **Yield** | Trailing distribution yield | `yfinance` `dividendYield` |

### Caveats specific to ETFs

- **`marketCap` ≈ AUM, loosely.** For funds, Yahoo's `marketCap` field is an
  imperfect stand-in for assets under management; treat it as an order-of-
  magnitude size signal, not an exact AUM.
- **P/E and beta are blended** across the fund's holdings and can be missing or
  noisy for niche thematics.
- **Demo mode is synthetic.** When `yfinance` is unavailable, fundamentals are
  generated deterministically from the ticker hash (see `data._synthetic_fundamentals`)
  and are **not real**. The sidebar flags demo mode.

## Putting it together

A reasonable workflow with the dashboard:

1. **Leaderboard** → scan which themes have the strongest blended momentum.
2. **Categories** → confirm whether that strength is broad (whole category) or
   idiosyncratic (one ETF).
3. **Theme detail** → inspect the rebased price chart and the fundamentals
   snapshot for a candidate.
4. **Watchlists** → track your shortlist over time.

As always: this is a **research lens, not advice**. Momentum is backward-looking
and says nothing about valuation or what happens next.
