# ============================================================
# INDICATORS.PY — Todos os indicadores técnicos
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from config import LOOKBACK

def fetch(symbol):
    try:
        end   = datetime.today()
        start = end - timedelta(days=LOOKBACK)
        df    = yf.download(symbol, start=start, end=end,
                            progress=False, auto_adjust=True)
        if df.empty or len(df) < 60:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        cols = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
        return df[cols].dropna()
    except:
        return None

def hurst(series):
    try:
        s    = np.array(series, dtype=float).flatten()
        lags = range(2, 20)
        tau  = [np.std(np.subtract(s[l:], s[:-l])) for l in lags]
        tau  = [t for t in tau if t > 0]
        if len(tau) < 2:
            return 0.50
        poly = np.polyfit(np.log(range(2, 2+len(tau))), np.log(tau), 1)
        return float(np.clip(poly[0], 0.01, 0.99))
    except:
        return 0.50

def atr_series(df, p=14):
    h = df["High"].astype(float)
    l = df["Low"].astype(float)
    c = df["Close"].astype(float)
    tr = pd.concat([h-l,
                    (h-c.shift()).abs(),
                    (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()

def vol_percentile(df):
    atr = atr_series(df)
    return round(float(atr.rank(pct=True).iloc[-1]*100), 1)

def calc_adx(df, p=14):
    try:
        h   = df["High"].astype(float)
        l   = df["Low"].astype(float)
        c   = df["Close"].astype(float)
        pdm = h.diff().clip(lower=0)
        mdm = (-l.diff()).clip(lower=0)
        pdm[pdm < mdm] = 0
        mdm[mdm < pdm] = 0
        tr  = pd.concat([h-l,
                         (h-c.shift()).abs(),
                         (l-c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(p).mean()
        pdi = 100 * pdm.rolling(p).mean() / atr
        mdi = 100 * mdm.rolling(p).mean() / atr
        dx  = (abs(pdi-mdi)/(pdi+mdi)*100).rolling(p).mean()
        return round(float(dx.iloc[-1]), 1)
    except:
        return 0.0

def ema(series, p):
    return pd.Series(series).ewm(span=p).mean()

def zscore(series, w):
    if len(series) < w:
        return None
    s   = series[-w:]
    std = np.std(s)
    if std == 0:
        return 0.0
    return round(float((series[-1]-np.mean(s))/std), 2)

def brennan_compression(df):
    atr  = atr_series(df)
    vp   = float(atr.rank(pct=True).iloc[-1]*100)
    c    = df["Close"].astype(float).values
    h_n  = hurst(c[-30:])
    h_o  = hurst(c[-60:-30])
    h_roc= h_n - h_o
    if vp < 25 and h_roc > 0.03:
        return "🔥 COMPRESSION+TRENDING"
    if vp < 25:
        return "⚡ COMPRESSED"
    if vp > 75:
        return "💥 EXPANDING"
    return "〰️ NORMAL"

def fractal_levels(price, low52, high52, h):
    rm   = 1.1 if h > 0.55 else 0.9
    skew = 1.08
    ts, ns, als = 0.040*rm, 0.120*rm, 0.280*rm
    return {
        "trade": (round(price*(1-ts*skew),  4), round(price*(1+ts),      4)),
        "trend": (round(price*(1-ns*skew),  4), round(price*(1+ns),      4)),
        "tail":  (round(max(low52*0.95, price*(1-als*skew)), 4),
                  round(min(high52*1.05, price*(1+als)),     4)),
    }

def momentum_score(pd_c, pd_1w, pd_1m, roc, h):
    s  = 0
    s += 0.8 if pd_c  > 0 else -0.8
    s += 0.6 if pd_1w > 0 else -0.6
    s += 0.4 if pd_1m > 0 else -0.4
    s += 0.5 if roc   > 0 else -0.5
    s += 0.4 if h > 0.55 else (-0.4 if h < 0.45 else 0)
    return round(s, 2)

def signal_label(score):
    if score >=  0.6: return "BULLISH"
    if score <= -0.6: return "BEARISH"
    return "TURNING"

def conviction_label(score, h, vp, adx_v):
    pts  = 0
    pts += 2 if abs(score) >= 1.5 else (1 if abs(score) >= 0.8 else 0)
    pts += 2 if h > 0.62 else (1 if h > 0.55 else 0)
    pts += 1 if adx_v > 25 else 0
    pts += 1 if 15 < vp < 85 else 0
    if pts >= 5: return "MUITO ALTA"
    if pts >= 3: return "ALTA"
    if pts >= 2: return "MÉDIA"
    return "BAIXA"

def options_signal(score, h, vp):
    if abs(score) < 0.6:
        return "Aguardar"
    direction = "CALL" if score > 0 else "PUT"
    expiry    = "Monthly" if vp < 65 else "Weekly"
    conv      = "Alta" if h > 0.62 else ("Média" if h > 0.52 else "Baixa")
    return f"{direction} | {expiry} | {conv}"

def analyse(symbol, name, market):
    """
    Analisa um ticker e devolve dict completo.
    Retorna None se não houver dados suficientes.
    """
    df = fetch(symbol)
    if df is None:
        return None

    closes = df["Close"].astype(float).values.flatten()
    if len(closes) < 25:
        return None

    price = float(closes[-1])
    p1d   = float(closes[-2])  if len(closes) > 1  else price
    p2d   = float(closes[-3])  if len(closes) > 2  else p1d
    p1w   = float(closes[-6])  if len(closes) > 5  else price
    p1m   = float(closes[-22]) if len(closes) > 21 else price

    low52  = float(np.min(closes[-252:]))
    high52 = float(np.max(closes[-252:]))

    pd_c   = round((price-p1d)/p1d*100,                              2)
    pd_y   = round((p1d  -p2d)/p2d*100,                              2)
    pd_1w  = round((price-p1w)/p1w*100,                              2)
    pd_1m  = round((price-p1m)/p1m*100,                              2)
    pd_str = round((price-(low52+high52)/2)/((low52+high52)/2)*100,  2)
    roc    = round(pd_c - pd_y,                                       2)

    h_d    = hurst(closes[-30:]) if len(closes) >= 30 else 0.50
    h_w    = hurst(closes[-60:]) if len(closes) >= 60 else 0.50
    h_roc  = round(h_d - h_w, 2)

    vp     = vol_percentile(df) if "High" in df.columns else 50.0
    comp   = brennan_compression(df) if "High" in df.columns else "N/A"
    adx_v  = calc_adx(df) if "High" in df.columns else 0.0
    ttmz   = zscore(closes, min(252, len(closes)))
    yr3z   = zscore(closes, min(756, len(closes)))

    avg_vol = float(df["Volume"].tail(20).mean()) \
              if "Volume" in df.columns else 0

    score  = momentum_score(pd_c, pd_1w, pd_1m, roc, h_d)
    sig    = signal_label(score)
    conv   = conviction_label(score, h_d, vp, adx_v)
    opt    = options_signal(score, h_d, vp)
    lvl    = fractal_levels(price, low52, high52, h_d)

    h_sig  = "a enfraquecer" if h_roc < -0.03 else \
             "a fortalecer"  if h_roc >  0.03 else "estável"

    pfmt   = f"{price:.4f}" if price < 10 else \
             f"{price:.3f}" if price < 100 else f"{price:.2f}"

    from config import DEGIRO_COMMISSIONS
    comm = DEGIRO_COMMISSIONS.get(market, 3.90)

    return {
        "symbol":  symbol,  "name":    name,
        "market":  market,  "price":   price,
        "pfmt":    pfmt,    "score":   score,
        "signal":  sig,     "conv":    conv,
        "h_d":     round(h_d, 2),
        "h_w":     round(h_w, 2),
        "h_roc":   h_roc,   "h_sig":   h_sig,
        "vp":      vp,      "comp":    comp,
        "adx":     adx_v,   "ttmz":    ttmz,
        "yr3z":    yr3z,    "pd_str":  pd_str,
        "pd_c":    pd_c,    "pd_y":    pd_y,
        "pd_1w":   pd_1w,   "pd_1m":   pd_1m,
        "roc":     roc,     "lvl":     lvl,
        "opt":     opt,     "comm":    comm,
        "avg_vol": avg_vol, "low52":   low52,
        "high52":  high52,
    }