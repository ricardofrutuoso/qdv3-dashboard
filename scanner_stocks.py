# ============================================================
# SCANNER_STOCKS.PY — Acções globais
# ============================================================

from indicators import analyse
from universe import STOCKS
from config import RUN_DATE, MIN_VOLUME, TOP_N

def run_stocks_scanner():
    print("\n" + "="*60)
    print(f"  STOCKS SCANNER — {RUN_DATE}")
    print("="*60)

    results = []

    for symbol, name, market in STOCKS:
        try:
            r = analyse(symbol, name, market)
            if r is None:
                continue
            if r["avg_vol"] < MIN_VOLUME:
                continue
            results.append(r)
            print(f"  ✓ {symbol:12} {r['pfmt']:>10}  "
                  f"{r['signal']:8}  Score:{r['score']:+.1f}  "
                  f"H:{r['h_d']}  Conv:{r['conv']}")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
            continue

    ranked = sorted(results,
                    key=lambda x: (abs(x["score"]) + x["h_d"]),
                    reverse=True)

    print(f"\n{'─'*60}")
    print(f"  TOP {min(TOP_N, len(ranked))} STOCKS")
    print(f"{'─'*60}")
    for i, r in enumerate(ranked[:TOP_N], 1):
        sig = "🟢" if r["signal"]=="BULLISH" else \
              "🔴" if r["signal"]=="BEARISH" else "🟡"
        print(f"  #{i:02}  {r['symbol']:12} {r['pfmt']:>10}  "
              f"{sig} {r['signal']:8}  "
              f"Score:{r['score']:+.1f}  H:{r['h_d']}  "
              f"Opção:{r['opt']}")

    print()
    return ranked

if __name__ == "__main__":
    run_stocks_scanner()