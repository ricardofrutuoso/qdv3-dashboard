# ============================================================
# SCANNER_STOCKS.PY — Stocks Globais QDV3
# Integra: DFA Hurst | P/D VWAP | Brennan | Insider | Trends
# ============================================================

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from config import CAPITAL, RUN_DATE, TOP_N, MIN_HURST, MIN_VOLUME
from universe import STOCKS
from indicators import analyse, signal_label, momentum_score

# ── ENTRY QUALITY ────────────────────────────────────────────
def entry_quality(r, insider_signal=None, trends_signal=None):
    pd_c   = r.get("pd_c",  0)
    pd_1w  = r.get("pd_1w", 0)
    pd_1m  = r.get("pd_1m", 0)
    h      = r.get("h_d",   0.5)
    vp     = r.get("vp",    50)
    comp   = r.get("comp",  "NORMAL")
    adx    = r.get("adx",   0)
    score  = r.get("score", 0)

    # Bonus Insider
    insider_bonus = 0
    if insider_signal:
        sig = insider_signal.get("signal", "")
        if "CLUSTER BUY FORTE" in sig: insider_bonus =  2
        elif "CLUSTER BUY"     in sig: insider_bonus =  1
        elif "CLUSTER SELL"    in sig: insider_bonus = -1

    # Bonus Trends (contrarian)
    trends_bonus = 0
    if trends_signal:
        tsig = trends_signal.get("signal", "")
        if "FOMO EXTREMO"  in tsig: trends_bonus = -1
        elif "ESQUECIDO"   in tsig: trends_bonus =  1

    adj_score = score + insider_bonus * 0.3 + trends_bonus * 0.2

    # Ideal: tudo alinhado, compressed + trending
    if (pd_c < 0 and pd_1w < 0 and pd_1m < 0 and
            h > 0.55 and vp < 40 and adx > 20 and
            "COMPRES" in comp and adj_score <= -0.8):
        return "✅ IDEAL"

    if (pd_c < 0 and pd_1w < 0 and h > 0.52 and
            vp < 55 and adj_score <= -0.6):
        return "🟡 ACEITÁVEL"

    if (pd_c > 0 and pd_1w > 0 and h > 0.55 and
            vp < 40 and "COMPRES" in comp):
        return "✅ IDEAL LONG"

    if pd_c > 0.05:
        return "⚠️ EXTENDED"

    if pd_c > 0.02 and adj_score > 0.8:
        return "⏳ AGUARDA"

    if vp > 80 or abs(adj_score) > 2.0:
        return "🚨 EXTREMO"

    return "⏳ AGUARDA"

# ── CALC RANK ────────────────────────────────────────────────
def calc_rank(r, insider_signal=None, trends_signal=None):
    score = 0
    # P/D alignment (30 pts)
    pd_align = sum([
        1 if r.get("pd_c",  0) < 0 else 0,
        1 if r.get("pd_1w", 0) < 0 else 0,
        1 if r.get("pd_1m", 0) < 0 else 0,
        1 if r.get("pd_str",0) < 0 else 0,
    ])
    score += pd_align * 7.5

    # Hurst DFA (25 pts)
    h = r.get("h_d", 0.5)
    if h >= 0.70: score += 25
    elif h >= 0.62: score += 18
    elif h >= 0.55: score += 12
    elif h >= 0.48: score += 6
    else: score += 0

    # Momentum score (20 pts)
    ms = abs(r.get("score", 0))
    score += min(ms * 10, 20)

    # Vol percentile (15 pts)
    vp = r.get("vp", 50)
    if 15 <= vp <= 35: score += 15
    elif 35 < vp <= 55: score += 10
    elif vp < 15: score += 5
    else: score += 0

    # Z-Score (10 pts)
    z = abs(r.get("ttmz", 0) or 0)
    if z >= 2.0: score += 10
    elif z >= 1.5: score += 7
    elif z >= 1.0: score += 4

    # Brennan compression bonus (10 pts)
    comp = r.get("comp", "")
    if "COMPRESSION+TRENDING" in comp: score += 10
    elif "COMPRESSED" in comp: score += 6

    # Insider bonus (10 pts)
    if insider_signal:
        sig = insider_signal.get("signal","")
        if "CLUSTER BUY FORTE" in sig: score += 10
        elif "CLUSTER BUY"     in sig: score += 6
        elif "CLUSTER SELL"    in sig: score -= 5

    # Trends bonus (5 pts)
    if trends_signal:
        tsig = trends_signal.get("signal","")
        if "ESQUECIDO"  in tsig: score += 5
        elif "FOMO EXTREMO" in tsig: score -= 5

    return min(round(score), 100)

# ── POSITION SIZE ────────────────────────────────────────────
def position_size(price, market, h, vp):
    from config import DEGIRO_COMMISSIONS
    risk_capital = CAPITAL * 0.10
    atr_est      = price * (vp / 100) * 0.02
    sl_dist      = max(atr_est * 1.5, price * 0.03)
    comm         = DEGIRO_COMMISSIONS.get(market, 3.90)
    if sl_dist <= 0: return 0, 0.0, 0.0
    qty = max(1, int((risk_capital - comm * 2) / sl_dist))
    notional   = round(qty * price, 2)
    sl_price   = round(price - sl_dist, 4)
    return qty, notional, sl_price

# ── RUN STOCKS SCANNER ───────────────────────────────────────
def run_stocks_scanner(insider_data=None, trends_data=None,
                       limit=None):
    print(f"\n{'='*60}")
    print(f"  STOCKS SCANNER — {RUN_DATE}")
    print(f"  DFA Hurst + P/D + Brennan + Insider + Trends")
    print("="*60)

    insider_map = {}
    if insider_data:
        for r in insider_data:
            insider_map[r["ticker"]] = r

    trends_map = {}
    if trends_data:
        for r in trends_data:
            trends_map[r["ticker"]] = r

    tickers = list(set(STOCKS))
    if limit:
        tickers = tickers[:limit]

    results = []
    for symbol, name, market in tickers:
        try:
            r = analyse(symbol, name, market)
            if r is None: continue
            if r["avg_vol"] < MIN_VOLUME: continue
            if r["h_d"] < MIN_HURST: continue

            ins = insider_map.get(symbol)
            trn = trends_map.get(symbol)

            r["entry_q"] = entry_quality(r, ins, trn)
            r["rank"]    = calc_rank(r, ins, trn)
            r["insider"] = ins
            r["trends"]  = trn

            qty, notional, sl = position_size(
                r["price"], market, r["h_d"], r["vp"])
            r["qty"]      = qty
            r["notional"] = notional
            r["sl"]       = sl

            results.append(r)
            sig = "✅" if "IDEAL" in r["entry_q"] else \
                  "🟡" if "ACEIT" in r["entry_q"] else \
                  "⚠️" if "EXTEND" in r["entry_q"] else "·"
            print(f"  {sig} {symbol:12} {name:20} "
                  f"H:{r['h_d']:.2f} "
                  f"P/D:{r['pd_c']:+.2f}% "
                  f"R:{r['rank']}")
        except Exception as e:
            continue

    results.sort(key=lambda x: x["rank"], reverse=True)
    top = results[:TOP_N]
    ideal = [r for r in results if "IDEAL" in r.get("entry_q","")]
    accept= [r for r in results if "ACEIT" in r.get("entry_q","")]
    print(f"\n  Total: {len(results)} | Ideal: {len(ideal)} | "
          f"Aceitável: {len(accept)} | Top {TOP_N} por rank")
    return results, top

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_stocks_html(results, top):
    def rows_html(lst, show_insider=True):
        rows = ""
        for r in lst:
            eq  = r.get("entry_q","—")
            c   = "#4ade80" if "IDEAL"  in eq else \
                  "#fbbf24" if "ACEIT"  in eq else \
                  "#f43f5e" if "EXTREM" in eq else "#94a3b8"
            hc  = "#4ade80" if r["h_d"]>0.62 else \
                  "#fbbf24" if r["h_d"]>0.52 else "#f87171"
            pdc = "#4ade80" if r["pd_c"]<0 else "#f43f5e"
            br  = r.get("comp","N/A")[:6]
            ins = r.get("insider")
            trn = r.get("trends")
            ins_badge = ""
            if ins and "CLUSTER" in ins.get("signal",""):
                ic = "#4ade80" if "BUY" in ins["signal"] else "#f43f5e"
                ins_badge = (
                    f"<span style='background:{ic}22;color:{ic};"
                    f"font-size:8px;padding:1px 4px;border-radius:3px;"
                    f"margin-left:4px'>INS</span>"
                )
            trn_badge = ""
            if trn and trn.get("z_score",0) != 0:
                tz = trn["z_score"]
                tc = "#f43f5e" if tz>1.5 else "#4ade80" if tz<-1.0 else ""
                if tc:
                    trn_badge = (
                        f"<span style='background:{tc}22;color:{tc};"
                        f"font-size:8px;padding:1px 4px;border-radius:3px;"
                        f"margin-left:2px'>TRD</span>"
                    )
            rows += f"""
            <tr>
              <td><strong>{r['symbol']}</strong></td>
              <td style="color:#64748b">{r['name'][:18]}</td>
              <td style="color:#475569;font-size:9px">{r['market']}</td>
              <td><strong>{r['pfmt']}</strong></td>
              <td style="background:{c}22;color:{c};font-size:10px;
                  border-radius:4px;padding:2px 5px">{eq}</td>
              <td style="color:{hc};font-weight:700">{r['h_d']:.2f}</td>
              <td style="font-size:9px;color:#64748b">{r['h_sig']}</td>
              <td style="color:{pdc}">{r['pd_c']:+.2f}%</td>
              <td style="color:#94a3b8">{r['pd_1w']:+.2f}%</td>
              <td style="color:#475569">{r['pd_1m']:+.2f}%</td>
              <td style="color:#94a3b8">{r['vp']:.0f}%</td>
              <td style="color:#64748b;font-size:9px">{br}</td>
              <td style="color:#94a3b8">{r['ttmz'] or '—'}</td>
              <td style="font-weight:700;color:{c}">{r['rank']}</td>
              <td>{ins_badge}{trn_badge}</td>
            </tr>"""
        return rows

    ideal   = [r for r in results if "IDEAL"  in r.get("entry_q","")]
    aceit   = [r for r in results if "ACEIT"  in r.get("entry_q","")]
    extnd   = [r for r in results if "EXTREM" in r.get("entry_q","") or
               "EXTEND" in r.get("entry_q","")]

    header = """<tr>
        <th>Ticker</th><th>Nome</th><th>Mercado</th><th>Preço</th>
        <th>Entry Quality</th><th>Hurst</th><th>H Sig</th>
        <th>P/D Diário</th><th>P/D Semanal</th><th>P/D Mensal</th>
        <th>Vol%</th><th>Brennan</th><th>Z-TTM</th><th>Rank</th>
        <th>+</th>
    </tr>"""

    return f"""
    <div id="stocks" class="tab-content section">
      <div class="section-title">STOCKS GLOBAIS</div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);
                  gap:8px;margin-bottom:16px">
        <div style="background:#4ade8022;border:1px solid #4ade8044;
                    border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:9px;color:#4ade80">IDEAL</div>
          <div style="font-size:24px;font-weight:900;color:#4ade80">
              {len(ideal)}</div></div>
        <div style="background:#fbbf2422;border:1px solid #fbbf2444;
                    border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:9px;color:#fbbf24">ACEITÁVEL</div>
          <div style="font-size:24px;font-weight:900;color:#fbbf24">
              {len(aceit)}</div></div>
        <div style="background:#f43f5e22;border:1px solid #f43f5e44;
                    border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:9px;color:#f43f5e">EXTENDED</div>
          <div style="font-size:24px;font-weight:900;color:#f43f5e">
              {len(extnd)}</div></div>
      </div>

      <div style="color:#64748b;font-size:11px;font-weight:700;
                  margin-bottom:8px">
          🏆 TOP {TOP_N} por Rank</div>
      <div class="table-wrap">
        <table>{header}{rows_html(top)}</table>
      </div>

      <div style="color:#64748b;font-size:11px;font-weight:700;
                  margin:16px 0 8px">✅ Setups IDEAIS</div>
      <div class="table-wrap">
        <table>{header}{rows_html(ideal)}</table>
      </div>

      <div style="color:#64748b;font-size:11px;font-weight:700;
                  margin:16px 0 8px">🟡 Setups ACEITÁVEIS</div>
      <div class="table-wrap">
        <table>{header}{rows_html(aceit)}</table>
      </div>
    </div>"""