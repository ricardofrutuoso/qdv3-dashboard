# ============================================================
# SCANNER_VOLATILITY.PY — Vol of Vol + Vol Master
# VIX, VXN, RVX, VVIX, SKEW, OVX, GVZ, EVZ
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime
from indicators import analyse, fetch, zscore, hurst
from universe import VOLATILITY
from config import RUN_DATE

def vol_regime(vix_level):
    if vix_level < 13:  return "😴 COMPLACÊNCIA"
    if vix_level < 18:  return "😊 CALMO"
    if vix_level < 25:  return "😐 NORMAL"
    if vix_level < 35:  return "😨 STRESS"
    if vix_level < 50:  return "😱 MEDO"
    return                     "💀 PÂNICO"

def term_structure(symbol):
    """Estima contango/backwardation via histórico recente"""
    try:
        df = fetch(symbol)
        if df is None:
            return "N/A"
        closes = df["Close"].astype(float).values.flatten()
        # Compara média 5D vs média 20D
        avg5  = float(np.mean(closes[-5:]))
        avg20 = float(np.mean(closes[-20:]))
        diff  = round((avg5 - avg20) / avg20 * 100, 2)
        if diff > 2:
            return f"📈 BACKWARDATION +{diff}%"
        if diff < -2:
            return f"📉 CONTANGO {diff}%"
        return f"〰️ FLAT {diff:+.2f}%"
    except:
        return "N/A"

def vol_master_score(results):
    """
    Agrega todos os índices de volatilidade
    num score mestre de 0 a 100
    """
    if not results:
        return None

    scores = []
    weights = {
        "^VVIX":  0.25,   # vol of vol — mais leading
        "^VIX":   0.20,   # mãe de todas
        "^VXN":   0.15,   # nasdaq vol
        "^SKEW":  0.15,   # tail risk
        "^RVX":   0.10,   # small caps
        "^OVX":   0.08,   # oil vol
        "^GVZ":   0.07,   # gold vol
    }

    total_weight = 0
    weighted_sum = 0

    for r in results:
        sym = r["symbol"]
        w   = weights.get(sym, 0.05)

        # Normaliza percentil histórico
        if r["ttmz"] is not None:
            # Converte z-score em percentil 0-100
            z     = float(r["ttmz"])
            pct   = min(100, max(0, 50 + z * 15))
            weighted_sum  += pct * w
            total_weight  += w

    if total_weight == 0:
        return None

    master = round(weighted_sum / total_weight, 1)
    return master

def master_interpretation(score):
    if score is None:
        return "N/A", "⚪"
    if score >= 80:
        return "💀 PÂNICO — oportunidade histórica de compra", "🔴"
    if score >= 65:
        return "😱 MEDO ELEVADO — mercado oversold", "🔴"
    if score >= 50:
        return "😨 STRESS MODERADO — cautela", "🟡"
    if score >= 35:
        return "😐 NORMAL — sem sinal claro", "⚪"
    if score >= 20:
        return "😊 CALMO — risco de complacência", "🟡"
    return "😴 COMPLACÊNCIA EXTREMA — cuidado com reversão", "🔴"

def run_volatility_scanner():
    print("\n" + "="*60)
    print(f"  VOL SCANNER — {RUN_DATE}")
    print(f"  Vol of Vol | Term Structure | Vol Master")
    print("="*60)

    results = []

    for symbol, name, market in VOLATILITY:
        try:
            r = analyse(symbol, name, market)
            if r is None:
                continue

            ts = term_structure(symbol)
            r["term_structure"] = ts

            # Regime específico para VIX
            if symbol == "^VIX":
                r["vol_regime"] = vol_regime(r["price"])
            else:
                r["vol_regime"] = ""

            results.append(r)

            # Print individual
            sig_emoji = "🟢" if r["signal"] == "BULLISH" else \
                        "🔴" if r["signal"] == "BEARISH" else "🟡"

            print(f"""
📌 {r['name']} ({symbol}) — {r['pfmt']}  {sig_emoji} {r['signal']}
Momentum Score: [{r['score']}]  |  Convicção: {r['conv']}
{r['vol_regime']}

P/D Current:  {r['pd_c']:+.2f}%
P/D 1W:       {r['pd_1w']:+.2f}%
P/D 1M:       {r['pd_1m']:+.2f}%
ROC P/D:      {r['roc']:+.2f}pp

TTM Z-Score:  {r['ttmz']}
Term Struct:  {ts}
Brennan Vol:  {r['comp']}

Hurst: Daily {r['h_d']} / Weekly {r['h_w']} → {r['h_sig']}
""")

        except Exception as e:
            print(f"⚠️  {symbol} ({name}) — erro: {e}")
            continue

    # Vol Master
    master = vol_master_score(results)
    interp, color = master_interpretation(master)

    print("="*60)
    print(f"  VOL MASTER SCORE: {master}/100")
    print(f"  {interp}")
    print("="*60)

    # VVIX vs VIX divergence
    vvix = next((r for r in results if r["symbol"] == "^VVIX"), None)
    vix  = next((r for r in results if r["symbol"] == "^VIX"),  None)

    if vvix and vix:
        print(f"""
DIVERGÊNCIA VVIX vs VIX:
  VVIX ROC: {vvix['roc']:+.2f}pp  |  VIX ROC: {vix['roc']:+.2f}pp""")

        if vvix["roc"] > 1 and vix["roc"] < 0:
            print("  ⚠️  VVIX LIDERA — stress iminente")
        elif vvix["roc"] < -1 and vix["roc"] > 0:
            print("  ✅ VVIX RELAXA — alívio a caminho")
        else:
            print("  〰️  Sem divergência significativa")

    print()
    return results, master

if __name__ == "__main__":
    run_volatility_scanner()