# ============================================================
# SCANNER_FX.PY — FX + Macro + USD Correlation
# Correlação rolling 30D | ROC D/W/M | Sinal
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from indicators import analyse
from universe   import FX
from config     import RUN_DATE, TOP_N

USD_CORR_UNIVERSE = [
    ("GC=F",    "Gold",           "COMMODITY"),
    ("SI=F",    "Silver",         "COMMODITY"),
    ("CL=F",    "WTI Crude",      "COMMODITY"),
    ("HG=F",    "Copper",         "COMMODITY"),
    ("NG=F",    "Natural Gas",    "COMMODITY"),
    ("GLD",     "Gold ETF",       "COMMODITY"),
    ("SLV",     "Silver ETF",     "COMMODITY"),
    ("SPY",     "S&P500",         "EQUITY"),
    ("QQQ",     "Nasdaq",         "EQUITY"),
    ("EEM",     "EM ETF",         "EQUITY"),
    ("EFA",     "Dev Mkt ETF",    "EQUITY"),
    ("MCHI",    "China ETF",      "EQUITY"),
    ("INDA",    "India ETF",      "EQUITY"),
    ("QDV5.DE", "MSCI India EUR", "EQUITY"),
    ("EXS1.DE", "EuroStoxx50",    "EQUITY"),
    ("IWDA.AS", "MSCI World",     "EQUITY"),
    ("EURUSD=X","EUR/USD",        "FX"),
    ("GBPUSD=X","GBP/USD",        "FX"),
    ("USDJPY=X","USD/JPY",        "FX"),
    ("AUDUSD=X","AUD/USD",        "FX"),
    ("USDCAD=X","USD/CAD",        "FX"),
    ("USDCHF=X","USD/CHF",        "FX"),
    ("USDCNH=X","USD/CNH",        "FX"),
    ("TLT",     "20Y Bond ETF",   "BOND"),
    ("IEF",     "7-10Y Bond ETF", "BOND"),
    ("HYG",     "High Yield ETF", "BOND"),
    ("BTC-USD", "Bitcoin",        "CRYPTO"),
    ("ETH-USD", "Ethereum",       "CRYPTO"),
    ("BABA",    "Alibaba",        "EQUITY"),
    ("NVDA",    "Nvidia",         "EQUITY"),
    ("AAPL",    "Apple",          "EQUITY"),
]

def fetch_closes(symbol, days=200):
    try:
        end   = datetime.today()
        start = end - timedelta(days=days)
        df    = yf.download(symbol, start=start, end=end,
                            progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df["Close"].dropna()
    except:
        return None

def corr_color(val):
    if val is None:   return "#475569"
    if val >  0.7:    return "#f87171"
    if val >  0.4:    return "#fbbf24"
    if val >  0.1:    return "#94a3b8"
    if val > -0.1:    return "#cbd5e1"
    if val > -0.4:    return "#94a3b8"
    if val > -0.7:    return "#86efac"
    return                   "#4ade80"

def roc_color(val):
    if val is None: return "#475569"
    if val > 0:     return "#f87171"
    if val < 0:     return "#4ade80"
    return                 "#94a3b8"

def corr_signal(corr_now):
    if corr_now is None:  return "N/A"
    if corr_now >  0.7:   return "🔴 FORTE POS"
    if corr_now >  0.4:   return "🟡 MOD POS"
    if corr_now >  0.1:   return "⚪ FRACA POS"
    if corr_now > -0.1:   return "⚪ NEUTRA"
    if corr_now > -0.4:   return "⚪ FRACA NEG"
    if corr_now > -0.7:   return "🟡 MOD NEG"
    return                       "🟢 FORTE NEG"

def analyse_usd_correlation():
    print("  → A calcular correlações vs USD...")
    usd = fetch_closes("DX-Y.NYB")
    if usd is None:
        print("  ⚠️  DXY não disponível")
        return []

    results = []
    for symbol, name, category in USD_CORR_UNIVERSE:
        try:
            asset = fetch_closes(symbol)
            if asset is None:
                continue

            df = pd.DataFrame({"usd": usd, "asset": asset}).dropna()
            if len(df) < 40:
                continue

            r_usd   = df["usd"].pct_change().dropna()
            r_asset = df["asset"].pct_change().dropna()
            df2     = pd.DataFrame({"usd": r_usd,
                                    "asset": r_asset}).dropna()
            if len(df2) < 35:
                continue

            corr30 = df2["usd"].rolling(30).corr(df2["asset"]).dropna()
            if len(corr30) < 5:
                continue

            corr_now = round(float(corr30.iloc[-1]),  3)
            corr_1d  = round(float(corr30.iloc[-2]),  3) \
                       if len(corr30) > 1  else None
            corr_1w  = round(float(corr30.iloc[-6]),  3) \
                       if len(corr30) > 5  else None
            corr_1m  = round(float(corr30.iloc[-22]), 3) \
                       if len(corr30) > 21 else None

            roc_d = round(corr_now - corr_1d,  3) if corr_1d else None
            roc_w = round(corr_now - corr_1w,  3) if corr_1w else None
            roc_m = round(corr_now - corr_1m,  3) if corr_1m else None

            price = float(df["asset"].iloc[-1])
            pfmt  = f"{price:.4f}" if price < 10 else \
                    f"{price:.3f}" if price < 100 else \
                    f"{price:.2f}"

            results.append({
                "symbol":   symbol,   "name":     name,
                "category": category, "pfmt":     pfmt,
                "corr_now": corr_now, "corr_1d":  corr_1d,
                "corr_1w":  corr_1w,  "corr_1m":  corr_1m,
                "roc_d":    roc_d,    "roc_w":    roc_w,
                "roc_m":    roc_m,
                "signal":   corr_signal(corr_now),
            })
        except:
            continue

    return sorted(results,
                  key=lambda x: abs(x["corr_now"]),
                  reverse=True)

def generate_corr_html(corr_results):
    if not corr_results:
        return "<p style='color:#475569'>Sem dados.</p>"

    def fmt_corr(val):
        if val is None:
            return "<td style='color:#475569'>—</td>"
        c     = corr_color(val)
        bar_w = int(abs(val) * 40)
        bar_c = "#f87171" if val > 0 else "#4ade80"
        bar   = (f"<span style='display:inline-block;"
                 f"width:{bar_w}px;height:8px;"
                 f"background:{bar_c};border-radius:2px;"
                 f"vertical-align:middle;margin-right:4px'></span>")
        return f"<td style='color:{c}'>{bar}{val:+.3f}</td>"

    def fmt_roc(val):
        if val is None:
            return "<td style='color:#475569'>—</td>"
        c = roc_color(val)
        a = "▲" if val > 0 else "▼" if val < 0 else "→"
        return f"<td style='color:{c}'>{a} {val:+.3f}</td>"

    categories = ["FX","COMMODITY","EQUITY","BOND","CRYPTO"]
    cat_labels  = {
        "FX":        "💱 FX",
        "COMMODITY": "🛢️ COMMODITIES",
        "EQUITY":    "📈 EQUITIES",
        "BOND":      "📊 BONDS",
        "CRYPTO":    "₿ CRYPTO",
    }

    rows = ""
    for cat in categories:
        cat_res = [r for r in corr_results if r["category"]==cat]
        if not cat_res:
            continue
        rows += f"""
        <tr>
          <td colspan="10"
              style="background:#0a1628;color:#6366f1;
                     font-size:9px;letter-spacing:.15em;
                     font-weight:700;padding:10px">
            {cat_labels.get(cat,cat)}
          </td>
        </tr>"""
        for r in cat_res:
            cn = r["corr_now"]
            bg = "#f43f5e11" if cn >  0.5 else \
                 "#00d4aa11" if cn < -0.5 else "#1e293b22"
            rows += f"""
            <tr style="background:{bg}">
                <td><strong>{r['symbol']}</strong></td>
                <td style="color:#64748b">{r['name']}</td>
                <td><strong>{r['pfmt']}</strong></td>
                {fmt_corr(r['corr_now'])}
                {fmt_corr(r['corr_1w'])}
                {fmt_corr(r['corr_1m'])}
                {fmt_roc(r['roc_d'])}
                {fmt_roc(r['roc_w'])}
                {fmt_roc(r['roc_m'])}
                <td style="font-size:10px;color:#94a3b8">
                    {r['signal']}
                </td>
            </tr>"""

    strong_pos = [r for r in corr_results if r["corr_now"] >  0.6]
    strong_neg = [r for r in corr_results if r["corr_now"] < -0.6]
    accel_pos  = [r for r in corr_results
                  if r["roc_d"] and r["roc_d"] >  0.05]
    accel_neg  = [r for r in corr_results
                  if r["roc_d"] and r["roc_d"] < -0.05]

    html = f"""
    <div style="margin-bottom:20px">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);
                  gap:8px;margin-bottom:16px">
        <div style="background:#f43f5e22;border:1px solid #f43f5e44;
                    border-radius:8px;padding:12px">
          <div style="font-size:9px;color:#f43f5e;letter-spacing:.15em;
                      margin-bottom:6px">🔴 FORTE POSITIVA</div>
          <div style="font-size:20px;font-weight:900;color:#f43f5e">
              {len(strong_pos)}</div>
          <div style="font-size:9px;color:#64748b;margin-top:4px">
              {' · '.join([r['symbol'] for r in strong_pos[:4]])}
          </div>
        </div>
        <div style="background:#00d4aa22;border:1px solid #00d4aa44;
                    border-radius:8px;padding:12px">
          <div style="font-size:9px;color:#00d4aa;letter-spacing:.15em;
                      margin-bottom:6px">🟢 FORTE NEGATIVA</div>
          <div style="font-size:20px;font-weight:900;color:#00d4aa">
              {len(strong_neg)}</div>
          <div style="font-size:9px;color:#64748b;margin-top:4px">
              {' · '.join([r['symbol'] for r in strong_neg[:4]])}
          </div>
        </div>
        <div style="background:#fbbf2422;border:1px solid #fbbf2444;
                    border-radius:8px;padding:12px">
          <div style="font-size:9px;color:#fbbf24;letter-spacing:.15em;
                      margin-bottom:6px">⚠️ CORR A SUBIR</div>
          <div style="font-size:20px;font-weight:900;color:#fbbf24">
              {len(accel_pos)}</div>
          <div style="font-size:9px;color:#64748b;margin-top:4px">
              {' · '.join([r['symbol'] for r in accel_pos[:4]])}
          </div>
        </div>
        <div style="background:#86efac22;border:1px solid #86efac44;
                    border-radius:8px;padding:12px">
          <div style="font-size:9px;color:#86efac;letter-spacing:.15em;
                      margin-bottom:6px">✅ CORR A DESCER</div>
          <div style="font-size:20px;font-weight:900;color:#86efac">
              {len(accel_neg)}</div>
          <div style="font-size:9px;color:#64748b;margin-top:4px">
              {' · '.join([r['symbol'] for r in accel_neg[:4]])}
          </div>
        </div>
      </div>

      <div style="background:#0a1628;border:1px solid #1e3a5f;
                  border-radius:8px;padding:12px;margin-bottom:16px;
                  font-size:9px;color:#475569;line-height:2">
        <strong style="color:#94a3b8">CORRELAÇÃO vs USD (DXY):</strong>
        &nbsp;
        <span style="color:#f87171">+1.0 = move igual ao USD</span>
        &nbsp;·&nbsp;
        <span style="color:#4ade80">-1.0 = move oposto ao USD</span>
        &nbsp;·&nbsp;
        <span style="color:#94a3b8">0 = sem relação</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <strong style="color:#94a3b8">ROC:</strong>
        <span style="color:#f87171">▲ correlação a aumentar</span>
        &nbsp;·&nbsp;
        <span style="color:#4ade80">▼ correlação a diminuir</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        Janela: 30D rolling
      </div>

      <table>
        <tr>
          <th>Ticker</th><th>Nome</th><th>Preço</th>
          <th>Corr Actual</th><th>Corr 1W</th><th>Corr 1M</th>
          <th>ROC D</th><th>ROC W</th><th>ROC M</th>
          <th>Sinal</th>
        </tr>
        {rows}
      </table>
    </div>"""

    return html

def run_fx_scanner():
    print("\n" + "="*60)
    print(f"  FX + USD CORRELATION SCANNER — {RUN_DATE}")
    print("="*60)

    fx_results = []
    for symbol, name, market in FX:
        try:
            r = analyse(symbol, name, market)
            if r is None:
                continue
            fx_results.append(r)
            print(f"  ✓ {name:15} {r['pfmt']:>10}  "
                  f"{r['signal']:8}  Score:{r['score']:+.1f}")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
            continue

    corr_results = analyse_usd_correlation()
    print(f"  ✓ {len(corr_results)} correlações calculadas")

    ranked = sorted(fx_results,
                    key=lambda x: (abs(x["score"]) + x["h_d"]),
                    reverse=True)

    print(f"\n{'─'*60}")
    print(f"  TOP FX SETUPS")
    print(f"{'─'*60}")
    for i, r in enumerate(ranked[:TOP_N], 1):
        sig = "🟢" if r["signal"]=="BULLISH" else \
              "🔴" if r["signal"]=="BEARISH" else "🟡"
        print(f"  #{i:02}  {r['name']:15} {r['pfmt']:>10}  "
              f"{sig} {r['signal']:8}  Score:{r['score']:+.1f}")

    print()
    return ranked, corr_results

if __name__ == "__main__":
    fx, corr = run_fx_scanner()
    print(f"\n✅ FX + USD Correlation completo!")