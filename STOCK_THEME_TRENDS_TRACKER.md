# Stock Theme Trends Tracker — Methodology

This document explains exactly what Trendasy measures, how, and what its limits
are. The goal is a transparent, reproducible read on **which market themes are
trending**, using thematic and sector ETFs as the unit of observation.

## Why ETFs as themes

A thematic ETF is a maintained, investable basket that already expresses a single
idea (e.g. `SOXX` = semiconductors, `TAN` = solar, `URNM` = uranium miners). Using
ETFs instead of hand-picked stock baskets means:

- **Constituents are curated** by the fund provider and rebalanced over time.
- **One clean price series** represents the whole theme — no weighting decisions
  on our side.
- **Comparability**: ranking 87 liquid ETFs is apples-to-apples.

The universe is defined in `streamlit_app/data_files/etf_tickers.csv` (87 tickers)
and enriched with human-readable names and macro categories in
`streamlit_app/themes.py`.

## The momentum score

For each ETF we compute the **trailing total return** over five standard windows
(measured in trading days):

| Window | Trading days |
|--------|--------------|
| 1W | 5 |
| 1M | 21 |
| 3M | 63 |
| 6M | 126 |
| 1Y | 252 |

Return for a window of `n` days is `price_today / price_{n days ago} − 1`.

These are blended into a single **momentum score**:

```
Momentum = 0.15·(1W) + 0.35·(1M) + 0.30·(3M) + 0.15·(6M) + 0.05·(1Y)
```

Design choices:

- **Medium-term tilt.** The 1M and 3M windows carry 65% of the weight — long
  enough to filter daily noise, short enough to catch active rotation.
- **Fresh-move sensitivity.** The 1W term (15%) lets a sharp new trend register
  before it dominates the monthly numbers.
- **Stale-trend discount.** The 1Y term is only 5%; a theme that ran a year ago
  but has since stalled won't keep scoring well.
- **Graceful gaps.** If a window can't be computed (insufficient history), its
  weight is renormalised across the remaining windows rather than treated as
  zero. A six-month-old ETF is still scored fairly on what data exists.

The score is a **relative** signal for ranking, not an annualised return or an
expected forward return.

## Date windows & the range return

The dashboard loads ~3 trading years of history and exposes a **date-range
slider**. Two distinct measures are derived from your selection:

- **Trailing windows / momentum** are computed *as of the end date* you pick —
  i.e. the price series is truncated at `end_date` and the 1W…1Y returns are
  measured back from there. Moving the end date back in time lets you ask "what
  was trending as of *that* day?"
- **Range %** is the simple return from `start_date` to `end_date` (nearest
  available trading days). This is the measure tied directly to the *specific*
  dates you choose, independent of the fixed windows.

On the **Compare themes** tab, selected ETFs are each **rebased to 100 at
`start_date`** and overlaid on one chart, so the vertical spread between lines is
their relative performance over your window.

## Category roll-ups

Each ETF maps to one of nine macro categories (Technology, Healthcare & Biotech,
Energy & Materials, …). The dashboard averages the momentum score within each
category to show where capital is rotating at the macro level. This is an
**equal-weight average across the ETFs in the category**, not AUM-weighted.

## Data sources & the offline fallback

- **Primary:** Yahoo Finance via `yfinance` (auto-adjusted daily closes).
- **Fallback:** when `yfinance` is unavailable or a download returns empty, the
  app generates a **deterministic synthetic price path per ticker** (seeded from
  a hash of the symbol, geometric random walk with per-ticker drift/vol). The
  same ticker always yields the same series, so screenshots and tests are stable.

The active mode is shown in the sidebar. **In demo mode the numbers are
synthetic** and must not be read as real market data.

## Limitations & caveats

- **Price-only.** Momentum ignores fundamentals, flows, valuation, and macro
  regime. It tells you *what* is trending, not *why* or whether it will continue.
- **Survivorship / selection.** The 87-ETF universe is a fixed, curated list;
  themes outside it are invisible.
- **Look-ahead-free but backward-looking.** All windows are trailing; this is a
  trend-following lens and will lag turning points.
- **No risk adjustment.** Scores are raw returns, not volatility-adjusted. A
  high-beta theme can top the board purely on amplitude.
- **Not investment advice.** This is a research and educational tool.

## Reproducing a ranking

```python
import sys; sys.path.insert(0, "streamlit_app")
import themes as u, data

tickers = u.all_tickers()
prices = data.get_price_history(tickers, days=252)
returns = data.compute_returns(prices)          # per-ticker, per-window %
# blend with the weights above to get the momentum score
```

See `app.py` (`momentum_score`) for the exact blending implementation.
