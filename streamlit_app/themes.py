"""Thematic ETF universe for Trendasy.

Each *theme* is a thematic or sector ETF — a ready-made basket that expresses a
single market idea (SOXX = semiconductors, TAN = solar, BOTZ = robotics, …).
Tracking ETFs instead of hand-picked stock baskets means the constituents are
maintained by the fund provider and the price series cleanly represents the
theme.

The universe is loaded from ``data_files/etf_tickers.csv`` and enriched with the
human-readable name and category in :data:`ETF_META` below. Any ticker in the
CSV that is missing from the metadata table still works — it just shows up under
the "Other" category using the raw symbol as its name (and the live data layer
fills in the real fund name when Yahoo Finance is reachable).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_CSV_PATH = Path(__file__).parent / "data_files" / "etf_tickers.csv"


@dataclass(frozen=True)
class Theme:
    """A thematic/sector ETF and the idea it expresses."""

    ticker: str
    name: str
    category: str


# Best-effort metadata for the supplied ETF universe: (name, category).
# Names mirror each fund's common description; categories group the funds into
# the macro buckets the dashboard rolls up to.
ETF_META: dict[str, tuple[str, str]] = {
    # --- Technology ---------------------------------------------------------
    "SOXX": ("iShares Semiconductor", "Technology"),
    "IGV": ("iShares Expanded Tech-Software", "Technology"),
    "IGN": ("iShares Tech Multimedia Networking", "Technology"),
    "AIQ": ("Global X Artificial Intelligence & Tech", "Technology"),
    "QTUM": ("Defiance Quantum Computing", "Technology"),
    "NXTG": ("First Trust NextG / 5G Connectivity", "Technology"),
    "BOTZ": ("Global X Robotics & Artificial Intelligence", "Technology"),
    "PRNT": ("The 3D Printing ETF", "Technology"),
    # --- Cybersecurity, Cloud & Fintech ------------------------------------
    "IHAK": ("iShares Cybersecurity & Tech", "Cyber, Cloud & Fintech"),
    "CLOU": ("Global X Cloud Computing", "Cyber, Cloud & Fintech"),
    "FINX": ("Global X FinTech", "Cyber, Cloud & Fintech"),
    "IPAY": ("Amplify Digital Payments", "Cyber, Cloud & Fintech"),
    "EBIZ": ("Global X E-commerce", "Cyber, Cloud & Fintech"),
    "BLOK": ("Amplify Transformational Data Sharing (Blockchain)", "Cyber, Cloud & Fintech"),
    "WGMI": ("Valkyrie Bitcoin Miners", "Cyber, Cloud & Fintech"),
    # --- Communications, Media & Internet ----------------------------------
    "XLC": ("Communication Services Select Sector", "Comms, Media & Internet"),
    "IXP": ("iShares Global Comm Services", "Comms, Media & Internet"),
    "SOCL": ("Global X Social Media", "Comms, Media & Internet"),
    "ESPO": ("VanEck Video Gaming & eSports", "Comms, Media & Internet"),
    "METV": ("Roundhill Ball Metaverse", "Comms, Media & Internet"),
    "AWAY": ("AdvisorShares / ETFMG Travel Tech", "Comms, Media & Internet"),
    "UFO": ("Procure Space", "Comms, Media & Internet"),
    # --- Healthcare & Biotech ----------------------------------------------
    "XPH": ("SPDR S&P Pharmaceuticals", "Healthcare & Biotech"),
    "IBB": ("iShares Biotechnology", "Healthcare & Biotech"),
    "XBI": ("SPDR S&P Biotech", "Healthcare & Biotech"),
    "IDNA": ("iShares Genomics Immunology & Healthcare", "Healthcare & Biotech"),
    "OZEM": ("Roundhill GLP-1 & Weight Loss", "Healthcare & Biotech"),
    "IHI": ("iShares U.S. Medical Devices", "Healthcare & Biotech"),
    "XHE": ("SPDR S&P Health Care Equipment", "Healthcare & Biotech"),
    "EDOC": ("Global X Telemedicine & Digital Health", "Healthcare & Biotech"),
    "IHF": ("iShares U.S. Healthcare Providers", "Healthcare & Biotech"),
    "AGNG": ("Global X Aging Population", "Healthcare & Biotech"),
    "PSIL": ("AdvisorShares Psychedelics", "Healthcare & Biotech"),
    # --- Financials ---------------------------------------------------------
    "KBE": ("SPDR S&P Bank", "Financials"),
    "KRE": ("SPDR S&P Regional Banking", "Financials"),
    "IAI": ("iShares U.S. Broker-Dealers", "Financials"),
    "PSP": ("Invesco Global Listed Private Equity", "Financials"),
    "KIE": ("SPDR S&P Insurance", "Financials"),
    "BETZ": ("Roundhill Sports Betting & iGaming", "Financials"),
    # --- Energy, Metals & Materials ----------------------------------------
    "IXC": ("iShares Global Energy", "Energy & Materials"),
    "XOP": ("SPDR S&P Oil & Gas Exploration", "Energy & Materials"),
    "OIH": ("VanEck Oil Services", "Energy & Materials"),
    "AMLP": ("Alerian MLP / Midstream", "Energy & Materials"),
    "CRAK": ("VanEck Oil Refiners", "Energy & Materials"),
    "URNM": ("Sprott Uranium Miners", "Energy & Materials"),
    "NLR": ("VanEck Uranium & Nuclear", "Energy & Materials"),
    "GDX": ("VanEck Gold Miners", "Energy & Materials"),
    "GDXJ": ("VanEck Junior Gold Miners", "Energy & Materials"),
    "SIL": ("Global X Silver Miners", "Energy & Materials"),
    "COPX": ("Global X Copper Miners", "Energy & Materials"),
    "REMX": ("VanEck Rare Earth / Strategic Metals", "Energy & Materials"),
    "PICK": ("iShares MSCI Global Metals & Mining", "Energy & Materials"),
    "SLX": ("VanEck Steel", "Energy & Materials"),
    "WOOD": ("iShares Global Timber & Forestry", "Energy & Materials"),
    "EVX": ("VanEck Environmental Services", "Energy & Materials"),
    "MOO": ("VanEck Agribusiness", "Energy & Materials"),
    # --- Clean Energy, Climate & Infrastructure ----------------------------
    "TAN": ("Invesco Solar", "Clean Energy & Infrastructure"),
    "FAN": ("First Trust Global Wind Energy", "Clean Energy & Infrastructure"),
    "HDRO": ("Defiance Next Gen Hydrogen", "Clean Energy & Infrastructure"),
    "ICLN": ("iShares Global Clean Energy", "Clean Energy & Infrastructure"),
    "LIT": ("Global X Lithium & Battery Tech", "Clean Energy & Infrastructure"),
    "KARS": ("KraneShares Electric Vehicles & Future Mobility", "Clean Energy & Infrastructure"),
    "GRID": ("First Trust NASDAQ Clean Edge Smart Grid", "Clean Energy & Infrastructure"),
    "CGW": ("Invesco S&P Global Water", "Clean Energy & Infrastructure"),
    "WATS": ("LeaderShares / Global Water", "Clean Energy & Infrastructure"),
    "PAVE": ("Global X U.S. Infrastructure Development", "Clean Energy & Infrastructure"),
    "RNRG": ("Global X Renewable Energy Producers", "Clean Energy & Infrastructure"),
    "DRNZ": ("Drone & Autonomous Tech", "Clean Energy & Infrastructure"),
    # --- Industrials, Defense & Transport ----------------------------------
    "ITA": ("iShares U.S. Aerospace & Defense", "Industrials & Defense"),
    "XAR": ("SPDR S&P Aerospace & Defense", "Industrials & Defense"),
    "SHLD": ("Global X Defense Tech", "Industrials & Defense"),
    "JETS": ("U.S. Global Jets / Airlines", "Industrials & Defense"),
    "XHB": ("SPDR S&P Homebuilders", "Industrials & Defense"),
    "CARZ": ("First Trust S-Network Future Vehicles & Tech", "Industrials & Defense"),
    "CRUZ": ("Defiance Hotel, Airline & Cruise", "Industrials & Defense"),
    # --- Consumer, Real Estate & Utilities ---------------------------------
    "XRT": ("SPDR S&P Retail", "Consumer & Real Assets"),
    "EATZ": ("AdvisorShares Restaurant", "Consumer & Real Assets"),
    "MJ": ("ETFMG Alternative Harvest (Cannabis)", "Consumer & Real Assets"),
    "PBJ": ("Invesco Food & Beverage", "Consumer & Real Assets"),
    "XLRE": ("Real Estate Select Sector", "Consumer & Real Assets"),
    "REET": ("iShares Global REIT", "Consumer & Real Assets"),
    "VPN": ("Global X Data Center REITs & Digital Infrastructure", "Consumer & Real Assets"),
    "SRVR": ("Pacer Data & Infrastructure Real Estate", "Consumer & Real Assets"),
    "INDS": ("Pacer Industrial Real Estate", "Consumer & Real Assets"),
    "REZ": ("iShares Residential & Multisector Real Estate", "Consumer & Real Assets"),
    "JXI": ("iShares Global Utilities", "Consumer & Real Assets"),
    "IGF": ("iShares Global Infrastructure", "Consumer & Real Assets"),
}


def _load_universe() -> list[Theme]:
    """Read the ticker CSV and join it against :data:`ETF_META`."""
    themes: list[Theme] = []
    if not _CSV_PATH.exists():
        # Fall back to whatever we have metadata for so imports never break.
        for ticker, (name, category) in ETF_META.items():
            themes.append(Theme(ticker, name, category))
        return themes

    with _CSV_PATH.open(newline="") as fh:
        for row in csv.reader(fh):
            if not row:
                continue
            ticker = row[0].strip().upper()
            if not ticker:
                continue
            name, category = ETF_META.get(ticker, (ticker, "Other"))
            themes.append(Theme(ticker, name, category))
    return themes


THEMES: list[Theme] = _load_universe()


# Curated watchlists: opinionated cuts across the ETF universe.
WATCHLISTS: dict[str, list[str]] = {
    "AI & Compute": ["SOXX", "AIQ", "BOTZ", "QTUM", "IGV"],
    "Energy Transition": ["TAN", "ICLN", "LIT", "URNM", "GRID"],
    "Defensive Real Assets": ["GDX", "XLRE", "JXI", "PBJ", "IGF"],
    "Risk-On Momentum": ["WGMI", "BLOK", "BETZ", "XBI", "JETS"],
}


def categories() -> list[str]:
    """Distinct category names in stable, first-seen order."""
    seen: list[str] = []
    for theme in THEMES:
        if theme.category not in seen:
            seen.append(theme.category)
    return seen


def themes_in(category: str) -> list[Theme]:
    """All themes belonging to ``category``."""
    return [t for t in THEMES if t.category == category]


def all_tickers() -> list[str]:
    """Every unique ETF ticker in the universe, sorted."""
    return sorted({t.ticker for t in THEMES})


def theme_by_ticker(ticker: str) -> Theme | None:
    """Look up a theme by its ETF ticker."""
    ticker = ticker.upper()
    for theme in THEMES:
        if theme.ticker == ticker:
            return theme
    return None
