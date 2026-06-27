"""Data layer for Trendasy.

Price history and fundamentals are pulled from Yahoo Finance via ``yfinance``
when it is installed and the network is reachable. When it is not — offline
demos, CI, locked-down sandboxes — every function transparently falls back to
deterministic synthetic data so the dashboard always renders.

The synthetic generator is seeded per-ticker, so the same symbol always
produces the same fake series. That keeps screenshots and tests stable.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import math

import pandas as pd

# Trading days roughly per calendar period; used to slice return windows.
WINDOWS: dict[str, int] = {
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "1Y": 252,
}

# How much history we load by default: ~3 trading years. This is the pool the
# UI's date-range slider draws from, so any specific start date within the last
# three years can be selected.
MAX_LOOKBACK_DAYS = 756

# The most recent date the (synthetic) series ends on. Kept here so the demo
# fallback and any date math agree on "today".
TODAY = _dt.date(2026, 6, 27)


def data_source() -> str:
    """Return ``"live"`` if yfinance is importable, else ``"demo"``."""
    try:
        import yfinance  # noqa: F401

        return "live"
    except Exception:
        return "demo"


# --------------------------------------------------------------------------- #
# Synthetic fallback
# --------------------------------------------------------------------------- #
def _seed(ticker: str) -> int:
    """Stable integer seed derived from the ticker symbol."""
    digest = hashlib.sha256(ticker.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _synthetic_series(ticker: str, days: int) -> pd.Series:
    """A plausible-looking geometric random walk for one ticker.

    Deterministic given the ticker: same symbol -> same path. Uses a small
    linear-congruential generator so we avoid any dependency on global RNG
    state or numpy.
    """
    seed = _seed(ticker)
    state = seed

    def _rand() -> float:
        # Numerical Recipes LCG -> uniform in [0, 1).
        nonlocal state
        state = (1664525 * state + 1013904223) % (2**32)
        return state / 2**32

    # Per-ticker drift/vol so themes diverge in a believable way.
    drift = (seed % 7 - 3) * 0.0006  # roughly -0.18%..+0.18% daily
    vol = 0.012 + (seed % 5) * 0.004  # 1.2%..2.8% daily
    price = 50.0 + seed % 450  # starting price 50..500

    prices: list[float] = []
    for _ in range(days):
        # Box-Muller from two uniforms -> approx standard normal shock.
        u1 = max(_rand(), 1e-9)
        u2 = _rand()
        shock = math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2)
        price *= math.exp(drift + vol * shock)
        prices.append(round(price, 2))

    idx = pd.bdate_range(end=TODAY, periods=days)
    return pd.Series(prices, index=idx, name=ticker)


def _synthetic_history(tickers: list[str], days: int) -> pd.DataFrame:
    return pd.DataFrame({t: _synthetic_series(t, days) for t in tickers})


def _synthetic_fundamentals(ticker: str) -> dict:
    seed = _seed(ticker)
    return {
        "ticker": ticker,
        "name": ticker,
        "sector": ["Technology", "Healthcare", "Energy", "Consumer"][seed % 4],
        "market_cap": (10 + seed % 2900) * 1e9,
        "pe_ratio": round(8 + (seed % 600) / 10, 1),
        "dividend_yield": round((seed % 40) / 1000, 4),
        "beta": round(0.6 + (seed % 140) / 100, 2),
    }


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_price_history(tickers: list[str], days: int = MAX_LOOKBACK_DAYS) -> pd.DataFrame:
    """Daily close prices for ``tickers`` as a wide DataFrame (date index).

    Loads ~3 trading years by default so the UI can slice to any specific date
    within that span. Falls back to synthetic data if yfinance is unavailable or
    the download comes back empty.
    """
    if not tickers:
        return pd.DataFrame()

    # An N-day trailing return needs N+1 observations, so pad the request past
    # the largest window we report on.
    fetch_days = max(days, max(WINDOWS.values())) + 5

    if data_source() == "live":
        try:
            import yfinance as yf

            if fetch_days > 504:
                period = "5y"
            elif fetch_days > 252:
                period = "2y"
            else:
                period = "1y"
            raw = yf.download(
                tickers,
                period=period,
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
            # yfinance returns a column MultiIndex for >1 ticker.
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"]
            else:
                close = raw[["Close"]]
                close.columns = tickers[:1]
            close = close.dropna(how="all").tail(fetch_days)
            if not close.empty:
                return close
        except Exception:
            pass  # fall through to synthetic

    return _synthetic_history(tickers, fetch_days)


def get_fundamentals(tickers: list[str]) -> pd.DataFrame:
    """Snapshot fundamentals (market cap, P/E, beta, yield) per ticker."""
    if not tickers:
        return pd.DataFrame()

    rows: list[dict] = []
    if data_source() == "live":
        try:
            import yfinance as yf

            for t in tickers:
                info = yf.Ticker(t).info or {}
                rows.append(
                    {
                        "ticker": t,
                        "name": info.get("shortName") or t,
                        "sector": info.get("sector") or "—",
                        "market_cap": info.get("marketCap"),
                        "pe_ratio": info.get("trailingPE"),
                        "dividend_yield": info.get("dividendYield"),
                        "beta": info.get("beta"),
                    }
                )
            if rows and any(r.get("market_cap") for r in rows):
                return pd.DataFrame(rows)
        except Exception:
            rows = []

    rows = [_synthetic_fundamentals(t) for t in tickers]
    return pd.DataFrame(rows)


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Trailing total return per ticker across the standard windows.

    Returns a DataFrame indexed by ticker with one column per window in
    :data:`WINDOWS` (values in percent).
    """
    out: dict[str, dict[str, float]] = {}
    for ticker in prices.columns:
        series = prices[ticker].dropna()
        row: dict[str, float] = {}
        for label, n in WINDOWS.items():
            if len(series) > n:
                start, end = series.iloc[-n - 1], series.iloc[-1]
                row[label] = round((end / start - 1) * 100, 2) if start else float("nan")
            else:
                row[label] = float("nan")
        out[ticker] = row
    return pd.DataFrame(out).T


def range_return(prices: pd.DataFrame, start, end) -> pd.Series:
    """Percent return of each ticker between ``start`` and ``end`` (inclusive).

    ``start``/``end`` are dates; the nearest available trading day at or after
    ``start`` and at or before ``end`` is used. Returns a Series indexed by
    ticker (values in percent), NaN where the window has no data.
    """
    window = prices.loc[str(start):str(end)]
    out: dict[str, float] = {}
    for ticker in prices.columns:
        series = window[ticker].dropna()
        if len(series) >= 2 and series.iloc[0]:
            out[ticker] = round((series.iloc[-1] / series.iloc[0] - 1) * 100, 2)
        else:
            out[ticker] = float("nan")
    return pd.Series(out, name="Range %")


def rebase(prices: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    """Rebase every column to ``base`` at its first valid observation.

    Lets multiple tickers with different absolute prices be compared on one
    chart — each starts at ``base`` and the lines show relative performance.
    """
    if prices.empty:
        return prices
    out = {}
    for ticker in prices.columns:
        series = prices[ticker].dropna()
        if series.empty or not series.iloc[0]:
            continue
        out[ticker] = series / series.iloc[0] * base
    return pd.DataFrame(out)


def theme_index(prices: pd.DataFrame, tickers: list[str]) -> pd.Series:
    """Equal-weight, rebased-to-100 index for a basket of tickers."""
    cols = [t for t in tickers if t in prices.columns]
    if not cols:
        return pd.Series(dtype=float)
    basket = prices[cols].dropna(how="all")
    normalized = basket.divide(basket.iloc[0]).mean(axis=1) * 100
    return normalized.rename("index")
