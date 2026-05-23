# ============================================================
# INDICATORS.PY — Todos os indicadores técnicos QDV3 v2
# DFA Hurst | P/D VWAP | ATR | ADX | Brennan
# Kurtosis | Skewness | Z-Volume | Risk Score
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from config import LOOKBACK

# ── FETCH ────────────────────────────────────────────────────
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
        cols = [c for c in ["Open","High","Low","Close","Volume"]
                if c in df.columns]
        return df[cols].dropna()
    except:
        return None

# ── HURST DFA (Detrended Fluctuation Analysis) ───────────────
def hurst_dfa(series):
    """
    DFA — mais robusto que R/S para séries financeiras
    Expoente DFA ≈ H de Hurst
    > 0.55 = trending | < 0.45 = reversão | ~0.5 = random
    """
    try:
        s = np.array(series, dtype=float).flatten()
        n = len(s)
        if n < 20:
            return 0.50
        # Profile — série acumulada de desvios da média
        profile  = np.cumsum(s - s.mean())
        max_box  = n // 4
        box_sizes = np.unique(
            np.logspace(np.log10(4), np.log10(max(max_box,5)),
                        20).astype(int)
        )
        fluctuations = []
        valid_boxes  = []
        for box in box_sizes:
            if box < 4 or box > n // 2:
                continue
            n_boxes = n // box
            if n_boxes < 4:
                continue
            rms_list = []
            for j in range(n_boxes):
                segment = profile[j*box:(j+1)*box]
                x       = np.arange(len(segment))
                coeffs  = np.polyfit(x, segment, 1)
                trend   = np.polyval(coeffs, x)
                residual= segment - trend
                rms_list.append(np.sqrt(np.mean(residual**2)))
            if rms_list:
                fluctuations.append(np.mean(rms_list))
                valid_boxes.append(box)
        if len(valid_boxes) < 4:
            return hurst_rs(s)  # fallback
        poly = np.polyfit(np.log(valid_boxes),
                          np.log(fluctuations), 1)
        return float(np.clip(poly[0], 0.01, 0.99))
    except:
        return 0.50

def hurst_rs(series):
    """Hurst clássico R/S — fallback"""
    try:
        s    = np.array(series, dtype=float).flatten()
        lags = range(2, 20)
        tau  = [np.std(np.subtract(s[l:], s[:-l])) for l in lags]
        tau  = [t for t in tau if t > 0]
        if len(tau) < 2:
            return 0.50
        poly = np.polyfit(np.log(range(2, 2+len(tau))),
                          np.log(tau), 1)
        return float(np.clip(poly[0], 0.01, 0.99))
    except:
        return 0.50

# Alias principal — usa DFA
def hurst(series):
    return hurst_dfa(series)

# ── ATR ──────────────────────────────────────────────────────
def atr_series(df, p=14):
    h  = df["High"].astype(float)
    l  = df["Low"].astype(float)
    c  = df["Close"].astype(float)
    tr = pd.concat([h-l,
                    (h-c.shift()).abs(),
                    (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()

# ── VOL PERCENTILE ───────────────────────────────────────────
def vol_percentile(df):
    atr = atr_series(df)
    return round(float(atr.rank(pct=True).iloc[-1]*100), 1)

# ── ADX ──────────────────────────────────────────────────────
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

# ── ZSCORE ───────────────────────────────────────────────────
def zscore(series, w):
    if len(series) < w:
        return None
    s   = series[-w:]
    std = np.std(s)
    if std == 0:
        return 0.0
    return round(float((series[-1]-np.mean(s))/std), 2)

# ── VWAP ─────────────────────────────────────────────────────
def vwap(df, periods):
    try:
        n = min(periods, len(df))
        c = df["Close"].astype(float).tail(n)
        if "Volume" in df.columns:
            v = df["Volume"].astype(float).tail(n)
            v = v.replace(0, np.nan).fillna(c.mean())
            if v.sum() == 0:
                return float(c.mean())
            return float((c * v).sum() / v.sum())
        return float(c.mean())
    except:
        return float(df["Close"].astype(float).tail(periods).mean())

# ── PREMIUM / DISCOUNT via VWAP ──────────────────────────────
def calc_pd(df, price):
    try:
        vwap_c   = vwap(df, 5)
        vwap_y   = vwap(df, 10)
        vwap_1w  = vwap(df, 22)
        vwap_1m  = vwap(df, 66)
        vwap_str = vwap(df, min(252, len(df)))

        def pd_calc(v):
            return round((price-v)/v*100, 2) if v and v>0 else 0.0

        pd_c   = pd_calc(vwap_c)
        pd_y   = pd_calc(vwap_y)
        pd_1w  = pd_calc(vwap_1w)
        pd_1m  = pd_calc(vwap_1m)
        pd_str = pd_calc(vwap_str)
        roc    = round(pd_c - pd_y, 2)
        return pd_c, pd_y, pd_1w, pd_1m, pd_str, roc
    except:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

# ── VOLUME Z-SCORE ───────────────────────────────────────────
def volume_zscore(df, window=252):
    try:
        if "Volume" not in df.columns:
            return None, None, None
        vol = df["Volume"].astype(float)
        vol = vol.replace(0, np.nan).dropna()
        if len(vol) < 30:
            return None, None, None
        log_vol   = np.log(vol + 1)
        w         = min(window, len(log_vol))
        mean      = float(log_vol.tail(w).mean())
        std       = float(log_vol.tail(w).std())
        if std == 0:
            return None, None, None
        current_z = float((log_vol.iloc[-1] - mean) / std)
        vol_roc   = None
        if len(log_vol) >= 6:
            past = log_vol.iloc[-6]
            vol_roc = round(float(
                (log_vol.iloc[-1]-past)/abs(past)*100
            ), 2) if past != 0 else None
        if current_z > 3.0:
            label = "PANICO — volume extremo"
        elif current_z > 2.0:
            label = "STRESS — volume elevado"
        elif current_z > 1.5:
            label = "ATENCAO — volume acima"
        elif current_z < -1.5:
            label = "SECO — complacencia"
        else:
            label = "NORMAL"
        return round(current_z, 2), vol_roc, label
    except:
        return None, None, None

# ── FAT TAIL ANALYSIS ────────────────────────────────────────
def fat_tail_analysis(df):
    try:
        from scipy.stats import kurtosis as sp_kurt, skew as sp_skew
        closes  = df["Close"].astype(float)
        returns = closes.pct_change().dropna()
        if len(returns) < 30:
            return None
        kurt     = float(sp_kurt(returns))
        skewness = float(sp_skew(returns))
        std      = float(returns.std())
        mean     = float(returns.mean())
        extreme  = returns[abs(returns - mean) > 2 * std]
        pct_ext  = len(extreme) / len(returns) * 100
        kurt_vel = None
        skew_vel = None
        if len(returns) >= 44:
            kurt_past = float(sp_kurt(returns.iloc[-44:-22]))
            skew_past = float(sp_skew(returns.iloc[-44:-22]))
            if kurt_past != 0:
                kurt_vel = round((kurt-kurt_past)/abs(kurt_past)*100, 1)
            if skew_past != 0:
                skew_vel = round((skewness-skew_past)/abs(skew_past)*100, 1)
        return {
            "kurt":     round(kurt, 2),
            "skew":     round(skewness, 2),
            "pct_ext":  round(pct_ext, 1),
            "kurt_vel": kurt_vel,
            "skew_vel": skew_vel,
        }
    except:
        return None

# ── RISK COMPOSITE SCORE ─────────────────────────────────────
def risk_composite_score(r, df):
    try:
        from scipy.stats import kurtosis as sp_kurt, skew as sp_skew
        closes  = df["Close"].astype(float)
        returns = closes.pct_change().dropna()
        if len(returns) < 30:
            return 0, [], "SEM DADOS"
        score = 0
        flags = []
        std   = float(returns.std())
        mean  = float(returns.mean())
        # 1. Kurtosis
        kurt     = float(sp_kurt(returns))
        kurt_vel = None
        if len(returns) >= 44:
            kp = float(sp_kurt(returns.iloc[-44:-22]))
            if kp != 0:
                kurt_vel = (kurt-kp)/abs(kp)*100
        k_score = 20 if kurt>7 else 13 if kurt>3 else 6 if kurt>1 else 0
        if kurt_vel and kurt_vel > 50 and k_score > 0:
            k_score = min(20, k_score+4)
            flags.append("Kurtosis acelerando")
        score += k_score
        if k_score >= 20: flags.append(f"Kurtosis severa ({kurt:.1f})")
        elif k_score >= 13: flags.append(f"Kurtosis elevada ({kurt:.1f})")
        # 2. Skewness
        skewness = float(sp_skew(returns))
        s_score  = 20 if skewness<-2 else 13 if skewness<-1 else 6 if skewness<-0.5 else 0
        score   += s_score
        if s_score >= 20: flags.append(f"Skew muito negativo ({skewness:.2f})")
        elif s_score >= 13: flags.append(f"Skew negativo ({skewness:.2f})")
        # 3. Extremos
        extreme = returns[abs(returns-mean) > 2*std]
        pct_ext = len(extreme)/len(returns)*100
        e_score = 20 if pct_ext>10 else 13 if pct_ext>8 else 6 if pct_ext>6 else 0
        score  += e_score
        if e_score >= 13: flags.append(f"Extremos elevados ({pct_ext:.1f}%)")
        # 4. Z-Score posição
        try:
            z     = abs(float(r.get("ttmz", 0) or 0))
            z3    = abs(float(r.get("yr3z", 0) or 0))
            z_max = max(z, z3)
            z_s   = 20 if z_max>2.5 else 13 if z_max>2.0 else 6 if z_max>1.5 else 0
            score += z_s
            if z_s >= 13: flags.append(f"Z-Score elevado ({z_max:.1f}s)")
        except:
            pass
        # 5. Volume Z
        vol_z, vol_roc, vol_label = volume_zscore(df)
        if vol_z is not None:
            v_s = 20 if vol_z>3 else 13 if vol_z>2 else 6 if vol_z>1.5 else 0
            if vol_roc and abs(vol_roc)>50 and v_s>0:
                v_s = min(20, v_s+4)
                flags.append("Volume acelerando")
            score += v_s
            if v_s >= 13: flags.append(f"Volume stress (Z:{vol_z:.1f})")
        final = round(min(score, 100), 1)
        if final >= 80:   label = "RISCO MAXIMO"
        elif final >= 60: label = "RISCO ALTO"
        elif final >= 40: label = "RISCO MODERADO"
        elif final >= 20: label = "RISCO BAIXO"
        else:             label = "NORMAL"
        return final, flags, label
    except:
        return 0, [], "ERRO"

# ── BRENNAN COMPRESSION ──────────────────────────────────────
def brennan_compression(df):
    atr  = atr_series(df)
    vp   = float(atr.rank(pct=True).iloc[-1]*100)
    c    = df["Close"].astype(float).values
    h_n  = hurst(c[-30:])
    h_o  = hurst(c[-60:-30])
    h_roc= h_n - h_o
    if vp < 25 and h_roc > 0.03:
        return "COMPRESSION+TRENDING"
    if vp < 25:
        return "COMPRESSED"
    if vp > 75:
        return "EXPANDING"
    return "NORMAL"

# ── FRACTAL LEVELS ───────────────────────────────────────────
def fractal_levels(price, low52, high52, h):
    rm   = 1.1 if h > 0.55 else 0.9
    skew = 1.08
    ts, ns, als = 0.040*rm, 0.120*rm, 0.280*rm
    return {
        "trade": (round(price*(1-ts*skew), 4),
                  round(price*(1+ts),      4)),
        "trend": (round(price*(1-ns*skew), 4),
                  round(price*(1+ns),      4)),
        "tail":  (round(max(low52*0.95, price*(1-als*skew)), 4),
                  round(min(high52*1.05, price*(1+als)),     4)),
    }

# ── MOMENTUM SCORE ───────────────────────────────────────────
def momentum_score(pd_c, pd_1w, pd_1m, roc, h):
    s  = 0
    s += 0.8 if pd_c  > 0 else -0.8
    s += 0.6 if pd_1w > 0 else -0.6
    s += 0.4 if pd_1m > 0 else -0.4
    s += 0.5 if roc   > 0 else -0.5
    s += 0.4 if h > 0.55 else (-0.4 if h < 0.45 else 0)
    return round(s, 2)

# ── SIGNAL LABEL ─────────────────────────────────────────────
def signal_label(score):
    if score >=  0.6: return "BULLISH"
    if score <= -0.6: return "BEARISH"
    return "TURNING"

# ── CONVICTION LABEL ─────────────────────────────────────────
def conviction_label(score, h, vp, adx_v):
    pts  = 0
    pts += 2 if abs(score) >= 1.5 else (1 if abs(score) >= 0.8 else 0)
    pts += 2 if h > 0.62 else (1 if h > 0.55 else 0)
    pts += 1 if adx_v > 25 else 0
    pts += 1 if 15 < vp < 85 else 0
    if pts >= 5: return "MUITO ALTA"
    if pts >= 3: return "ALTA"
    if pts >= 2: return "MEDIA"
    return "BAIXA"

# ── OPTIONS SIGNAL ───────────────────────────────────────────
def options_signal(score, h, vp):
    if abs(score) < 0.6:
        return "Aguardar"
    direction = "CALL" if score > 0 else "PUT"
    expiry    = "Monthly" if vp < 65 else "Weekly"
    conv      = "Alta"  if h > 0.62 else "Media" if h > 0.52 else "Baixa"
    return f"{direction} | {expiry} | {conv}"

# ── ANALYSE ──────────────────────────────────────────────────
def analyse(symbol, name, market):
    df = fetch(symbol)
    if df is None:
        return None
    closes = df["Close"].astype(float).values.flatten()
    if len(closes) < 25:
        return None
    price  = float(closes[-1])
    low52  = float(np.min(closes[-252:])) if len(closes)>=252 else float(np.min(closes))
    high52 = float(np.max(closes[-252:])) if len(closes)>=252 else float(np.max(closes))
    # P/D via VWAP
    pd_c, pd_y, pd_1w, pd_1m, pd_str, roc = calc_pd(df, price)
    # Hurst DFA
    h_d   = hurst(closes[-30:]) if len(closes) >= 30 else 0.50
    h_w   = hurst(closes[-60:]) if len(closes) >= 60 else 0.50
    h_roc = round(h_d - h_w, 2)
    h_sig = "a enfraquecer" if h_roc < -0.03 else \
            "a fortalecer"  if h_roc >  0.03 else "estavel"
    # Vol / ADX / Brennan
    vp    = vol_percentile(df)      if "High" in df.columns else 50.0
    comp  = brennan_compression(df) if "High" in df.columns else "N/A"
    adx_v = calc_adx(df)            if "High" in df.columns else 0.0
    # Z-Scores
    ttmz  = zscore(closes, min(252, len(closes)))
    yr3z  = zscore(closes, min(756, len(closes)))
    # Volume
    avg_vol = float(df["Volume"].tail(20).mean()) \
              if "Volume" in df.columns else 0
    # Score / Signal
    score = momentum_score(pd_c, pd_1w, pd_1m, roc, h_d)
    sig   = signal_label(score)
    conv  = conviction_label(score, h_d, vp, adx_v)
    opt   = options_signal(score, h_d, vp)
    lvl   = fractal_levels(price, low52, high52, h_d)
    # Fat tail
    fat = fat_tail_analysis(df)
    # Volume Z-Score
    vol_z, vol_roc, vol_label = volume_zscore(df)
    # Risk Score
    r_temp = {"ttmz": ttmz, "yr3z": yr3z}
    risk_score, risk_flags, risk_label = risk_composite_score(r_temp, df)
    # Formato preço
    pfmt = f"{price:.4f}" if price < 10 else \
           f"{price:.3f}" if price < 100 else f"{price:.2f}"
    from config import DEGIRO_COMMISSIONS
    comm = DEGIRO_COMMISSIONS.get(market, 3.90)
    return {
        "symbol":     symbol,    "name":      name,
        "market":     market,    "price":     price,
        "pfmt":       pfmt,      "score":     score,
        "signal":     sig,       "conv":      conv,
        "h_d":        round(h_d, 2),
        "h_w":        round(h_w, 2),
        "h_roc":      h_roc,     "h_sig":     h_sig,
        "vp":         vp,        "comp":      comp,
        "adx":        adx_v,     "ttmz":      ttmz,
        "yr3z":       yr3z,      "pd_str":    pd_str,
        "pd_c":       pd_c,      "pd_y":      pd_y,
        "pd_1w":      pd_1w,     "pd_1m":     pd_1m,
        "roc":        roc,       "lvl":       lvl,
        "opt":        opt,       "comm":      comm,
        "avg_vol":    avg_vol,   "low52":     low52,
        "high52":     high52,
        "kurt":       fat["kurt"]    if fat else 0,
        "skew":       fat["skew"]    if fat else 0,
        "pct_ext":    fat["pct_ext"] if fat else 0,
        "kurt_vel":   fat["kurt_vel"] if fat else None,
        "skew_vel":   fat["skew_vel"] if fat else None,
        "vol_z":      vol_z,
        "vol_roc":    vol_roc,
        "vol_label":  vol_label,
        "risk_score": risk_score,
        "risk_flags": risk_flags,
        "risk_label": risk_label,
    }