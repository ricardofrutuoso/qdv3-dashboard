# ============================================================
# SCANNER_VOLATILITY.PY — Vol Universe + PCC + Market Risk
# VIX | VXN | SKEW | VVIX | PCC | Risk Score Global
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from config import RUN_DATE, TOP_N

VOL_TICKERS = [
    ("^VIX",   "VIX S&P500",      "VOL"),
    ("^VXN",   "VXN Nasdaq",      "VOL"),
    ("^RVX",   "RVX Russell",     "VOL"),
    ("^VXD",   "VXD Dow",         "VOL"),
    ("^OVX",   "OVX Oil",         "VOL"),
    ("^GVZ",   "GVZ Gold",        "VOL"),
    ("^EVZ",   "EVZ Euro",        "VOL"),
    ("^VVIX",  "VVIX Vol of VIX", "VOL"),
    ("^SKEW",  "SKEW Tail Risk",  "VOL"),
    ("VXX",    "VIX ETF",         "VOL"),
]

PCC_TICKERS = [
    ("^PCC",   "Put/Call Total",  "SENTIMENT"),
    ("^PCCE",  "Put/Call Equity", "SENTIMENT"),
    ("^PCCI",  "Put/Call Index",  "SENTIMENT"),
]

def fetch(symbol, days=400):
    try:
        end   = datetime.today()
        start = end - timedelta(days=days)
        df    = yf.download(symbol, start=start, end=end,
                            progress=False, auto_adjust=True)
        if df.empty or len(df) < 20:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except:
        return None

def zscore(series, w):
    if len(series) < w:
        return None
    s   = series[-w:]
    std = np.std(s)
    if std == 0:
        return 0.0
    return round(float((series[-1]-np.mean(s))/std), 2)

def velocity(series, window=5):
    try:
        if len(series) < window + 1:
            return None
        current = float(series.iloc[-1])
        past    = float(series.iloc[-window])
        if past == 0:
            return None
        return round((current - past) / abs(past) * 100, 2)
    except:
        return None

def calc_market_risk_score(vol_results, pcc_results, vix_level):
    score = 0
    flags = []
    # VIX (25 pts)
    vix = next((r for r in vol_results if r["symbol"]=="^VIX"), None)
    if vix:
        v = vix["price"]
        v_vel = vix.get("vel_5d")
        v_score = 25 if v>=35 else 16 if v>=25 else 8 if v>=20 else 0
        if v_vel and v_vel > 30 and v_score > 0:
            v_score = min(25, v_score+5)
            flags.append(f"VIX acelerando ({v_vel:+.1f}%/5d)")
        score += v_score
        if v_score >= 25: flags.append(f"VIX panico ({v:.1f})")
        elif v_score >= 16: flags.append(f"VIX stress ({v:.1f})")
    # SKEW (25 pts)
    skew = next((r for r in vol_results if r["symbol"]=="^SKEW"), None)
    if skew:
        s = skew["price"]
        s_vel = skew.get("vel_5d")
        s_score = 25 if s>=150 else 16 if s>=140 else 8 if s>=130 else 0
        if s_vel and s_vel > 5 and s_score > 0:
            s_score = min(25, s_score+5)
            flags.append(f"SKEW acelerando ({s_vel:+.1f}%/5d)")
        score += s_score
        if s_score >= 25: flags.append(f"SKEW tail risk ({s:.0f})")
    # VVIX (25 pts)
    vvix = next((r for r in vol_results if r["symbol"]=="^VVIX"), None)
    if vvix:
        vv = vvix["price"]
        vv_vel = vvix.get("vel_5d")
        vv_score = 25 if vv>=120 else 16 if vv>=100 else 8 if vv>=80 else 0
        if vv_vel and vv_vel > 20 and vv_score > 0:
            vv_score = min(25, vv_score+5)
            flags.append(f"VVIX acelerando ({vv_vel:+.1f}%/5d)")
        score += vv_score
        if vv_score >= 25: flags.append(f"VVIX extremo ({vv:.1f})")
    # PCC (25 pts)
    pcc = next((r for r in pcc_results if r["symbol"]=="^PCC"), None)
    if pcc:
        p = pcc["current"]
        p_vel = pcc.get("roc_d", 0)
        p_score = 25 if p>=1.5 else 16 if p>=1.2 else 8 if p>=1.0 else \
                  16 if p<=0.6 else 8 if p<=0.7 else 0
        if p_vel and p_vel > 0.1 and p_score > 0:
            p_score = min(25, p_score+5)
            flags.append(f"PCC acelerando ({p_vel:+.3f}/d)")
        score += p_score
        if p >= 1.5: flags.append(f"PCC medo extremo ({p:.3f})")
        elif p <= 0.6: flags.append(f"PCC euforia extrema ({p:.3f})")
    final = round(min(score, 100), 1)
    if final >= 80:   label = "RISCO MAXIMO — mercado fragil"
    elif final >= 60: label = "RISCO ALTO — cautela maxima"
    elif final >= 40: label = "RISCO MODERADO — monitora"
    elif final >= 20: label = "RISCO BAIXO — normal"
    else:             label = "CALMO — possivel complacencia"
    return final, flags, label

def analyse_pcc(symbol, name):
    try:
        df = fetch(symbol)
        if df is None: return None
        closes = df["Close"].astype(float).values.flatten()
        if len(closes) < 10: return None
        current = float(closes[-1])
        p1d = float(closes[-2]) if len(closes) > 1 else current
        p1w = float(closes[-6]) if len(closes) > 5 else current
        p1m = float(closes[-22]) if len(closes) > 21 else current
        roc_d = round(current - p1d, 3)
        roc_w = round(current - p1w, 3)
        roc_m = round(current - p1m, 3)
        z_ttm = zscore(closes, min(252, len(closes)))
        z_1m  = zscore(closes, min(22, len(closes)))
        pct   = round(float(pd.Series(closes).rank(pct=True).iloc[-1]*100), 1) \
                if len(closes) >= 50 else 50.0
        if current >= 1.2:
            signal="OPORTUNIDADE"; sentiment="MEDO EXTREMO"
            color="#4ade80"; action="Considera LONG — medo maximo"
        elif current >= 1.0:
            signal="ATENCAO"; sentiment="MEDO ELEVADO"
            color="#86efac"; action="Mercado defensivo — monitora"
        elif current >= 0.8:
            signal="NEUTRO"; sentiment="NEUTRO"
            color="#94a3b8"; action="Sem extremos — segue o modelo"
        elif current >= 0.6:
            signal="CUIDADO"; sentiment="OPTIMISMO"
            color="#fbbf24"; action="Euforia a crescer — reduz risco"
        else:
            signal="PERIGO"; sentiment="EUFORIA EXTREMA"
            color="#f43f5e"; action="Euforia maxima — considera hedge"
        roc_sig = "Medo a aumentar" if roc_d > 0.05 else \
                  "Medo a diminuir" if roc_d < -0.05 else "Estavel"
        return {
            "symbol":current,"name":name,"current":round(current,3),
            "pfmt":f"{current:.3f}","p1d":round(p1d,3),
            "p1w":round(p1w,3),"p1m":round(p1m,3),
            "roc_d":roc_d,"roc_w":roc_w,"roc_m":roc_m,
            "roc_sig":roc_sig,"z_ttm":z_ttm,"z_1m":z_1m,"pct":pct,
            "signal":signal,"sentiment":sentiment,"color":color,"action":action,
        }
    except:
        return None

def analyse_pcc(symbol, name):
    try:
        df = fetch(symbol)
        if df is None: return None
        closes = df["Close"].astype(float).values.flatten()
        if len(closes) < 10: return None
        current = float(closes[-1])
        p1d  = float(closes[-2])  if len(closes) > 1  else current
        p1w  = float(closes[-6])  if len(closes) > 5  else current
        p1m  = float(closes[-22]) if len(closes) > 21 else current
        roc_d = round(current - p1d, 3)
        roc_w = round(current - p1w, 3)
        roc_m = round(current - p1m, 3)
        z_ttm = zscore(closes, min(252, len(closes)))
        z_1m  = zscore(closes, min(22, len(closes)))
        pct = round(float(
            pd.Series(closes).rank(pct=True).iloc[-1]*100), 1) \
            if len(closes) >= 50 else 50.0
        if current >= 1.2:
            signal="OPORTUNIDADE"; sentiment="MEDO EXTREMO"
            color="#4ade80"; action="Considera LONG — medo maximo"
        elif current >= 1.0:
            signal="ATENCAO"; sentiment="MEDO ELEVADO"
            color="#86efac"; action="Mercado defensivo — monitora"
        elif current >= 0.8:
            signal="NEUTRO"; sentiment="NEUTRO"
            color="#94a3b8"; action="Sem extremos — segue o modelo"
        elif current >= 0.6:
            signal="CUIDADO"; sentiment="OPTIMISMO"
            color="#fbbf24"; action="Euforia a crescer — reduz risco"
        else:
            signal="PERIGO"; sentiment="EUFORIA EXTREMA"
            color="#f43f5e"; action="Euforia maxima — considera hedge"
        roc_sig = "Medo a aumentar" if roc_d > 0.05 else \
                  "Medo a diminuir" if roc_d < -0.05 else "Estavel"
        return {
            "symbol":symbol,"name":name,"current":round(current,3),
            "pfmt":f"{current:.3f}","p1d":round(p1d,3),
            "p1w":round(p1w,3),"p1m":round(p1m,3),
            "roc_d":roc_d,"roc_w":roc_w,"roc_m":roc_m,
            "roc_sig":roc_sig,"z_ttm":z_ttm,"z_1m":z_1m,"pct":pct,
            "signal":signal,"sentiment":sentiment,"color":color,"action":action,
        }
    except:
        return None

def calc_sentiment_score(pcc_results, vix_level):
    score = 50
    pcc_total = next((r for r in pcc_results if r["symbol"]=="^PCC"), None)
    if pcc_total:
        pcc = pcc_total["current"]
        if pcc >= 1.5:   score += 30
        elif pcc >= 1.2: score += 20
        elif pcc >= 1.0: score += 10
        elif pcc >= 0.6: score -= 10
        else:            score -= 20
    if vix_level:
        if vix_level >= 35:   score += 20
        elif vix_level >= 25: score += 10
        elif vix_level >= 20: score += 5
        elif vix_level <= 12: score -= 15
    return min(max(round(score), 0), 100)

def sentiment_interpretation(score):
    if score >= 80: return "PANICO EXTREMO — oportunidade historica","#4ade80"
    if score >= 65: return "MEDO ELEVADO — considera longs","#86efac"
    if score >= 50: return "MEDO MODERADO — cautela selectiva","#fbbf24"
    if score >= 35: return "NEUTRO — segue o modelo","#94a3b8"
    if score >= 20: return "OPTIMISMO — reduz exposicao","#fbbf24"
    return "EUFORIA EXTREMA — hedge obrigatorio","#f43f5e"

def analyse_vol(symbol, name, category):
    try:
        df = fetch(symbol)
        if df is None: return None
        closes = df["Close"].astype(float).values.flatten()
        if len(closes) < 20: return None
        price = float(closes[-1])
        p1d   = float(closes[-2]) if len(closes) > 1 else price
        p2d   = float(closes[-3]) if len(closes) > 2 else p1d
        pd_c  = round((price-p1d)/p1d*100, 2) if p1d > 0 else 0
        roc   = round(pd_c-(p1d-p2d)/p2d*100, 2) if p2d > 0 else 0
        z_ttm = zscore(closes, min(252, len(closes)))
        vel_5d= None
        if len(closes) >= 6:
            past = float(closes[-6])
            if past > 0:
                vel_5d = round((price-past)/past*100, 2)
        pct = round(float(
            pd.Series(closes).rank(pct=True).iloc[-1]*100), 1) \
            if len(closes) >= 50 else 50.0
        vol_regime = "NORMAL"
        if symbol == "^VIX":
            vol_regime = "PANICO"       if price > 30 else \
                         "STRESS"       if price > 20 else \
                         "COMPLACENCIA" if price < 15 else "NORMAL"
        comp = "COMPRESSED" if pct<25 else "EXPANDING" if pct>75 else "NORMAL"
        score = 0
        score += 0.8 if pd_c > 0 else -0.8
        score += 0.5 if roc  > 0 else -0.5
        score += 0.4 if pct>70 else (-0.4 if pct<30 else 0)
        score = round(score, 2)
        if score >= 0.6:   signal = "BEARISH"
        elif score <= -0.6:signal = "BULLISH"
        else:              signal = "TURNING"
        pfmt = f"{price:.2f}" if price >= 1 else f"{price:.4f}"
        return {
            "symbol":symbol,"name":name,"pfmt":pfmt,"price":price,
            "signal":signal,"score":score,"pd_c":pd_c,"roc":roc,
            "ttmz":z_ttm,"vp":pct,"comp":comp,
            "term_structure":"N/A","vol_regime":vol_regime,"vel_5d":vel_5d,
        }
    except:
        return None

def calc_vol_master(vol_results):
    if not vol_results: return 50
    vix  = next((r for r in vol_results if r["symbol"]=="^VIX"),  None)
    vxn  = next((r for r in vol_results if r["symbol"]=="^VXN"),  None)
    skew = next((r for r in vol_results if r["symbol"]=="^SKEW"), None)
    vvix = next((r for r in vol_results if r["symbol"]=="^VVIX"), None)
    score = 0; count = 0
    for item, thresholds in [
        (vix,  [(40,100),(30,80),(25,60),(20,40),(15,20)]),
        (vxn,  [(45,100),(35,80),(28,60),(22,40),(17,20)]),
        (skew, [(150,80),(140,60),(130,40),(120,20)]),
        (vvix, [(120,100),(100,70),(80,40)]),
    ]:
        if item:
            v = item["price"]
            s = 10
            for threshold, pts in thresholds:
                if v >= threshold:
                    s = pts
                    break
            score += s
            count += 1
    return round(score/count) if count > 0 else 50

def generate_pcc_html(pcc_results, sentiment_score,
                       market_risk=0, risk_flags=[],
                       risk_label="NORMAL"):
    if not pcc_results: return ""
    sent_label, sent_color = sentiment_interpretation(sentiment_score)
    risk_color = "#f43f5e" if market_risk>=80 else \
                 "#f97316" if market_risk>=60 else \
                 "#fbbf24" if market_risk>=40 else \
                 "#4ade80" if market_risk>=20 else "#94a3b8"
    cards = ""
    for r in pcc_results:
        roc_color = "#4ade80" if r["roc_d"]>0.02 else \
                    "#f43f5e" if r["roc_d"]<-0.02 else "#94a3b8"
        c = r["color"]
        cards += f"""
        <div style="background:#0a1628;border:1px solid {c}44;
                    border-radius:8px;padding:14px">
            <div style="color:{c};font-size:9px;margin-bottom:6px">
                {r['name']}</div>
            <div style="font-size:28px;font-weight:900;color:{c};
                        margin-bottom:4px">{r['pfmt']}</div>
            <div style="font-size:11px;color:{c};margin-bottom:8px;
                        font-weight:700">{r['signal']}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;
                        gap:4px;font-size:10px;margin-bottom:8px">
                <div style="color:#475569">ROC D:</div>
                <div style="color:{roc_color}">
                    {'▲' if r['roc_d']>0 else '▼'} {r['roc_d']:+.3f}
                </div>
                <div style="color:#475569">Percentil:</div>
                <div style="color:#94a3b8">{r['pct']}%</div>
                <div style="color:#475569">Z-TTM:</div>
                <div style="color:#94a3b8">{r['z_ttm']}</div>
            </div>
            <div style="background:{c}22;border-radius:4px;
                        padding:6px 8px;font-size:9px;color:{c}">
                {r['action']}</div>
        </div>"""
    flags_html = ""
    if risk_flags:
        flags_html = "<div style='margin-top:12px'>"
        for f in risk_flags:
            flags_html += f"""<div style="font-size:10px;color:#94a3b8;
                padding:4px 8px;margin-bottom:4px;
                background:#1e293b;border-radius:4px">{f}</div>"""
        flags_html += "</div>"
    return f"""
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);
                border:2px solid {risk_color}44;border-radius:10px;
                padding:20px;margin-bottom:20px">
        <div style="display:grid;grid-template-columns:1fr 1fr;
                    gap:16px;align-items:center">
            <div style="text-align:center">
                <div style="font-size:10px;color:#475569;margin-bottom:8px">
                    MARKET RISK SCORE</div>
                <div style="font-size:56px;font-weight:900;color:{risk_color}">
                    {market_risk}</div>
                <div style="font-size:11px;color:{risk_color};
                            margin-top:4px;font-weight:700">
                    {risk_label}</div>
            </div>
            <div>
                <div style="font-size:9px;color:#475569;margin-bottom:8px">
                    VIX · SKEW · VVIX · PCC + velocidade</div>
                <div style="font-size:9px;color:#334155;
                            font-style:italic">
                    Indicador de fragilidade — nao de timing.
                    Human in the Loop sempre.</div>
            </div>
        </div>
        <div style="margin-top:16px;background:#1e293b;border-radius:8px;
                    height:14px;overflow:hidden;position:relative">
            <div style="position:absolute;left:0;top:0;
                        width:{market_risk}%;height:100%;
                        background:linear-gradient(90deg,#4ade80,#fbbf24,#f97316,#f43f5e);
                        border-radius:8px"></div>
        </div>
        <div style="display:flex;justify-content:space-between;
                    font-size:9px;color:#334155;margin-top:4px">
            <span>0</span><span>20</span><span>40</span>
            <span>60</span><span>80</span><span>100</span>
        </div>
        {flags_html}
    </div>
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);
                border:1px solid {sent_color}44;border-radius:10px;
                padding:20px;margin-bottom:20px;text-align:center">
        <div style="font-size:10px;color:#475569;margin-bottom:8px">
            SENTIMENT MASTER SCORE</div>
        <div style="font-size:48px;font-weight:900;color:{sent_color}">
            {sentiment_score}/100</div>
        <div style="font-size:12px;color:{sent_color};
                    margin-top:8px;font-weight:700">{sent_label}</div>
        <div style="margin-top:16px;background:#1e293b;border-radius:8px;
                    height:12px;overflow:hidden;position:relative">
            <div style="position:absolute;left:0;top:0;
                        width:{sentiment_score}%;height:100%;
                        background:linear-gradient(90deg,#f43f5e,#fbbf24,#4ade80);
                        border-radius:8px"></div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);
                gap:8px;margin-bottom:16px">{cards}</div>"""

def run_volatility_scanner():
    print(f"\n{'='*60}")
    print(f"  VOL + SENTIMENT + RISK — {RUN_DATE}")
    print("="*60)
    vol_results = []
    for symbol, name, category in VOL_TICKERS:
        try:
            r = analyse_vol(symbol, name, category)
            if r:
                vol_results.append(r)
                sig = "↑" if r["signal"]=="BULLISH" else \
                      "↓" if r["signal"]=="BEARISH" else "–"
                vel = f" vel:{r['vel_5d']:+.1f}%/5d" if r.get("vel_5d") else ""
                print(f"  {sig} {name:20} {r['pfmt']:>8}  "
                      f"{r['signal']:8}{vel}")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
    pcc_results = []
    vix_level   = None
    vix_r = next((r for r in vol_results if r["symbol"]=="^VIX"), None)
    if vix_r: vix_level = vix_r["price"]
    print(f"\n  → Put/Call Ratios...")
    for symbol, name, category in PCC_TICKERS:
        try:
            r = analyse_pcc(symbol, name)
            if r:
                pcc_results.append(r)
                print(f"  ✓ {name:20} {r['pfmt']:>8}  {r['signal']}")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
    vol_master      = calc_vol_master(vol_results)
    sentiment_score = calc_sentiment_score(pcc_results, vix_level)
    market_risk, risk_flags, risk_label = calc_market_risk_score(
        vol_results, pcc_results, vix_level)
    sent_label, _ = sentiment_interpretation(sentiment_score)
    print(f"\n  Vol Master Score:  {vol_master}/100")
    print(f"  Sentiment Score:   {sentiment_score}/100")
    print(f"  Market Risk Score: {market_risk}/100 — {risk_label}")
    for f in risk_flags:
        print(f"    → {f}")
    return (vol_results, vol_master,
            pcc_results, sentiment_score,
            market_risk, risk_flags, risk_label)