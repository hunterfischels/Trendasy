# Trendasy 📈

**A thematic-ETF trend tracker.** Trendasy ranks a universe of **87 thematic and
sector ETFs** by a blended price-momentum score and rolls them up into nine macro
categories, so you can see at a glance which market themes are trending — from
semiconductors and uranium to GLP-1 and defense tech.

It ships as two things:

| Piece | Path | What it is |
|-------|------|-----------|
| **Dashboard** | `streamlit_app/app.py` | Interactive Streamlit app: leaderboard, category roll-ups, per-theme drill-down, watchlists. |
| **Landing page** | `index.html` + `assets/` | Static site (deployable to GitHub Pages) describing the project and the theme universe. |

> ⚠️ **Educational research tool — not investment advice.** ETFs carry risk,
> including possible loss of principal.

---

## Quick start

```bash
git clone https://github.com/hunterfischels/Trendasy.git
cd Trendasy
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

Then open <http://localhost:8501>.

### Live vs. demo data

- **Live:** if [`yfinance`](https://pypi.org/project/yfinance/) is installed and
  the network is reachable, prices and fundamentals come from Yahoo Finance.
- **Demo:** otherwise the app transparently falls back to **deterministic
  synthetic prices** (seeded per ticker), so it always renders — useful in CI,
  offline, or locked-down sandboxes. The sidebar shows which mode is active.

---

## How the momentum score works

For each ETF we compute trailing total returns over five windows and blend them:

```
Momentum = 0.15·(1W) + 0.35·(1M) + 0.30·(3M) + 0.15·(6M) + 0.05·(1Y)
```

The weighting favours the medium-term trend (1–3 months) while still reacting to
fresh moves and discounting stale ones. Missing windows are renormalised away, so
a young ETF without a full year of history still gets a fair score. See
[`STOCK_THEME_TRENDS_TRACKER.md`](STOCK_THEME_TRENDS_TRACKER.md) for the full
methodology and [`WATCHLISTS_AND_FUNDAMENTALS.md`](WATCHLISTS_AND_FUNDAMENTALS.md)
for the curated watchlists and fundamentals snapshot.

---

## The theme universe

The 87 ETFs are grouped into nine macro categories. The list lives in
[`streamlit_app/data_files/etf_tickers.csv`](streamlit_app/data_files/etf_tickers.csv)
and is enriched with names/categories in
[`streamlit_app/themes.py`](streamlit_app/themes.py).

| Category | # |
|----------|---|
| Technology | 8 |
| Cyber, Cloud & Fintech | 7 |
| Comms, Media & Internet | 7 |
| Healthcare & Biotech | 11 |
| Financials | 6 |
| Energy & Materials | 17 |
| Clean Energy & Infrastructure | 12 |
| Industrials & Defense | 7 |
| Consumer & Real Assets | 12 |

To add a theme, drop its ticker into the CSV and (optionally) add a name +
category in `ETF_META`. Unknown tickers still work — they appear under "Other"
with the raw symbol as the name.

---

## Project layout

```
Trendasy/
├── index.html                      # static landing page (GitHub Pages)
├── assets/                         # style.css, logo.svg
├── requirements.txt                # convenience root pin
├── publish.sh                      # push this repo's HEAD to a remote/branch
├── streamlit_app/
│   ├── app.py                      # Streamlit dashboard
│   ├── data.py                     # price/fundamentals + synthetic fallback
│   ├── themes.py                   # ETF universe, categories, watchlists
│   ├── requirements.txt            # app dependencies
│   └── data_files/etf_tickers.csv  # the 87-ticker universe
├── STOCK_THEME_TRENDS_TRACKER.md   # methodology
├── WATCHLISTS_AND_FUNDAMENTALS.md  # watchlists + fundamentals notes
└── .github/workflows/deploy-pages.yml
```

---

## Deploying

### Dashboard → Streamlit Community Cloud
1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io/), create an app pointing
   at this repo with main file **`streamlit_app/app.py`**.

### Landing page → GitHub Pages
1. **Settings → Pages → Source = "GitHub Actions"**.
2. The bundled [`deploy-pages.yml`](.github/workflows/deploy-pages.yml) workflow
   publishes `index.html` + `assets/` on every push to `main`. The site lands at
   `https://hunterfischels.github.io/Trendasy/`.

---

## Development

```bash
# compile-check the app
python -m py_compile streamlit_app/*.py

# headless smoke test (no browser needed)
python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("streamlit_app/app.py", default_timeout=60).run()
assert not at.exception, at.exception
print("ok:", len(at.tabs), "tabs")
PY
```

## License

MIT — see [`LICENSE`](LICENSE).
