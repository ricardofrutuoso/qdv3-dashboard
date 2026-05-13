# ============================================================
# DEGIRO MASTER SCANNER v1
# QDV3 + Hedgeye Regime + Multi-Market Dynamic Universe
# Ready to paste into VS Code / Windows Python
# Free stack: pandas + numpy + yfinance
# ============================================================

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# ============================================================
# USER CONFIG
# ============================================================

DEGIRO_FILE = "degiro_universe.csv"   # Your exported DEGIRO file
TARGET_EXCHANGE = "EUREX"             # Example: EUREX / XPAR / XAMS
MAX_PRICE = 30.0
TOP_N = 15

# Filters
MIN_HURST = 0.55
MIN_ADX = 18
MIN_AVG_VOLUME = 100000

# Optional
STOCK_ONLY = True
EUR_ONLY = False

# ============================================================
# COLUMN MAPPING
# Adjust these to match your DEGIRO export
# ============================================================

COL_SYMBOL = "Symbol"
COL_NAME = "Name"
COL_EXCHANGE = "Exchange"
COL_TYPE = "Type"
COL_CURRENCY = "Currency"

# ============================================================
# DATA LOADER
# ============================================================

def load_degiro_universe(filepath):
    df = pd.read_csv(filepath)

    # Basic cleanup
    df = df.dropna(subset=[COL_SYMBOL, COL_EXCHANGE])

    if STOCK_ONLY and COL_TYPE in df.columns:
        df = df[df[COL_TYPE].str.contains("Stock", case=False, na=False)]

    if EUR_ONLY and COL_CURRENCY in df.columns:
        df = df[df[COL_CURRENCY] == "EUR"]

    return df


# ============================================================
# YAHOO SYMBOL MAPPING (adjust manually where needed)
# ============================================================

def degiro_to_yahoo(symbol, exchange):
    exchange_suffix = {
        "EUREX": ".DE",
        "XETRA": ".DE",
        "XPAR": ".PA",
        "XAMS": ".AS",
        "XMIL": ".MI",
        "XLIS": ".LS",
        "XMAD": ".MC",
        "XBRU": ".BR",
        "NASDAQ": "",
        "NYSE": "",
    }

    suffix = exchange_suffix.get(exchange, "")

    if symbol.endswith(suffix):
        return symbol

    return f"{symbol}{suffix}"


# ============================================================
# FETCH DATA
# ============================================================

def fetch_data(symbol, days=400):
    try:
        end = datetime.today()
        start = end - timedelta(days=days)

        df = yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return None

        return df.dropna()

    except:
        return None


# ============================================================
# INDICATORS
# ============================================================

def ema(series, period):
    return pd.Series(series).ewm(span=period).mean()

def hurst_exponent(series):
    try:
        series = np.array(series)
        lags = range(2, 20)

        tau = []
        for lag in lags:
            diff = np.subtract(series[lag:], series[:-lag])
            std = np.std(diff)

            if std > 0:
                tau.append(std)

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


def atr(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    return tr.rolling(period).mean()


def adx(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    atr_val = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr_val)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr_val)

    dx = abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_val = (dx * 100).rolling(period).mean()

    return float(adx_val.iloc[-1])


# ============================================================
# REGIME / SCORING
# ============================================================

def premium_discount(price, low52, high52):
    if high52 == low52:
        return 50
    return ((price - low52) / (high52 - low52)) * 100


def regime_state(price, ema21, ema55, adx_val):
    if price > ema21 > ema55 and adx_val > MIN_ADX:
        return "🟢 BULL"
    elif price < ema21 < ema55 and adx_val > MIN_ADX:
        return "🔴 BEAR"
    return "🟡 NEUTRAL"


def conviction_label(score):
    if score >= 8:
        return "🔥 VERY HIGH"
    elif score >= 6:
        return "💪 HIGH"
    elif score >= 4:
        return "⚠️ MEDIUM"
    return "❌ LOW"


def score_model(price, ema21, ema55, h, adx_val, pd_val, atr_pct, avg_vol):
    score = 0

    # Trend
    if price > ema21:
        score += 1
    if ema21 > ema55:
        score += 2

    # Hurst
    if h > 0.62:
        score += 2
    elif h > 0.55:
        score += 1

    # ADX
    if adx_val > 25:
        score += 2
    elif adx_val > 18:
        score += 1

    # P/D sweet spot
    if 20 <= pd_val <= 80:
        score += 2
    elif pd_val > 95 or pd_val < 5:
        score -= 2

    # Compression
    if atr_pct < 35:
        score += 1

    # Liquidity
    if avg_vol > MIN_AVG_VOLUME:
        score += 1

    return round(score, 2)


# ============================================================
# MAIN SCANNER
# ============================================================

def run_scanner():
    universe = load_degiro_universe(DEGIRO_FILE)

    universe = universe[universe[COL_EXCHANGE] == TARGET_EXCHANGE]

    if universe.empty:
        print(f"⚠️ No instruments found for {TARGET_EXCHANGE}")
        return

    results = []

    print("\n" + "=" * 100)
    print(f"DEGIRO MASTER SCANNER — {TARGET_EXCHANGE} — {datetime.today().strftime('%d %b %Y')}")
    print("=" * 100)

    for _, row in universe.iterrows():

        try:
            ticker = str(row[COL_SYMBOL]).strip()
            name = str(row[COL_NAME]).strip() if COL_NAME in row else ticker
            exchange = str(row[COL_EXCHANGE]).strip()

            yahoo_symbol = degiro_to_yahoo(ticker, exchange)

            df = fetch_data(yahoo_symbol)

            if df is None or len(df) < 120:
                continue

            closes = df["Close"].values.astype(float)

            price = float(closes[-1])

            if price > MAX_PRICE:
                continue

            avg_volume = float(df["Volume"].tail(20).mean())

            if avg_volume < MIN_AVG_VOLUME:
                continue

            ema21 = float(ema(closes, 21).iloc[-1])
            ema55 = float(ema(closes, 55).iloc[-1])

            h = hurst_exponent(closes[-100:])

            if h < MIN_HURST:
                continue

            adx_val = adx(df)

            atr_series = atr(df)
            atr_now = float(atr_series.iloc[-1])
            atr_pct = float(atr_series.rank(pct=True).iloc[-1] * 100)

            low52 = float(np.min(closes[-252:]))
            high52 = float(np.max(closes[-252:]))

            pd_val = premium_discount(price, low52, high52)

            regime = regime_state(price, ema21, ema55, adx_val)

            score = score_model(
                price,
                ema21,
                ema55,
                h,
                adx_val,
                pd_val,
                atr_pct,
                avg_volume
            )

            results.append({
                "Ticker": ticker,
                "Name": name,
                "Yahoo": yahoo_symbol,
                "Price": round(price, 2),
                "Regime": regime,
                "Score": score,
                "Conviction": conviction_label(score),
                "Hurst": round(h, 2),
                "ADX": round(adx_val, 2),
                "P/D %": round(pd_val, 1),
                "ATR %ile": round(atr_pct, 1),
                "ATR": round(atr_now, 2),
                "Avg Vol": int(avg_volume),
                "52W Low": round(low52, 2),
                "52W High": round(high52, 2),
            })

        except:
            continue

    if not results:
        print("⚠️ No valid setups found.")
        return

    # Rank
    results = sorted(results, key=lambda x: x["Score"], reverse=True)

    # Output
    for i, r in enumerate(results[:TOP_N], start=1):

        print(f"""
#{i} — {r['Ticker']} ({r['Name']})
Yahoo: {r['Yahoo']}
Price: {r['Price']}  |  {r['Regime']}
Score: {r['Score']} | Conviction: {r['Conviction']}

Hurst: {r['Hurst']} | ADX: {r['ADX']}
P/D: {r['P/D %']}% | ATR: {r['ATR']} | ATR %ile: {r['ATR %ile']}
Avg Volume: {r['Avg Vol']}
52W Range: {r['52W Low']} → {r['52W High']}
""")

    # Save CSV
    output_df = pd.DataFrame(results)
    output_name = f"scanner_results_{TARGET_EXCHANGE}.csv"
    output_df.to_csv(output_name, index=False)

    print("=" * 100)
    print(f"SCAN COMPLETE — Results saved to {output_name}")
    print("=" * 100)


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_scanner()