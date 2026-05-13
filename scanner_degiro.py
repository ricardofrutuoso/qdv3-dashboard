# ============================================================
# QDV3 MASTER OPPORTUNITY SCANNER v5
# Long Bias | Stocks + Options + ETFs | Opportunity > Price
# Clean Dashboard + Search + Market Filters
# Paste directly into VS Code
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# USER SETTINGS (EDIT ONLY THESE)
# ============================================================

CAPITAL               = 1000        # Your capital
RISK_PER_TRADE_PCT    = 0.10        # 10% ideal risk
TOP_N                 = 25
LOOKBACK              = 400
MIN_HURST             = 0.50
MIN_VOLUME            = 50000
MARKET_FILTER         = "ALL"       # ALL / NASDAQ / XETRA / XLIS etc
SEARCH_TERM           = ""          # "oil", "bank", "ai", etc
LONG_BIAS             = True        # Prefer bullish but still show bearish
INCLUDE_VIX           = True

# ============================================================
# UNIVERSE
# Expand freely
# ============================================================

UNIVERSE = [
     # ── FX MAJORS ─────────────────────────────
    ("EURUSD=X", "EUR/USD", "FX"),
    ("GBPUSD=X", "GBP/USD", "FX"),
    ("USDJPY=X", "USD/JPY", "FX"),
    ("AUDUSD=X", "AUD/USD", "FX"),
    ("USDCAD=X", "USD/CAD", "FX"),
    ("USDCHF=X", "USD/CHF", "FX"),
    ("NZDUSD=X", "NZD/USD", "FX"),

    # ── DOLLAR INDEX / MACRO FX ──────────────
    ("DX-Y.NYB", "US Dollar Index", "MACRO"),
    ("UUP", "Dollar Bull ETF", "MACRO"),
    ("FXE", "Euro ETF", "MACRO"),
    ("FXY", "Yen ETF", "MACRO"),

    # ── ENERGY ───────────────────────────────
    ("CL=F", "WTI Crude Oil", "COMMODITY"),
    ("BZ=F", "Brent Crude", "COMMODITY"),
    ("NG=F", "Natural Gas", "COMMODITY"),
    ("RB=F", "RBOB Gasoline", "COMMODITY"),
    ("HO=F", "Heating Oil", "COMMODITY"),
    ("XLE", "Energy Sector ETF", "COMMODITY"),

    # ── PRECIOUS METALS ──────────────────────
    ("GC=F", "Gold", "COMMODITY"),
    ("SI=F", "Silver", "COMMODITY"),
    ("PL=F", "Platinum", "COMMODITY"),
    ("PA=F", "Palladium", "COMMODITY"),
    ("GLD", "Gold ETF", "COMMODITY"),
    ("SLV", "Silver ETF", "COMMODITY"),

    # ── INDUSTRIAL METALS ────────────────────
    ("HG=F", "Copper", "COMMODITY"),
    ("CPER", "Copper ETF", "COMMODITY"),

    # ── AGRICULTURE ──────────────────────────
    ("ZC=F", "Corn", "COMMODITY"),
    ("ZW=F", "Wheat", "COMMODITY"),
    ("ZS=F", "Soybeans", "COMMODITY"),
    ("KC=F", "Coffee", "COMMODITY"),
    ("SB=F", "Sugar", "COMMODITY"),
    ("CC=F", "Cocoa", "COMMODITY"),
    ("DBA", "Agriculture ETF", "COMMODITY"),

    # ── RATES / BONDS ───────────────────────
    ("ZB=F", "US 30Y Bond", "RATES"),
    ("ZN=F", "US 10Y Note", "RATES"),
    ("TLT", "20Y Treasury ETF", "RATES"),
    ("IEF", "7-10Y Treasury ETF", "RATES"),

    # ── VOL / FEAR ──────────────────────────
    ("^VIX", "VIX", "VOL"),
    ("VXX", "VIX ETF", "VOL"),

    # ── CRYPTO ──────────────────────────────
    ("BTC-USD", "Bitcoin", "CRYPTO"),
    ("ETH-USD", "Ethereum", "CRYPTO"),
    ("MSTR", "MicroStrategy", "CRYPTO"),
    ("COIN", "Coinbase", "CRYPTO"),
    ("AAPL", "Apple", "NASDAQ"),
    ("MSFT", "Microsoft", "NASDAQ"),
    ("NVDA", "Nvidia", "NASDAQ"),
    ("AMD", "AMD", "NASDAQ"),
    ("META", "Meta", "NASDAQ"),
    ("AMZN", "Amazon", "NASDAQ"),
    ("GOOGL", "Alphabet", "NASDAQ"),
    ("TSLA", "Tesla", "NASDAQ"),
    ("BABA", "Alibaba", "NYSE"),
    ("PDD", "PDD", "NASDAQ"),
    ("QQQ", "QQQ ETF", "NASDAQ"),
    ("SPY", "SPY ETF", "NYSE"),
    ("XOM", "Exxon", "NYSE"),
    ("CVX", "Chevron", "NYSE"),
    ("SHEL", "Shell", "NYSE"),
    ("TTE", "TotalEnergies", "NYSE"),
    ("SAN.MC", "Santander", "XMAD"),
    ("BBVA.MC", "BBVA", "XMAD"),
    ("BCP.LS", "BCP", "XLIS"),
    ("EDP.LS", "EDP", "XLIS"),
    ("GALP.LS", "Galp", "XLIS"),
    ("SAP.DE", "SAP", "XETRA"),
    ("IFX.DE", "Infineon", "XETRA"),
    ("SIE.DE", "Siemens", "XETRA"),
    ("AIR.PA", "Airbus", "XPAR"),
    ("MC.PA", "LVMH", "XPAR"),
    ("ASML.AS", "ASML", "XAMS"),
    ("IWDA.AS", "MSCI World", "XAMS"),
    ("VUSA.AS", "SP500 EUR", "XAMS"),
    ("^VIX", "VIX", "INDEX"),
]

# ============================================================
# FETCH
# ============================================================

def fetch(symbol):
    try:
        end = datetime.today()
        start = end - timedelta(days=LOOKBACK)

        df = yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True
        )

        if df.empty or len(df) < 60:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    except:
        return None

# ============================================================
# CORE INDICATORS
# ============================================================

def ema(series, period):
    return pd.Series(series).ewm(span=period).mean()

def hurst(series):
    try:
        s = np.array(series, dtype=float)

        lags = range(2, 20)

        tau = [np.std(np.subtract(s[lag:], s[:-lag])) for lag in lags]
        tau = [x for x in tau if x > 0]

        if len(tau) < 2:
            return 0.50

        poly = np.polyfit(
            np.log(range(2, 2 + len(tau))),
            np.log(tau),
            1
        )

        return float(np.clip(poly[0], 0.01, 0.99))

    except:
        return 0.50

def atr(df, p=14):
    h = df["High"]
    l = df["Low"]
    c = df["Close"]

    tr = pd.concat([
        h - l,
        (h - c.shift()).abs(),
        (l - c.shift()).abs()
    ], axis=1).max(axis=1)

    return tr.rolling(p).mean()

def adx(df, p=14):
    try:
        h = df["High"]
        l = df["Low"]
        c = df["Close"]

        plus_dm = h.diff()
        minus_dm = -l.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr = pd.concat([
            h - l,
            (h - c.shift()).abs(),
            (l - c.shift()).abs()
        ], axis=1).max(axis=1)

        atr_val = tr.rolling(p).mean()

        plus_di = 100 * (plus_dm.rolling(p).mean() / atr_val)
        minus_di = 100 * (minus_dm.rolling(p).mean() / atr_val)

        dx = abs(plus_di - minus_di) / (plus_di + minus_di)
        adx_val = (dx * 100).rolling(p).mean()

        return float(adx_val.iloc[-1])

    except:
        return 0.0

# ============================================================
# REGIME + SIGNALS
# ============================================================

def market_signal(price, ema21, ema55, h, adx_val):
    if price > ema21 > ema55 and h > 0.55:
        if adx_val > 25:
            return "🟢 STRONG BULL"
        return "🟢 BULL"

    if price < ema21 < ema55 and h > 0.55:
        if adx_val > 25:
            return "🔴 STRONG BEAR"
        return "🔴 BEAR"

    return "🟡 TRANSITION"

def strategy_label(signal, vp, pd_struct):
    if "BULL" in signal:
        if vp < 25:
            return "📈 STOCK / LEAPS / CALL"
        if pd_struct < 20:
            return "📈 EARLY TREND"
        if pd_struct > 60:
            return "⚠️ BULL EXTENDED"
        return "📈 MOMENTUM LONG"

    if "BEAR" in signal:
        if vp < 25:
            return "📉 PUT / SHORT WATCH"
        return "🔻 RISK-OFF"

    return "⏳ WATCHLIST"

def conviction(score):
    if score >= 12:
        return "🔥 ELITE"
    elif score >= 9:
        return "💪 HIGH"
    elif score >= 6:
        return "⚠️ MEDIUM"
    return "❌ LOW"

# ============================================================
# OPPORTUNITY SCORE
# ============================================================

def opportunity_score(price, ema21, ema55, h, adx_val, vp, pd_struct, long_bias=True):
    score = 0

    # Trend structure
    if price > ema21:
        score += 2
    else:
        score -= 2

    if ema21 > ema55:
        score += 3
    else:
        score -= 3

    # Hurst
    if h > 0.62:
        score += 3
    elif h > 0.55:
        score += 2
    elif h < 0.45:
        score -= 2

    # ADX
    if adx_val > 25:
        score += 2
    elif adx_val > 18:
        score += 1

    # Compression / expansion
    if vp < 25:
        score += 2
    elif vp > 80:
        score -= 2

    # Structural opportunity
    if pd_struct < -20:
        score += 3
    elif pd_struct < 20:
        score += 2
    elif pd_struct > 70:
        score -= 3

    # Long bias
    if long_bias and score < 0:
        score *= 0.7

    return round(score, 2)

# ============================================================
# MAIN
# ============================================================

def run_scanner():

    results = []

    print("\nRunning QDV3 MASTER OPPORTUNITY SCANNER...\n")

    for symbol, name, market in UNIVERSE:

        try:
            if MARKET_FILTER != "ALL" and market != MARKET_FILTER:
                continue

            search_blob = f"{symbol} {name} {market}".lower()
            if SEARCH_TERM and SEARCH_TERM.lower() not in search_blob:
                continue

            if not INCLUDE_VIX and symbol == "^VIX":
                continue

            df = fetch(symbol)

            if df is None:
                continue

            closes = df["Close"].values.astype(float)

            avg_volume = float(df["Volume"].tail(20).mean())

            if avg_volume < MIN_VOLUME and symbol != "^VIX":
                continue

            price = float(closes[-1])

            low52 = float(np.min(closes[-252:]))
            high52 = float(np.max(closes[-252:]))

            mid = (low52 + high52) / 2
            pd_struct = ((price - mid) / mid) * 100

            h = hurst(closes[-100:])

            if h < MIN_HURST and symbol != "^VIX":
                continue

            ema21 = float(ema(closes, 21).iloc[-1])
            ema55 = float(ema(closes, 55).iloc[-1])

            adx_val = adx(df)

            atr_series = atr(df)
            vp = float(atr_series.rank(pct=True).iloc[-1] * 100)

            score = opportunity_score(
                price,
                ema21,
                ema55,
                h,
                adx_val,
                vp,
                pd_struct,
                LONG_BIAS
            )

            signal = market_signal(price, ema21, ema55, h, adx_val)

            strat = strategy_label(signal, vp, pd_struct)

            ideal_risk = CAPITAL * RISK_PER_TRADE_PCT

            results.append({
                "Ticker": symbol,
                "Name": name,
                "Market": market,
                "Price": round(price, 2),
                "Signal": signal,
                "Strategy": strat,
                "Opportunity Score": score,
                "Conviction": conviction(score),
                "Hurst": round(h, 2),
                "ADX": round(adx_val, 2),
                "Vol %ile": round(vp, 1),
                "P/D Struct %": round(pd_struct, 2),
                "52W Low": round(low52, 2),
                "52W High": round(high52, 2),
                "Ideal Risk €": round(ideal_risk, 2),
                "Avg Volume": int(avg_volume),
            })

        except:
            continue

    if not results:
        print("No setups found.")
        return

    dashboard = pd.DataFrame(results)

    dashboard = dashboard.sort_values(
        by="Opportunity Score",
        ascending=False
    )

    # Save outputs
    dashboard.to_csv("qdv3_dashboard.csv", index=False)

    try:
        dashboard.to_excel("qdv3_dashboard.xlsx", index=False)
    except:
        pass

    # Terminal preview
    print("=" * 120)
    print(f"TOP {TOP_N} MARKET OPPORTUNITIES")
    print("=" * 120)

    print(
        dashboard.head(TOP_N)[[
            "Ticker",
            "Name",
            "Market",
            "Price",
            "Signal",
            "Strategy",
            "Opportunity Score",
            "Conviction",
            "Hurst",
            "ADX",
            "Vol %ile",
            "P/D Struct %"
        ]]
    )

    print("\nFiles created:")
    print("qdv3_dashboard.csv")
    print("qdv3_dashboard.xlsx (if openpyxl installed)")
    print("\nDone.")

# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_scanner()