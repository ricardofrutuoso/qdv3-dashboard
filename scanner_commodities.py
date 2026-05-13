# ============================================================
# SCANNER_COMMODITIES.PY — Commodities
# ============================================================

from indicators import analyse
from universe import COMMODITIES
from config import RUN_DATE, TOP_N

def run_commodities_scanner():
    print("\n" + "="*60)
    print(f"  COMMODITIES SCANNER — {RUN_DATE}")
    print("="*60)

    results = []

    for symbol, name, market in COMMODITIES:
        try:
            r = analyse(symbol, name, market)
            if r is None:
                continue
            results.append(r)
            print(f"  ✓ {name:15} {r['pfmt']:>10}  "
                  f"{r['signal']:8}  Score:{r['score']:+.1f}  "
                  f"H:{r['h_d']}  VP:{r['vp']}%")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
            continue

    ranked = sorted(results,
                    key=lambda x: (abs(x["score"]) + x["h_d"]),
                    reverse=True)

    print(f"\n{'─'*60}")
    print(f"  TOP COMMODITIES SETUPS")
    print(f"{'─'*60}")
    for i, r in enumerate(ranked[:TOP_N], 1):
        sig = "🟢" if r["signal"]=="BULLISH" else \
              "🔴" if r["signal"]=="BEARISH" else "🟡"
        print(f"  #{i:02}  {r['name']:15} {r['pfmt']:>10}  "
              f"{sig} {r['signal']:8}  "
              f"Score:{r['score']:+.1f}  H:{r['h_d']}  "
              f"{r['comp']}")

    print()
    return ranked

if __name__ == "__main__":
    run_commodities_scanner()