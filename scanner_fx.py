# ============================================================
# SCANNER_FX.PY — FX + Macro QDV3
# DFA Hurst | P/D VWAP | Brennan | COT Smart Money
# ============================================================

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from config import CAPITAL, RUN_DATE, TOP_N, MIN_HURST
from universe import FX
from indicators import analyse

def entry_quality(r, cot_signal=None):
    pd_c = r.get("pd_c",0); pd_1w=r.get("pd_1w",0)
    h    = r.get("h_d",0.5); vp  =r.get("vp",50)
    comp = r.get("comp","NORMAL"); score=r.get("score",0)
    adx  = r.get("adx",0)
    # Bonus COT
    cot_bonus = 0
    if cot_signal:
        csig = cot_signal.get("cot_signal","")
        if "BULLISH FORTE" in csig: cot_bonus = -0.5  # bearish means buy base
        elif "BEARISH FORTE" in csig: cot_bonus = 0.5
    adj = score + cot_bonus
    if (pd_c<0 and pd_1w<0 and h>0.55 and vp<40 and
            "COMPRES" in comp and adj<=-0.8):
        return "✅ IDEAL"
    if (pd_c<0 and pd_1w<0 and h>0.52 and vp<55 and adj<=-0.6):
        return "🟡 ACEITÁVEL"
    if (pd_c>0 and pd_1w>0 and h>0.55 and vp<40 and "COMPRES" in comp):
        return "✅ IDEAL LONG"
    if pd_c>0.05: return "⚠️ EXTENDED"
    if vp>80 or abs(score)>2.0: return "🚨 EXTREMO"
    return "⏳ AGUARDA"

def calc_rank(r, cot_signal=None):
    score = 0
    pd_align = sum([
        1 if r.get("pd_c",  0)<0 else 0,
        1 if r.get("pd_1w", 0)<0 else 0,
        1 if r.get("pd_1m", 0)<0 else 0,
        1 if r.get("pd_str",0)<0 else 0,
    ])
    score += pd_align * 7.5
    h = r.get("h_d",0.5)
    if h>=0.70: score+=25
    elif h>=0.62: score+=18
    elif h>=0.55: score+=12
    elif h>=0.48: score+=6
    score += min(abs(r.get("score",0))*10, 20)
    vp = r.get("vp",50)
    if 15<=vp<=35: score+=15
    elif 35<vp<=55: score+=10
    elif vp<15: score+=5
    z = abs(r.get("ttmz",0) or 0)
    if z>=2.0: score+=10
    elif z>=1.5: score+=7
    elif z>=1.0: score+=4
    comp = r.get("comp","")
    if "COMPRESSION+TRENDING" in comp: score+=10
    elif "COMPRESSED" in comp: score+=6
    # COT bonus (10 pts)
    if cot_signal:
        csig = cot_signal.get("cot_signal","")
        cz   = abs(cot_signal.get("commercial_z",0))
        if "FORTE" in csig and cz>=2.0: score+=10
        elif csig not in ("","NEUTRO"): score+=5
    return min(round(score),100)

def run_fx_scanner(cot_data=None, limit=None):
    print(f"\n{'='*60}")
    print(f"  FX + MACRO SCANNER — {RUN_DATE}")
    print(f"  DFA Hurst + P/D VWAP + COT Smart Money")
    print("="*60)
    cot_map = {}
    if cot_data:
        for r in cot_data:
            cot_map[r["ticker"]] = r
    tickers = list(set(FX))
    if limit: tickers = tickers[:limit]
    results = []
    for symbol, name, market in tickers:
        try:
            r = analyse(symbol, name, market)
            if r is None: continue
            if r["h_d"] < MIN_HURST: continue
            cot = cot_map.get(symbol)
            r["entry_q"] = entry_quality(r, cot)
            r["rank"]    = calc_rank(r, cot)
            r["cot"]     = cot
            results.append(r)
            sig = "✅" if "IDEAL" in r["entry_q"] else \
                  "🟡" if "ACEIT" in r["entry_q"] else "·"
            cot_str = ""
            if cot:
                cot_str = f" | COT:{cot['cot_signal'][:8]}"
            print(f"  {sig} {symbol:14} {name:16} "
                  f"H:{r['h_d']:.2f} P/D:{r['pd_c']:+.3f}% "
                  f"R:{r['rank']}{cot_str}")
        except:
            continue
    results.sort(key=lambda x: x["rank"], reverse=True)
    top   = results[:TOP_N]
    ideal = [r for r in results if "IDEAL" in r.get("entry_q","")]
    aceit = [r for r in results if "ACEIT" in r.get("entry_q","")]
    print(f"\n  Total:{len(results)} | Ideal:{len(ideal)} | "
          f"Aceitável:{len(aceit)}")
    return results, top

def generate_fx_html(results, top):
    def rows_html(lst):
        rows = ""
        for r in lst:
            eq  = r.get("entry_q","—")
            c   = "#4ade80" if "IDEAL" in eq else \
                  "#fbbf24" if "ACEIT" in eq else \
                  "#f43f5e" if "EXTREM" in eq else "#94a3b8"
            hc  = "#4ade80" if r["h_d"]>0.62 else \
                  "#fbbf24" if r["h_d"]>0.52 else "#f87171"
            pdc = "#4ade80" if r["pd_c"]<0 else "#f43f5e"
            cot = r.get("cot")
            cot_cell = "—"
            if cot:
                cc = cot.get("cot_color","#94a3b8")
                cot_cell = (
                    f"<span style='color:{cc};font-size:9px'>"
                    f"{cot['cot_signal'][:10]}</span>"
                )
            rows += f"""
            <tr>
              <td><strong>{r['symbol']}</strong></td>
              <td style="color:#64748b">{r['name']}</td>
              <td><strong>{r['pfmt']}</strong></td>
              <td style="background:{c}22;color:{c};font-size:10px;
                  border-radius:4px;padding:2px 5px">{eq}</td>
              <td style="color:{hc};font-weight:700">{r['h_d']:.2f}</td>
              <td style="color:{pdc}">{r['pd_c']:+.4f}%</td>
              <td style="color:#94a3b8">{r['pd_1w']:+.4f}%</td>
              <td style="color:#475569">{r['pd_1m']:+.4f}%</td>
              <td style="color:#94a3b8">{r['vp']:.0f}%</td>
              <td style="color:#94a3b8">{r['ttmz'] or '—'}</td>
              <td>{cot_cell}</td>
              <td style="font-weight:700;color:{c}">{r['rank']}</td>
            </tr>"""
        return rows
    ideal = [r for r in results if "IDEAL" in r.get("entry_q","")]
    aceit = [r for r in results if "ACEIT" in r.get("entry_q","")]
    header = """<tr>
        <th>Par</th><th>Nome</th><th>Preço</th>
        <th>Entry Quality</th><th>Hurst</th><th>P/D D</th>
        <th>P/D W</th><th>P/D M</th><th>Vol%</th>
        <th>Z-TTM</th><th>COT</th><th>Rank</th>
    </tr>"""
    return f"""
    <div id="fx" class="tab-content section">
      <div class="section-title">FX + MACRO</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;
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
      </div>
      <div class="table-wrap">
        <table>{header}{rows_html(top)}</table>
      </div>
      <div style="color:#64748b;font-size:11px;font-weight:700;
                  margin:16px 0 8px">✅ IDEAIS</div>
      <div class="table-wrap">
        <table>{header}{rows_html(ideal)}</table>
      </div>
    </div>"""