# ============================================================
# SCANNER_OPTIONS.PY — Options Universe QDV3
# DFA Hurst + GEX + Max Pain + IV Skew + Rank
# ============================================================

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from config import CAPITAL, RUN_DATE, TOP_N, MIN_HURST
from universe import OPTIONS_UNIVERSE
from indicators import analyse

def entry_quality(r, opt_analytics=None):
    pd_c=r.get("pd_c",0); pd_1w=r.get("pd_1w",0)
    h=r.get("h_d",0.5);   vp=r.get("vp",50)
    comp=r.get("comp","NORMAL"); score=r.get("score",0)
    adx=r.get("adx",0)
    # Bonus GEX
    gex_bonus = 0
    if opt_analytics and opt_analytics.get("gex") is not None:
        gex = opt_analytics["gex"]
        if gex > 1.0:   gex_bonus = -0.3  # vol comprimida = bom para range
        elif gex < -1.0: gex_bonus = 0.3  # vol expansiva
    adj = score + gex_bonus
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

def calc_rank(r, opt_analytics=None):
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
    if opt_analytics:
        gex = opt_analytics.get("gex")
        if gex is not None:
            if abs(gex) > 2.0: score+=8
            elif abs(gex) > 1.0: score+=4
        skew = (opt_analytics.get("iv_skew") or {}).get("skew",0)
        if abs(skew) > 10: score+=5
    return min(round(score),100)

def format_opt_signal(r):
    h=r.get("h_d",0.5); vp=r.get("vp",50); score=r.get("score",0)
    if abs(score)<0.6: return "Aguardar"
    direction="CALL" if score>0 else "PUT"
    expiry="Monthly" if vp<65 else "Weekly"
    conv="Alta" if h>0.62 else "Media" if h>0.52 else "Baixa"
    return f"{direction} | {expiry} | {conv}"

def run_options_scanner(opt_analytics_data=None, limit=None):
    print(f"\n{'='*60}")
    print(f"  OPTIONS SCANNER — {RUN_DATE}")
    print(f"  DFA Hurst + GEX + Max Pain + IV Skew")
    print("="*60)
    opt_map = {}
    if opt_analytics_data:
        for r in opt_analytics_data:
            opt_map[r["symbol"]] = r
    tickers = list(set(OPTIONS_UNIVERSE))
    if limit: tickers = tickers[:limit]
    results = []
    for symbol, name, market in tickers:
        try:
            r = analyse(symbol, name, market)
            if r is None: continue
            if r["h_d"] < MIN_HURST: continue
            opt = opt_map.get(symbol)
            r["entry_q"]  = entry_quality(r, opt)
            r["rank"]     = calc_rank(r, opt)
            r["opt"]      = opt
            r["opt_sig"]  = format_opt_signal(r)
            results.append(r)
            sig = "✅" if "IDEAL" in r["entry_q"] else \
                  "🟡" if "ACEIT" in r["entry_q"] else "·"
            opt_str = ""
            if opt and opt.get("gex") is not None:
                opt_str = f" GEX:{opt['gex']:+.2f}Bn"
            print(f"  {sig} {symbol:10} {name:18} "
                  f"H:{r['h_d']:.2f} P/D:{r['pd_c']:+.2f}% "
                  f"R:{r['rank']}{opt_str}")
        except:
            continue
    results.sort(key=lambda x: x["rank"], reverse=True)
    top   = results[:TOP_N]
    ideal = [r for r in results if "IDEAL" in r.get("entry_q","")]
    aceit = [r for r in results if "ACEIT" in r.get("entry_q","")]
    print(f"\n  Total:{len(results)} | Ideal:{len(ideal)} | "
          f"Aceitável:{len(aceit)}")
    return results, top

def generate_options_html(results, top):
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
            opt = r.get("opt")
            gex_cell = "—"; mp_cell = "—"; skew_cell = "—"
            if opt:
                gex = opt.get("gex")
                mp  = opt.get("max_pain")
                mpp = opt.get("mp_pct")
                skew_d= (opt.get("iv_skew") or {}).get("skew",None)
                if gex is not None:
                    gc = "#4ade80" if gex>0 else "#f43f5e"
                    gex_cell = f"<span style='color:{gc}'>{gex:+.2f}Bn</span>"
                if mp:
                    mpc = "#4ade80" if mpp and mpp>0 else "#f43f5e"
                    mp_cell = f"<span style='color:{mpc}'>${mp:.0f}</span>"
                if skew_d is not None:
                    sc = "#f43f5e" if skew_d>10 else \
                         "#fbbf24" if skew_d>5  else "#94a3b8"
                    skew_cell = f"<span style='color:{sc}'>{skew_d:+.1f}%</span>"
            rows += f"""
            <tr>
              <td><strong>{r['symbol']}</strong></td>
              <td style="color:#64748b">{r['name'][:16]}</td>
              <td style="color:#475569;font-size:9px">{r['market']}</td>
              <td><strong>{r['pfmt']}</strong></td>
              <td style="background:{c}22;color:{c};font-size:10px;
                  border-radius:4px;padding:2px 5px">{eq}</td>
              <td style="color:{hc};font-weight:700">{r['h_d']:.2f}</td>
              <td style="color:{pdc}">{r['pd_c']:+.2f}%</td>
              <td style="color:#94a3b8">{r['vp']:.0f}%</td>
              <td style="color:#64748b;font-size:10px">
                  {r.get('opt_sig','—')}</td>
              <td>{gex_cell}</td>
              <td>{mp_cell}</td>
              <td>{skew_cell}</td>
              <td style="font-weight:700;color:{c}">{r['rank']}</td>
            </tr>"""
        return rows
    ideal = [r for r in results if "IDEAL" in r.get("entry_q","")]
    aceit = [r for r in results if "ACEIT" in r.get("entry_q","")]
    header = """<tr>
        <th>Ticker</th><th>Nome</th><th>Mercado</th><th>Preço</th>
        <th>Entry Quality</th><th>Hurst</th><th>P/D D</th>
        <th>Vol%</th><th>Opção Sugerida</th>
        <th>GEX</th><th>Max Pain</th><th>IV Skew</th><th>Rank</th>
    </tr>"""
    return f"""
    <div id="options" class="tab-content section">
      <div class="section-title">OPTIONS — GEX + MAX PAIN + IV SKEW</div>
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