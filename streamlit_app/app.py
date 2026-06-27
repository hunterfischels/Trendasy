"""Trendasy — thematic ETF trend tracker.

A Streamlit dashboard that ranks a universe of thematic / sector ETFs by price
momentum, rolls them up into macro categories, and lets you drill into any
single theme. It runs against live Yahoo Finance data when ``yfinance`` is
installed and the network is up, and transparently falls back to deterministic
synthetic data otherwise (see :mod:`data`).

Run locally with::

    streamlit run streamlit_app/app.py
"""

from __future__ import annotations

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
def load_prices(tickers: tuple[str, ...], days: int) -> pd.DataFrame:
    return datalib.get_price_history(list(tickers), days=days)


@st.cache_data(ttl=60 * 60, show_spinner="Loading fundamentals…")
def load_fundamentals(tickers: tuple[str, ...]) -> pd.DataFrame:
    return datalib.get_fundamentals(list(tickers))


def _heat(value: float, vmin: float = -15.0, vmax: float = 15.0) -> str:
    """Map a number to a red→amber→green cell background (no matplotlib).

    Returns a CSS ``background-color`` declaration suitable for
    ``Styler.map``. NaNs get no styling.
    """
    if value is None or pd.isna(value):
        return ""
    # Clamp to [vmin, vmax] then to a 0..1 position.
    t = (max(min(float(value), vmax), vmin) - vmin) / (vmax - vmin)
    if t < 0.5:  # red -> amber
        f = t / 0.5
        r, g, b = 214, int(80 + 175 * f), 70
    else:  # amber -> green
        f = (t - 0.5) / 0.5
        r, g, b = int(214 - 130 * f), 200 - int(20 * f), int(70 + 20 * f)
    return f"background-color: rgba({r},{g},{b},0.55)"


def momentum_score(returns_row: pd.Series) -> float:
    """Blend trailing windows into one momentum score.

    Weights favour the medium-term trend (1M/3M) while still rewarding fresh
    moves (1W) and penalising stale ones. NaNs are ignored.
    """
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
# Sidebar controls
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.title("📈 Trendasy")
    st.caption("Thematic ETF trend tracker")

    source = datalib.data_source()
    if source == "live":
        st.success("Live data · Yahoo Finance", icon="🟢")
    else:
        st.info("Demo data (deterministic synthetic prices)", icon="🟡")
        st.caption("Install `yfinance` and connect to the internet for live quotes.")

    lookback_label = st.select_slider(
        "Price history window",
        options=["3M", "6M", "1Y"],
        value="1Y",
    )
    days_map = {"3M": 63, "6M": 126, "1Y": 252}
    days = days_map[lookback_label]

    cat_options = ["All categories", *universe.categories()]
    chosen_category = st.selectbox("Filter by category", cat_options)

    st.divider()
    st.caption(f"{len(universe.THEMES)} ETFs · {len(universe.categories())} categories")
    st.caption("Not investment advice. For research & education only.")


# Resolve the active ticker set based on the category filter.
if chosen_category == "All categories":
    active_themes = universe.THEMES
else:
    active_themes = universe.themes_in(chosen_category)
active_tickers = tuple(t.ticker for t in active_themes)

prices = load_prices(active_tickers, days)
returns = datalib.compute_returns(prices)


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
    "Ranking thematic and sector ETFs by a blended price-momentum score. "
    "Higher score = stronger, more consistent recent uptrend."
)

if table.empty:
    st.warning("No price data available for the current selection.")
    st.stop()

leaders = table.head(3)
laggards = table.tail(3).iloc[::-1]
c1, c2, c3 = st.columns(3)
for col, (_, row) in zip((c1, c2, c3), leaders.iterrows()):
    col.metric(
        f"🏆 {row['Ticker']}",
        f"{row['Momentum']:+.1f}",
        f"{row['1M %']:+.1f}% · 1M" if pd.notna(row["1M %"]) else "—",
        help=row["Theme"],
    )


tab_rank, tab_categories, tab_detail, tab_watch = st.tabs(
    ["🔥 Leaderboard", "🗂️ Categories", "🔎 Theme detail", "⭐ Watchlists"]
)


# --------------------------------------------------------------------------- #
# Tab: Leaderboard
# --------------------------------------------------------------------------- #
with tab_rank:
    st.subheader("Momentum leaderboard")

    def _style(df: pd.DataFrame):
        pct_cols = ["Momentum", "1W %", "1M %", "3M %", "6M %", "1Y %"]
        styler = df.style.format({c: "{:+.1f}" for c in pct_cols}, na_rep="—")
        return styler.map(_heat, subset=["Momentum"])

    st.dataframe(
        _style(table.reset_index(drop=True)),
        width="stretch",
        hide_index=True,
        height=560,
    )

    st.caption("Momentum = 0.15·1W + 0.35·1M + 0.30·3M + 0.15·6M + 0.05·1Y (trailing total return %).")


# --------------------------------------------------------------------------- #
# Tab: Categories
# --------------------------------------------------------------------------- #
with tab_categories:
    st.subheader("How each macro category is trending")
    cat_summary = (
        table.groupby("Category")["Momentum"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "Avg momentum", "count": "ETFs"})
        .sort_values("Avg momentum", ascending=False)
    )
    cat_summary["Avg momentum"] = cat_summary["Avg momentum"].round(2)

    bar = cat_summary["Avg momentum"]
    st.bar_chart(bar, horizontal=True, color="#4f8bf9")
    st.dataframe(
        cat_summary.style.format({"Avg momentum": "{:+.2f}"}),
        width="stretch",
    )


# --------------------------------------------------------------------------- #
# Tab: Theme detail
# --------------------------------------------------------------------------- #
with tab_detail:
    pick = st.selectbox(
        "Choose a theme",
        options=table["Ticker"].tolist(),
        format_func=lambda t: f"{t} — {universe.theme_by_ticker(t).name}",
    )
    theme = universe.theme_by_ticker(pick)
    st.markdown(f"### {theme.name}  \n`{theme.ticker}` · {theme.category}")

    idx = datalib.theme_index(prices, [pick])
    if not idx.empty:
        rebased = (idx / idx.iloc[0] * 100).rename(pick)
        st.line_chart(rebased, height=320)
        st.caption("Price rebased to 100 at the start of the selected window.")

    r = returns.loc[pick]
    cols = st.columns(5)
    for col, window in zip(cols, ["1W", "1M", "3M", "6M", "1Y"]):
        val = r.get(window)
        col.metric(window, f"{val:+.1f}%" if pd.notna(val) else "—")

    fund = load_fundamentals([pick])
    if not fund.empty:
        st.markdown("#### Snapshot")
        f = fund.iloc[0]
        mc = f.get("market_cap")
        st.write(
            {
                "Name": f.get("name"),
                "Sector / focus": f.get("sector"),
                "AUM / mkt cap": f"${mc/1e9:,.1f}B" if mc else "—",
                "P/E": f.get("pe_ratio"),
                "Beta": f.get("beta"),
                "Yield": f"{f.get('dividend_yield', 0)*100:.2f}%"
                if f.get("dividend_yield")
                else "—",
            }
        )


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
                    "1M %": r.get("1M"),
                    "3M %": r.get("3M"),
                }
            )
        wl = pd.DataFrame(wl_rows).sort_values("Momentum", ascending=False)
        st.dataframe(
            wl.style.format(
                {"Momentum": "{:+.1f}", "1M %": "{:+.1f}", "3M %": "{:+.1f}"},
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
