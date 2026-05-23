# ============================================================
# RUN_ALL.PY — QDV3 Master Runner v3
# Corre TODOS os scanners e gera dashboard HTML completo
# ============================================================

import os
import sys
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from config import (CAPITAL, RUN_DATE, DASHBOARD_FILE,
                    PORTFOLIO, CLOSED_TRADES)

# ── IMPORTS TODOS NO TOPO ─────────────────────────────────────
from scanner_volatility import run_volatility_scanner, generate_pcc_html
from scanner_macro      import analyse_macro_indicators, generate_macro_html
from scanner_stocks     import run_stocks_scanner, generate_stocks_html
from scanner_etfs       import run_etfs_scanner, generate_etfs_html
from scanner_fx         import run_fx_scanner, generate_fx_html
from scanner_commodities import run_commodities_scanner, generate_commodities_html
from scanner_options    import run_options_scanner, generate_options_html
from scanner_earnings   import run_earnings_scanner, generate_earnings_html
from scanner_cot        import run_cot_scanner, fetch_cot_data, generate_cot_html
from scanner_options_analytics import run_options_analytics, generate_options_analytics_html
from scanner_trends     import run_trends_scanner, generate_trends_html
from scanner_insider    import run_insider_scanner, generate_insider_html
from alertas            import (portfolio_alert, check_price_alerts,
                                check_risk_alerts, morning_briefing,
                                generate_portfolio_html)

# ── HTML BASE ─────────────────────────────────────────────────
HTML_HEADER = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QDV3 — Dashboard</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ background:#060d1a; color:#e2e8f0; font-family:'JetBrains Mono',
         'Fira Code','Cascadia Code',monospace; font-size:11px; min-height:100vh }}
  .header {{ background:linear-gradient(135deg,#0a1628,#1e293b);
             border-bottom:1px solid #1e3a5f; padding:20px 24px;
             display:flex; justify-content:space-between; align-items:center }}
  .logo {{ font-size:20px; font-weight:900; color:#38bdf8; letter-spacing:3px }}
  .meta {{ color:#475569; font-size:9px; text-align:right }}
  .nav {{ background:#0a1628; border-bottom:1px solid #1e3a5f;
          padding:0 16px; display:flex; overflow-x:auto; gap:2px }}
  .tab {{ padding:10px 16px; cursor:pointer; color:#475569; font-size:10px;
         border:none; background:none; font-family:inherit;
         border-bottom:2px solid transparent; transition:all 0.2s; white-space:nowrap }}
  .tab:hover {{ color:#94a3b8 }}
  .tab.active {{ color:#38bdf8; border-bottom:2px solid #38bdf8; font-weight:700 }}
  .content {{ padding:20px 24px; max-width:1800px; margin:0 auto }}
  .tab-content {{ display:none }}
  .tab-content.active {{ display:block }}
  .section {{ background:linear-gradient(135deg,#0a1628,#0f172a);
             border:1px solid #1e3a5f; border-radius:12px;
             padding:20px; margin-bottom:16px }}
  .section-title {{ color:#38bdf8; font-size:10px; font-weight:700;
                   letter-spacing:2px; margin-bottom:16px;
                   padding-bottom:8px; border-bottom:1px solid #1e3a5f }}
  .table-wrap {{ overflow-x:auto; border-radius:8px; border:1px solid #1e3a5f }}
  table {{ width:100%; border-collapse:collapse }}
  th {{ background:#1e293b; color:#64748b; font-size:9px;
       padding:8px 10px; text-align:left; border-bottom:1px solid #1e3a5f;
       letter-spacing:0.5px; white-space:nowrap }}
  td {{ padding:7px 10px; border-bottom:1px solid #0f172a;
       color:#94a3b8; vertical-align:middle; white-space:nowrap }}
  tr:hover td {{ background:#1e293b22 }}
  tr:last-child td {{ border-bottom:none }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="logo">QDV3</div>
    <div style="color:#475569;font-size:9px;margin-top:4px">
        Quantitative Dynamic Volatility · v3.0</div>
  </div>
  <div class="meta">
    <div style="color:#38bdf8;font-size:11px;font-weight:700;margin-bottom:4px">
        {run_date}</div>
    <div>Capital: €{capital:,.2f}</div>
    <div>DFA Hurst + P/D VWAP + COT + GEX + Insider + Trends</div>
  </div>
</div>

<div class="nav">
  <button class="tab active" onclick="showTab('portfolio')">💼 Portfolio</button>
  <button class="tab" onclick="showTab('stocks')">📈 Stocks</button>
  <button class="tab" onclick="showTab('etfs')">🗂️ ETFs</button>
  <button class="tab" onclick="showTab('fx')">💱 FX</button>
  <button class="tab" onclick="showTab('commodities')">⛽ Commodities</button>
  <button class="tab" onclick="showTab('vol')">🌊 Volatilidade</button>
  <button class="tab" onclick="showTab('options')">⚙️ Options</button>
  <button class="tab" onclick="showTab('macro')">🌍 Macro</button>
  <button class="tab" onclick="showTab('earnings')">📊 Earnings</button>
  <button class="tab" onclick="showTab('cot')">📜 COT</button>
  <button class="tab" onclick="showTab('opt_analytics')">🎯 Opt Analytics</button>
  <button class="tab" onclick="showTab('trends')">📡 Trends</button>
  <button class="tab" onclick="showTab('insider')">👤 Insider</button>
  <button class="tab" onclick="showTab('alerts')">🔔 Alertas</button>
</div>

<div class="content">
"""

HTML_FOOTER = """
</div>
<script>
function showTab(id) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
  document.querySelectorAll('.tab').forEach(t => {
    if (t.getAttribute('onclick') && t.getAttribute('onclick').includes("'" + id + "'"))
      t.classList.add('active');
  });
}
document.querySelector('.tab-content').classList.add('active');
</script>
</body>
</html>"""

# ── ALERTS HTML ───────────────────────────────────────────────
def generate_alerts_html(triggered_alerts):
    rows = ""
    for a in triggered_alerts:
        dc = "#4ade80" if a["direction"] == "above" else "#f43f5e"
        rows += f"""
        <tr>
          <td><strong>{a['ticker']}</strong></td>
          <td style="color:#64748b">{a['name']}</td>
          <td style="color:{dc}">{'≥' if a['direction']=='above' else '≤'} {a['level']}</td>
          <td style="color:#94a3b8">{a['price']:.4f}</td>
          <td style="color:{dc};font-size:10px">{a['note']}</td>
        </tr>"""
    empty = "" if triggered_alerts else \
        "<tr><td colspan='5' style='color:#334155;text-align:center;padding:20px'>Nenhum alerta activo</td></tr>"
    return f"""
    <div id="alerts" class="tab-content section">
      <div class="section-title">ALERTAS ACTIVOS</div>
      <div class="table-wrap">
        <table>
          <tr><th>Ticker</th><th>Nome</th><th>Nível</th>
              <th>Actual</th><th>Nota</th></tr>
          {rows}{empty}
        </table>
      </div>
    </div>"""

# ── MAIN ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  QDV3 — MASTER RUNNER v3")
    print(f"  {RUN_DATE}")
    print("=" * 60)

    # 1. Volatilidade & Risco
    vol_results, vol_master, pcc_results, sentiment_score, \
    market_risk, risk_flags, risk_label = run_volatility_scanner()

    # 2. Macro
    macro_data = analyse_macro_indicators()

    # 3. COT
    cot_results = []
    cot_df = None
    try:
        cot_df      = fetch_cot_data()
        cot_results = run_cot_scanner()
    except Exception as e:
        print(f"  ⚠️  COT erro: {e}")

    # 4. Options Analytics
    opt_analytics_results = []
    try:
        opt_analytics_results = run_options_analytics()
    except Exception as e:
        print(f"  ⚠️  Options analytics erro: {e}")

    # 5. Insider
    insider_results = []
    try:
        insider_results = run_insider_scanner()
    except Exception as e:
        print(f"  ⚠️  Insider erro: {e}")

    # 6. Trends
    trends_results = []
    try:
        trends_results = run_trends_scanner()
    except Exception as e:
        print(f"  ⚠️  Trends erro: {e}")

    # 7. Stocks
    stocks_results, stocks_top = run_stocks_scanner(
        insider_data=insider_results,
        trends_data=trends_results
    )

    # 8. ETFs
    etfs_results, etfs_top = run_etfs_scanner()

    # 9. FX
    fx_results, fx_top = run_fx_scanner(cot_data=cot_results)

    # 10. Commodities
    comm_results, comm_top = run_commodities_scanner(cot_data=cot_results)

    # 11. Options
    opts_results, opts_top = run_options_scanner(
        opt_analytics_data=opt_analytics_results
    )

    # 12. Earnings
    earnings_results = run_earnings_scanner()

    # 13. Portfolio & Alertas
    positions, total_pnl, closed_pnl, global_pnl = portfolio_alert(
        send_telegram=True)
    triggered  = check_price_alerts(send_telegram=True)
    check_risk_alerts(market_risk, risk_flags, send_telegram=True)
    morning_briefing(market_risk,
                     macro_data.get("quad_label"),
                     send_telegram=True)

    # ── GERAR HTML ─────────────────────────────────────────────
    print(f"\n  → Gerando dashboard HTML...")

    html_portfolio   = generate_portfolio_html(positions, total_pnl,
                                               closed_pnl, global_pnl)
    html_stocks      = generate_stocks_html(stocks_results, stocks_top)
    html_etfs        = generate_etfs_html(etfs_results, etfs_top)
    html_fx          = generate_fx_html(fx_results, fx_top)
    html_comm        = generate_commodities_html(comm_results, comm_top)
    html_vol_pcc     = generate_pcc_html(pcc_results, sentiment_score,
                                          market_risk, risk_flags, risk_label)
    html_vol_section = f"""
    <div id="vol" class="tab-content section">
      <div class="section-title">VOLATILIDADE + SENTIMENT + RISK</div>
      {html_vol_pcc}
    </div>"""
    html_options     = generate_options_html(opts_results, opts_top)
    html_macro_inner = generate_macro_html(macro_data)
    html_macro_wrap  = f'<div id="macro" class="tab-content">{html_macro_inner}</div>'
    html_earnings    = generate_earnings_html(earnings_results)
    html_cot         = generate_cot_html(cot_results)
    html_opt_anlys   = generate_options_analytics_html(opt_analytics_results)
    html_trends      = generate_trends_html(trends_results)
    html_insider     = generate_insider_html(insider_results)
    html_alerts      = generate_alerts_html(triggered)

    full_html = (
        HTML_HEADER.format(run_date=RUN_DATE, capital=CAPITAL)
        + html_portfolio
        + html_stocks
        + html_etfs
        + html_fx
        + html_comm
        + html_vol_section
        + html_options
        + html_macro_wrap
        + html_earnings
        + html_cot
        + html_opt_anlys
        + html_trends
        + html_insider
        + html_alerts
        + HTML_FOOTER
    )

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"\n  ✅ Dashboard guardado: {DASHBOARD_FILE}")
    print(f"  📈 Stocks:      {len(stocks_results)}")
    print(f"  🗂️  ETFs:        {len(etfs_results)}")
    print(f"  💱 FX:          {len(fx_results)}")
    print(f"  ⛽ Commodities: {len(comm_results)}")
    print(f"  ⚙️  Options:     {len(opts_results)}")
    print(f"  📊 Earnings:    {len(earnings_results)}")
    print(f"  📜 COT:         {len(cot_results)}")
    print(f"  🎯 Opt Anlys:   {len(opt_analytics_results)}")
    print(f"  📡 Trends:      {len(trends_results)}")
    print(f"  👤 Insider:     {len(insider_results)}")
    print(f"\n  🎯 Market Risk: {market_risk}/100 — {risk_label}")
    print(f"  📐 Quad:        {macro_data.get('quad_label', '—')}")
    import webbrowser
webbrowser.open(DASHBOARD_FILE)
    print(f"\n  ✅ QDV3 completo!")

if __name__ == "__main__":
    main()