# ============================================================
# CONFIG.PY — Configurações globais QDV3
# ============================================================

from datetime import datetime

# ── FRED API ─────────────────────────────────────────────────
FRED_API_KEY = "7b5855b317108664ade01a13fcedffe0"

# ── CAPITAL & RISCO ──────────────────────────────────────────
CAPITAL            = 3347.00
RISK_PER_TRADE_PCT = 0.10
LOOKBACK           = 400
TOP_N              = 20

# ── FILTROS ──────────────────────────────────────────────────
MIN_HURST          = 0.48
MIN_VOLUME         = 50000
LONG_BIAS          = True

# ── DEGIRO COMISSÕES ─────────────────────────────────────────
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

# ── POSIÇÕES ABERTAS ─────────────────────────────────────────
PORTFOLIO = [
    {
        "ticker":   "NVDA",
        "name":     "Nvidia",
        "qty":      3,
        "entry":    213.3336,
        "market":   "NASDAQ",
        "date":     "06 Mai 2026",
        "currency": "USD",
    },
    {
        "ticker":   "BCP.LS",
        "name":     "Millennium BCP",
        "qty":      500,
        "entry":    0.9147,
        "market":   "XLIS",
        "date":     "06 Mai 2026",
        "currency": "EUR",
    },
]

# ── TRADES FECHADAS ──────────────────────────────────────────
CLOSED_TRADES = [
    {
        "ticker":   "NVDA",
        "name":     "Nvidia",
        "qty":      5,
        "entry":    197.6500,
        "exit":     216.3400,
        "date_in":  "01 Mai 2026",
        "date_out": "07 Mai 2026",
        "market":   "NASDAQ",
        "currency": "USD",
    },
    {
        "ticker":   "NVDA",
        "name":     "Nvidia",
        "qty":      3,
        "entry":    213.3336,
        "exit":     226.2420,
        "date_in":  "06 Mai 2026",
        "date_out": "15 Mai 2026",
        "market":   "NASDAQ",
        "currency": "USD",
    },
    {
        "ticker":   "PDD",
        "name":     "PDD Holdings",
        "qty":      10,
        "entry":    99.9655,
        "exit":     95.2500,
        "date_in":  "05 Mai 2026",
        "date_out": "15 Mai 2026",
        "market":   "NASDAQ",
        "currency": "USD",
    },
    {
        "ticker":   "PDD",
        "name":     "PDD Holdings",
        "qty":      5,
        "entry":    97.8700,
        "exit":     95.2500,
        "date_in":  "05 Mai 2026",
        "date_out": "15 Mai 2026",
        "market":   "NASDAQ",
        "currency": "USD",
    },
    {
        "ticker":   "PDD",
        "name":     "PDD Holdings",
        "qty":      5,
        "entry":    104.8490,
        "exit":     99.3900,
        "date_in":  "13 Abr 2026",
        "date_out": "07 Mai 2026",
        "market":   "NASDAQ",
        "currency": "USD",
    },
    {
        "ticker":   "QDV5.DE",
        "name":     "MSCI India",
        "qty":      220,
        "entry":    7.5477,
        "exit":     7.4400,
        "date_in":  "13 Abr 2026",
        "date_out": "23 Abr 2026",
        "market":   "XETRA",
        "currency": "EUR",
    },
    {
        "ticker":   "BCP.LS",
        "name":     "Millennium BCP",
        "qty":      1000,
        "entry":    0.9147,
        "exit":     0.9250,
        "date_in":  "13 Abr 2026",
        "date_out": "11 Mai 2026",
        "market":   "XLIS",
        "currency": "EUR",
    },
    {
        "ticker":   "CL=F",
        "name":     "WTI Crude Short",
        "qty":      1,
        "entry":    104.0000,
        "exit":     102.3000,
        "date_in":  "15 Mai 2026",
        "date_out": "15 Mai 2026",
        "market":   "COMMODITY",
        "currency": "USD",
    },
    {
        "ticker":   "CL=F",
        "name":     "WTI Crude Short 2",
        "qty":      1,
        "entry":    104.0000,
        "exit":     107.2800,
        "date_in":  "15 Mai 2026",
        "date_out": "15 Mai 2026",
        "market":   "COMMODITY",
        "currency": "USD",
    },
]

# ── HISTÓRICO P&L ────────────────────────────────────────────
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
    ("12 Mai", 124.61),
    ("13 Mai",   0.00),
    ("15 Mai",  54.00),
    ("18 Mai",   0.00),
]

# ── OUTPUT ───────────────────────────────────────────────────
DASHBOARD_FILE = "dashboard.html"
RESULTS_CSV    = "qdv3_results.csv"
RUN_DATE       = datetime.today().strftime("%d %b %Y — %H:%M")

# ── TELEGRAM ─────────────────────────────────────────────────
TELEGRAM_TOKEN   = "8865063923:AAGKpnOJh2QYgl-cOTE4SbRKRI"
TELEGRAM_CHAT_ID = "8797381859"