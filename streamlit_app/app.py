"""Trendasy — thematic ETF trend tracker.

A Streamlit dashboard that ranks a universe of thematic / sector ETFs by price
momentum, rolls them up into macro categories, and lets you drill into (and
overlay) individual themes over any specific date window in the last ~3 years.
It runs against live Yahoo Finance data when ``yfinance`` is installed and the
network is up, and transparently falls back to deterministic synthetic data
otherwise (see :mod:`data`).

Run locally with::

    streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import data as datalib
import themes as universe

st.set_page_config(
    page_title="Trendasy · Thematic ETF Trends",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Cached data access
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=60 * 30, show_spinner="Loading price history…")
def load_prices(tickers: tuple[str, ...]) -> pd.DataFrame:
    """~3 years of daily closes; sliced per the date window in the UI."""
    return datalib.get_price_history(list(tickers), days=datalib.MAX_LOOKBACK_DAYS)


@st.cache_data(ttl=60 * 60, show_spinner="Loading fundamentals…")
def load_fundamentals(tickers: tuple[str, ...]) -> pd.DataFrame:
    return datalib.get_fundamentals(list(tickers))


def _heat(value: float, vmin: float = -15.0, vmax: float = 15.0) -> str:
    """Map a number to a red→amber→green cell background (no matplotlib)."""
    if value is None or pd.isna(value):
        return ""
    t = (max(min(float(value), vmax), vmin) - vmin) / (vmax - vmin)
    if t < 0.5:  # red -> amber
        f = t / 0.5
        r, g, b = 214, int(80 + 175 * f), 70
    else:  # amber -> green
        f = (t - 0.5) / 0.5
        r, g, b = int(214 - 130 * f), 200 - int(20 * f), int(70 + 20 * f)
    return f"background-color: rgba({r},{g},{b},0.55)"


def momentum_score(returns_row: pd.Series) -> float:
    """Blend trailing windows into one momentum score (NaNs renormalised)."""
    weights = {"1W": 0.15, "1M": 0.35, "3M": 0.30, "6M": 0.15, "1Y": 0.05}
    total_w = 0.0
    acc = 0.0
    for window, w in weights.items():
        val = returns_row.get(window)
        if val is not None and pd.notna(val):
            acc += w * float(val)
            total_w += w
    return round(acc / total_w, 2) if total_w else float("nan")


# --------------------------------------------------------------------------- #
# Sidebar — category filter (date slider added once prices are loaded)
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.title("📈 Trendasy")
    st.caption("Thematic ETF trend tracker")

    if datalib.data_source() == "live":
        st.success("Live data · Yahoo Finance", icon="🟢")
    else:
        st.info("Demo data (deterministic synthetic prices)", icon="🟡")
        st.caption("Install `yfinance` and connect to the internet for live quotes.")

    cat_options = ["All categories", *universe.categories()]
    chosen_category = st.selectbox("Filter by category", cat_options)


# Resolve active tickers and load the full history pool.
if chosen_category == "All categories":
    active_themes = universe.THEMES
else:
    active_themes = universe.themes_in(chosen_category)
active_tickers = tuple(t.ticker for t in active_themes)

prices_full = load_prices(active_tickers)
if prices_full.empty:
    st.warning("No price data available for the current selection.")
    st.stop()

# Date bounds come from the loaded series.
all_dates = prices_full.index
min_date: dt.date = all_dates.min().date()
max_date: dt.date = all_dates.max().date()
default_start = max(min_date, max_date - dt.timedelta(days=365))

with st.sidebar:
    start_date, end_date = st.slider(
        "Analysis window",
        min_value=min_date,
        max_value=max_date,
        value=(default_start, max_date),
        format="YYYY-MM-DD",
        help="Pick any specific start/end date within the last ~3 years.",
    )
    st.divider()
    st.caption(f"{len(active_themes)} ETFs · window {start_date} → {end_date}")
    st.caption("Not investment advice. For research & education only.")


# --------------------------------------------------------------------------- #
# Returns: trailing windows "as of" end_date + the specific-date range return
# --------------------------------------------------------------------------- #
up_to_end = prices_full.loc[:str(end_date)]
returns = datalib.compute_returns(up_to_end)
range_ret = datalib.range_return(prices_full, start_date, end_date)
window_prices = prices_full.loc[str(start_date):str(end_date)]


# --------------------------------------------------------------------------- #
# Build the master theme table
# --------------------------------------------------------------------------- #
rows: list[dict] = []
for theme in active_themes:
    if theme.ticker not in returns.index:
        continue
    r = returns.loc[theme.ticker]
    rows.append(
        {
            "Ticker": theme.ticker,
            "Theme": theme.name,
            "Category": theme.category,
            "Momentum": momentum_score(r),
            "Range %": range_ret.get(theme.ticker),
            "1W %": r.get("1W"),
            "1M %": r.get("1M"),
            "3M %": r.get("3M"),
            "6M %": r.get("6M"),
            "1Y %": r.get("1Y"),
        }
    )

table = pd.DataFrame(rows)
if not table.empty:
    table = table.sort_values("Momentum", ascending=False, na_position="last")


# --------------------------------------------------------------------------- #
# Header + headline metrics
# --------------------------------------------------------------------------- #
st.title("Thematic ETF Trends")
st.write(
    f"Ranking thematic and sector ETFs by a blended price-momentum score "
    f"(as of **{end_date}**). The **Range %** column is each theme's return over "
    f"your selected window **{start_date} → {end_date}**."
)

if table.empty:
    st.warning("No price data available for the current selection.")
    st.stop()

leaders = table.head(3)
c1, c2, c3 = st.columns(3)
for col, (_, row) in zip((c1, c2, c3), leaders.iterrows()):
    col.metric(
        f"🏆 {row['Ticker']}",
        f"{row['Momentum']:+.1f}",
        f"{row['Range %']:+.1f}% · window" if pd.notna(row["Range %"]) else "—",
        help=row["Theme"],
    )


tab_rank, tab_categories, tab_detail, tab_watch = st.tabs(
    ["🔥 Leaderboard", "🗂️ Categories", "🔎 Compare themes", "⭐ Watchlists"]
)


# --------------------------------------------------------------------------- #
# Tab: Leaderboard
# --------------------------------------------------------------------------- #
with tab_rank:
    st.subheader("Momentum leaderboard")

    def _style(df: pd.DataFrame):
        pct_cols = ["Momentum", "Range %", "1W %", "1M %", "3M %", "6M %", "1Y %"]
        styler = df.style.format({c: "{:+.1f}" for c in pct_cols}, na_rep="—")
        return styler.map(_heat, subset=["Momentum"]).map(_heat, subset=["Range %"])

    st.dataframe(
        _style(table.reset_index(drop=True)),
        width="stretch",
        hide_index=True,
        height=560,
    )
    st.caption(
        "Momentum = 0.15·1W + 0.35·1M + 0.30·3M + 0.15·6M + 0.05·1Y (trailing, as of end date). "
        f"Range % = return from {start_date} to {end_date}."
    )


# --------------------------------------------------------------------------- #
# Tab: Categories
# --------------------------------------------------------------------------- #
with tab_categories:
    st.subheader("How each macro category is trending")
    cat_summary = (
        table.groupby("Category")[["Momentum", "Range %"]]
        .mean()
        .round(2)
        .sort_values("Momentum", ascending=False)
    )
    st.bar_chart(cat_summary["Momentum"], horizontal=True, color="#4f8bf9")
    st.dataframe(
        cat_summary.style.format({"Momentum": "{:+.2f}", "Range %": "{:+.2f}"}, na_rep="—"),
        width="stretch",
    )


# --------------------------------------------------------------------------- #
# Tab: Compare themes (multi-ETF overlay)
# --------------------------------------------------------------------------- #
with tab_detail:
    st.subheader("Compare themes over the selected window")
    default_pick = table["Ticker"].head(3).tolist()
    picks = st.multiselect(
        "Choose one or more ETFs to overlay",
        options=table["Ticker"].tolist(),
        default=default_pick,
        format_func=lambda t: f"{t} — {universe.theme_by_ticker(t).name}",
    )

    if not picks:
        st.info("Select at least one ETF to plot.")
    else:
        rebased = datalib.rebase(window_prices[[p for p in picks if p in window_prices.columns]])
        if not rebased.empty:
            st.line_chart(rebased, height=380)
            st.caption(
                f"Each line rebased to 100 at {start_date}. Lines above 100 "
                f"outperformed their {start_date} level; the spread shows relative trend."
            )

        # Side-by-side returns for the picked ETFs.
        cmp_rows = []
        for t in picks:
            r = returns.loc[t] if t in returns.index else pd.Series(dtype=float)
            cmp_rows.append(
                {
                    "Ticker": t,
                    "Theme": universe.theme_by_ticker(t).name,
                    "Momentum": momentum_score(r),
                    "Range %": range_ret.get(t),
                    "1M %": r.get("1M"),
                    "3M %": r.get("3M"),
                    "1Y %": r.get("1Y"),
                }
            )
        cmp = pd.DataFrame(cmp_rows)
        st.dataframe(
            cmp.style.format(
                {c: "{:+.1f}" for c in ["Momentum", "Range %", "1M %", "3M %", "1Y %"]},
                na_rep="—",
            ),
            width="stretch",
            hide_index=True,
        )

        # Fundamentals snapshot (kept light: only when a handful are selected).
        if len(picks) <= 6:
            fund = load_fundamentals(tuple(picks))
            if not fund.empty:
                with st.expander("Fundamentals snapshot"):
                    show = fund.copy()
                    if "market_cap" in show:
                        show["market_cap"] = show["market_cap"].apply(
                            lambda v: f"${v/1e9:,.1f}B" if pd.notna(v) and v else "—"
                        )
                    if "dividend_yield" in show:
                        show["dividend_yield"] = show["dividend_yield"].apply(
                            lambda v: f"{v*100:.2f}%" if pd.notna(v) and v else "—"
                        )
                    st.dataframe(show, width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Tab: Watchlists
# --------------------------------------------------------------------------- #
with tab_watch:
    st.subheader("Curated watchlists")
    for name, tickers in universe.WATCHLISTS.items():
        present = [t for t in tickers if t in returns.index]
        if not present:
            continue
        st.markdown(f"#### {name}")
        wl_rows = []
        for t in present:
            th = universe.theme_by_ticker(t)
            r = returns.loc[t]
            wl_rows.append(
                {
                    "Ticker": t,
                    "Theme": th.name if th else t,
                    "Momentum": momentum_score(r),
                    "Range %": range_ret.get(t),
                    "1M %": r.get("1M"),
                    "3M %": r.get("3M"),
                }
            )
        wl = pd.DataFrame(wl_rows).sort_values("Momentum", ascending=False)
        st.dataframe(
            wl.style.format(
                {c: "{:+.1f}" for c in ["Momentum", "Range %", "1M %", "3M %"]},
                na_rep="—",
            ),
            width="stretch",
            hide_index=True,
        )

st.divider()
st.caption(
    "Trendasy · built with Streamlit · data via Yahoo Finance (yfinance) with a "
    "deterministic offline fallback. Educational use only — not investment advice."
)
