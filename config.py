# ============================================================
# CONFIG.PY — Configurações globais QDV3
# ============================================================

from datetime import datetime

# ── CAPITAL & RISCO ─────────────────────────────────────────
CAPITAL            = 1000
RISK_PER_TRADE_PCT = 0.10
LOOKBACK           = 400
TOP_N              = 20

# ── FILTROS ─────────────────────────────────────────────────
MIN_HURST          = 0.48
MIN_VOLUME         = 50000
LONG_BIAS          = True

# ── DEGIRO COMISSÕES ────────────────────────────────────────
DEGIRO_COMMISSIONS = {
    "NASDAQ":    1.00, "NYSE":      1.00,
    "XETRA":     3.90, "XPAR":      3.90,
    "XAMS":      3.90, "XMIL":      3.90,
    "XLIS":      1.00, "XMAD":      3.90,
    "XBRU":      3.90, "LSE":       3.90,
    "SWX":       5.00, "TSE":       5.00,
    "HKEX":      5.00, "ASX":       5.00,
    "TSX":       1.00, "XSTO":      3.90,
    "XCSE":      3.90, "XOSL":      3.90,
    "XHEL":      3.90, "XATH":      3.90,
    "XWBO":      3.90, "XDUB":      3.90,
    "XWAR":      3.90, "XPRA":      3.90,
    "SGX":       5.00, "FX":        0.00,
    "MACRO":     1.00, "COMMODITY": 1.00,
    "VOL":       1.00, "CBOE":      0.75,
    "EUREX":     0.75, "EURONEXT":  0.75,
    "MEFF":      0.75, "OMX":       0.75,
    "RATES":     1.00, "CRYPTO":    0.00,
    "INDEX":     0.00,
}

# ── CARTEIRA ────────────────────────────────────────────────
# P&L escondido por defeito no dashboard
PORTFOLIO = [
    {"ticker": "PDD",    "qty": 5,   "entry": 98.550,  "market": "NASDAQ"},
    {"ticker": "BCP.LS", "qty": 500, "entry": 0.9147,  "market": "XLIS"},
    {"ticker": "NVDA",   "qty": 6,   "entry": 199.555, "market": "NASDAQ"},
]

# Histórico de P&L para chart (data, valor)
PORTFOLIO_HISTORY = [
    ("13 Abr", -17.29),
    ("14 Abr",  22.53),
    ("15 Abr",  30.35),
    ("16 Abr", -21.94),
    ("17 Abr",  -9.07),
    ("21 Abr", -40.32),
    ("22 Abr", -33.28),
    ("23 Abr", -42.81),
    ("25 Abr", -23.32),
    ("28 Abr", -21.94),
    ("29 Abr",  -9.46),
    ("30 Abr", -42.81),
    ("01 Mai", -47.24),
    ("05 Mai", -47.24),
    ("06 Mai", 104.93),
    ("07 Mai", 111.87),
    ("08 Mai",  93.66),
    ("09 Mai", 136.58),
    ("11 Mai", 136.58),
]

# ── OUTPUT ──────────────────────────────────────────────────
DASHBOARD_FILE = "dashboard.html"
RESULTS_CSV    = "qdv3_results.csv"
RUN_DATE       = datetime.today().strftime("%d %b %Y — %H:%M")
FRED_API_KEY = "e26710c24b9cd3247ab3c6e78c736cef"