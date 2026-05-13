# ============================================================
# SCANNER_OPTIONS.PY — Sugestões de opções DeGiro
# ============================================================

from indicators import analyse
from universe import OPTIONS_UNIVERSE
from config import RUN_DATE, CAPITAL, RISK_PER_TRADE_PCT

def expiry_suggestion(h, vp, score):
    if vp < 25:
        return "Monthly (vol baixa = comprar tempo)"
    if vp > 65:
        return "Weekly (vol alta = theta agressivo)"
    if h > 0.62:
        return "Monthly (trending = dar espaço)"
    return "Monthly"

def strike_suggestion(lvl, signal):
    if signal == "BULLISH":
        return f"ATM ou {lvl['trade'][1]} (Trade Upper)"
    if signal == "BEARISH":
        return f"ATM ou {lvl['trade'][0]} (Trade Lower)"
    return "Aguardar"

def size_suggestion(price, capital, risk_pct):
    risk_eur  = capital * risk_pct
    contracts = max(1, int(risk_eur / (price * 0.10)))
    return contracts

def run_options_scanner():
    print("\n" + "="*60)
    print(f"  OPTIONS SCANNER — {RUN_DATE}")
    print(f"  Capital: €{CAPITAL}  |  Risco/Trade: {RISK_PER_TRADE_PCT*100:.0f}%")
    print("="*60)

    results = []

    for symbol, name, market in OPTIONS_UNIVERSE:
        try:
            r = analyse(symbol, name, market)
            if r is None:
                continue

            if abs(r["score"]) < 0.6:
                continue

            expiry  = expiry_suggestion(r["h_d"], r["vp"], r["score"])
            strike  = strike_suggestion(r["lvl"], r["signal"])
            size    = size_suggestion(r["price"], CAPITAL, RISK_PER_TRADE_PCT)
            comm    = r["comm"]

            r["expiry"] = expiry
            r["strike"] = strike
            r["size"]   = size
            results.append(r)

        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
            continue

    ranked = sorted(results,
                    key=lambda x: abs(x["score"]),
                    reverse=True)

    for r in ranked:
        sig = "🟢" if r["signal"]=="BULLISH" else \
              "🔴" if r["signal"]=="BEARISH" else "🟡"
        direction = "CALL 📈" if r["signal"]=="BULLISH" else \
                    "PUT 📉"  if r["signal"]=="BEARISH" else "WAIT ⏳"
        print(f"""
{sig} {r['symbol']} ({r['name']}) — {r['pfmt']}
Direcção:  {direction}
Strike:    {r['strike']}
Expiry:    {r['expiry']}
Contratos: {r['size']}x  |  DeGiro: €{r['comm']}/contrato
Score:     {r['score']}  |  Hurst: {r['h_d']}  |  Vol%ile: {r['vp']}%
Convicção: {r['conv']}
""")

    if not ranked:
        print("  ⏳ Sem setups de opções com convicção suficiente hoje.")

    print()
    return ranked

if __name__ == "__main__":
    run_options_scanner()