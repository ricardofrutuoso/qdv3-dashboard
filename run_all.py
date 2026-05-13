# ============================================================
# RUN_ALL.PY — Corre todos os scanners e gera dashboard
# ============================================================

import webbrowser
import os
import json
from datetime import datetime

from scanner_volatility  import run_volatility_scanner
from scanner_stocks      import run_stocks_scanner
from scanner_etfs        import run_etfs_scanner
from scanner_fx          import run_fx_scanner, generate_corr_html
from scanner_commodities import run_commodities_scanner
from scanner_options     import run_options_scanner
from scanner_macro       import run_macro_scanner, generate_macro_html
from config              import RUN_DATE, PORTFOLIO, PORTFOLIO_HISTORY, DASHBOARD_FILE

def calc_portfolio(all_results):
    rows     = ""
    total_pl = 0
    prices   = {r["symbol"]: r["price"] for r in all_results}
    for p in PORTFOLIO:
        ticker  = p["ticker"]
        qty     = p["qty"]
        entry   = p["entry"]
        current = prices.get(ticker, None)
        if current is None:
            rows += f"""
            <tr>
                <td><strong>{ticker}</strong></td>
                <td>{qty}</td>
                <td>{entry:.4f}</td>
                <td>N/A</td><td>—</td><td>—</td>
            </tr>"""
            continue
        pl_unit  = current - entry
        pl_pct   = (pl_unit / entry) * 100
        pl_eur   = pl_unit * qty
        total_pl += pl_eur
        color    = "#00d4aa" if pl_eur >= 0 else "#f43f5e"
        arrow    = "▲" if pl_eur >= 0 else "▼"
        rows += f"""
        <tr>
            <td><strong>{ticker}</strong></td>
            <td>{qty}</td>
            <td>{entry:.4f}</td>
            <td>{current:.4f}</td>
            <td style="color:{color}">{arrow} {pl_pct:+.2f}%</td>
            <td class="pl-value" style="color:{color}">
                <strong>{arrow} €{pl_eur:+.2f}</strong>
            </td>
        </tr>"""
    total_color = "#00d4aa" if total_pl >= 0 else "#f43f5e"
    total_arrow = "▲" if total_pl >= 0 else "▼"
    rows += f"""
        <tr class="total-row">
            <td colspan="5"><strong>TOTAL P&L</strong></td>
            <td class="pl-value" style="color:{total_color}">
                <strong>{total_arrow} €{total_pl:+.2f}</strong>
            </td>
        </tr>"""
    return rows, total_pl

def make_rows(results):
    html = ""
    for r in results:
        sig   = r.get("signal", "")
        score = r.get("score", 0)
        color = "#00d4aa22" if sig=="BULLISH" else \
                "#f43f5e22" if sig=="BEARISH" else "#f59e0b22"
        badge = "#00d4aa"  if sig=="BULLISH" else \
                "#f43f5e"  if sig=="BEARISH" else "#f59e0b"
        emoji = "🟢" if sig=="BULLISH" else \
                "🔴" if sig=="BEARISH" else "🟡"
        html += f"""
        <tr style="background:{color}" class="data-row"
            data-signal="{sig}"
            data-symbol="{r.get('symbol','').lower()}"
            data-name="{r.get('name','').lower()}"
            data-market="{r.get('market','').lower()}">
            <td><strong>{r.get('symbol','')}</strong></td>
            <td>{r.get('name','')}</td>
            <td>{r.get('market','')}</td>
            <td><strong>{r.get('pfmt','')}</strong></td>
            <td><span style="background:{badge}22;color:{badge};
                padding:2px 8px;border-radius:4px;
                font-size:11px;font-weight:700">
                {emoji} {sig}</span></td>
            <td><strong>{score:+.1f}</strong></td>
            <td>{r.get('conv','')}</td>
            <td>{r.get('h_d','')}</td>
            <td>{r.get('vp','')}%</td>
            <td>{r.get('pd_c',0):+.2f}%</td>
            <td>{r.get('pd_1w',0):+.2f}%</td>
            <td>{r.get('pd_1m',0):+.2f}%</td>
            <td>{r.get('ttmz','')}</td>
            <td>{r.get('comp','')}</td>
            <td>{r.get('opt','')}</td>
        </tr>"""
    return html

def make_vol_rows(results):
    html = ""
    for r in results:
        sig   = r.get("signal","")
        color = "#00d4aa22" if sig=="BULLISH" else \
                "#f43f5e22" if sig=="BEARISH" else "#f59e0b22"
        badge = "#00d4aa" if sig=="BULLISH" else \
                "#f43f5e" if sig=="BEARISH" else "#f59e0b"
        emoji = "🟢" if sig=="BULLISH" else \
                "🔴" if sig=="BEARISH" else "🟡"
        html += f"""
        <tr style="background:{color}">
            <td><strong>{r.get('name','')}</strong></td>
            <td><strong>{r.get('pfmt','')}</strong></td>
            <td><span style="background:{badge}22;color:{badge};
                padding:2px 8px;border-radius:4px;
                font-size:11px;font-weight:700">
                {emoji} {sig}</span></td>
            <td>{r.get('score',0):+.1f}</td>
            <td>{r.get('pd_c',0):+.2f}%</td>
            <td>{r.get('roc',0):+.2f}pp</td>
            <td>{r.get('ttmz','')}</td>
            <td>{r.get('term_structure','')}</td>
            <td>{r.get('comp','')}</td>
            <td>{r.get('vol_regime','')}</td>
        </tr>"""
    return html

def master_interpretation(score):
    if score is None: return "N/A", "⚪"
    if score >= 80: return "💀 PÂNICO — oportunidade histórica", "🔴"
    if score >= 65: return "😱 MEDO ELEVADO — mercado oversold", "🔴"
    if score >= 50: return "😨 STRESS MODERADO — cautela", "🟡"
    if score >= 35: return "😐 NORMAL — sem sinal claro", "⚪"
    if score >= 20: return "😊 CALMO — risco de complacência", "🟡"
    return "😴 COMPLACÊNCIA EXTREMA — cuidado", "🔴"

def generate_dashboard(stocks, etfs, fx, commodities,
                        vol_results, vol_master,
                        options, all_results,
                        macro_html="", corr_html=""):

    portfolio_rows, total_pl = calc_portfolio(all_results)

    all_ranked = sorted(
        [r for r in all_results if r.get("signal") in ["BULLISH","BEARISH"]],
        key=lambda x: (abs(x.get("score",0)) + x.get("h_d",0)),
        reverse=True
    )[:20]

    bull_count = sum(1 for r in all_results if r.get("signal")=="BULLISH")
    bear_count = sum(1 for r in all_results if r.get("signal")=="BEARISH")
    turn_count = sum(1 for r in all_results if r.get("signal")=="TURNING")
    total      = len(all_results)

    vol_color  = "#f43f5e" if vol_master and vol_master > 65 else \
                 "#f59e0b" if vol_master and vol_master > 40 else "#00d4aa"

    hist_labels = json.dumps([h[0] for h in PORTFOLIO_HISTORY])
    hist_values = json.dumps([h[1] for h in PORTFOLIO_HISTORY])

    search_data = json.dumps([{
        "symbol": r.get("symbol",""),
        "name":   r.get("name",""),
        "market": r.get("market",""),
        "pfmt":   r.get("pfmt",""),
        "signal": r.get("signal",""),
        "score":  r.get("score",0),
        "conv":   r.get("conv",""),
        "h_d":    r.get("h_d",""),
        "vp":     r.get("vp",""),
        "pd_c":   r.get("pd_c",0),
        "pd_1w":  r.get("pd_1w",0),
        "pd_1m":  r.get("pd_1m",0),
        "ttmz":   r.get("ttmz",""),
        "comp":   r.get("comp",""),
        "opt":    r.get("opt",""),
    } for r in all_results])

    table_headers = """
      <th>Ticker</th><th>Nome</th><th>Mercado</th>
      <th>Preço</th><th>Sinal</th><th>Score</th>
      <th>Convicção</th><th>Hurst</th><th>Vol%</th>
      <th>P/D Day</th><th>P/D 1W</th><th>P/D 1M</th>
      <th>Z-TTM</th><th>Brennan</th><th>Opção</th>"""

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QDV3 Dashboard — {RUN_DATE}</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    background:#020817; color:#cbd5e1;
    font-family:'JetBrains Mono',monospace;
    font-size:12px; padding:20px;
  }}
  h1 {{ font-size:22px; color:#f1f5f9;
        letter-spacing:.05em; margin-bottom:4px; }}
  .subtitle {{ color:#475569; font-size:10px;
               letter-spacing:.2em; margin-bottom:24px; }}
  .section {{ margin-bottom:28px; }}
  .section-title {{ font-size:13px; font-weight:700; color:#f1f5f9;
                    letter-spacing:.08em; margin-bottom:12px;
                    padding-bottom:6px; border-bottom:1px solid #1e3a5f; }}
  table {{ width:100%; border-collapse:collapse; font-size:11px; }}
  th {{ background:#0a1628; color:#475569; font-size:9px;
        letter-spacing:.1em; text-transform:uppercase;
        padding:8px 10px; text-align:left; position:sticky; top:0; }}
  td {{ padding:7px 10px; border-bottom:1px solid #0f172a; color:#cbd5e1; }}
  tr:hover td {{ background:#1e293b44; }}
  .total-row td {{ border-top:2px solid #1e3a5f;
                   background:#0a1628; font-size:13px; }}
  .tabs {{ display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }}
  .tab {{ background:#0a1628; border:1px solid #1e3a5f;
          border-radius:6px; padding:6px 14px; cursor:pointer;
          font-size:10px; font-weight:700; letter-spacing:.08em;
          color:#64748b; text-transform:uppercase; transition:.2s; }}
  .tab.active {{ background:#6366f1; color:#fff; border-color:#6366f1; }}
  .tab-content {{ display:none; }}
  .tab-content.active {{ display:block; }}
  .vol-master {{ background:linear-gradient(135deg,#0f172a,#1e293b);
                 border:1px solid #1e3a5f; border-radius:10px;
                 padding:20px; margin-bottom:16px; text-align:center; }}
  .vol-score {{ font-size:48px; font-weight:900; color:{vol_color}; }}
  .distribution {{ display:flex; gap:4px; margin-bottom:24px;
                   height:8px; border-radius:4px; overflow:hidden; }}
  .dist-bull {{ background:#00d4aa; flex:{bull_count}; }}
  .dist-turn {{ background:#f59e0b; flex:{turn_count}; }}
  .dist-bear {{ background:#f43f5e; flex:{bear_count}; }}
  .search-box {{ width:100%; padding:12px 16px;
                 background:#0a1628; border:1px solid #1e3a5f;
                 border-radius:8px; color:#f1f5f9; font-size:13px;
                 font-family:inherit; margin-bottom:16px;
                 outline:none; transition:.2s; }}
  .search-box:focus {{ border-color:#6366f1; }}
  .search-box::placeholder {{ color:#475569; }}
  .search-count {{ color:#475569; font-size:10px;
                   margin-bottom:12px; letter-spacing:.1em; }}
  .pl-hidden {{ filter:blur(6px); transition:.3s; }}
  .pl-toggle {{ background:#1e293b; border:1px solid #1e3a5f;
                border-radius:6px; padding:6px 14px; cursor:pointer;
                font-size:10px; color:#64748b; font-family:inherit;
                margin-bottom:16px; transition:.2s; }}
  .pl-toggle:hover {{ color:#f1f5f9; border-color:#6366f1; }}
  .chart-container {{ background:#0a1628; border:1px solid #1e3a5f;
                      border-radius:10px; padding:20px; margin-bottom:20px; }}
  canvas {{ width:100% !important; }}
  .banner-active {{ outline:2px solid #6366f1 !important; }}
</style>
</head>
<body>

<h1>QDV3 MARKET DASHBOARD</h1>
<div class="subtitle">HURST · FRACTAL · REGIME · VOL — {RUN_DATE}</div>

<!-- BANNERS CLICÁVEIS -->
<div style="display:grid;grid-template-columns:repeat(4,1fr);
            gap:8px;margin-bottom:16px">
  <div id="banner-BULLISH" onclick="filterAll('BULLISH',this)"
       style="background:#00d4aa22;border:1px solid #00d4aa44;
              border-radius:8px;padding:14px;cursor:pointer;
              transition:.2s;user-select:none">
    <div style="font-size:9px;color:#00d4aa;letter-spacing:.15em;
                margin-bottom:6px">🟢 BULLISH</div>
    <div style="font-size:28px;font-weight:900;color:#00d4aa">{bull_count}</div>
    <div style="font-size:9px;color:#64748b;margin-top:4px">
        {round(bull_count/total*100) if total else 0}% · clica para filtrar
    </div>
  </div>
  <div id="banner-BEARISH" onclick="filterAll('BEARISH',this)"
       style="background:#f43f5e22;border:1px solid #f43f5e44;
              border-radius:8px;padding:14px;cursor:pointer;
              transition:.2s;user-select:none">
    <div style="font-size:9px;color:#f43f5e;letter-spacing:.15em;
                margin-bottom:6px">🔴 BEARISH</div>
    <div style="font-size:28px;font-weight:900;color:#f43f5e">{bear_count}</div>
    <div style="font-size:9px;color:#64748b;margin-top:4px">
        {round(bear_count/total*100) if total else 0}% · clica para filtrar
    </div>
  </div>
  <div id="banner-TURNING" onclick="filterAll('TURNING',this)"
       style="background:#f59e0b22;border:1px solid #f59e0b44;
              border-radius:8px;padding:14px;cursor:pointer;
              transition:.2s;user-select:none">
    <div style="font-size:9px;color:#f59e0b;letter-spacing:.15em;
                margin-bottom:6px">🟡 TURNING</div>
    <div style="font-size:28px;font-weight:900;color:#f59e0b">{turn_count}</div>
    <div style="font-size:9px;color:#64748b;margin-top:4px">
        clica para filtrar
    </div>
  </div>
  <div id="banner-ALL" onclick="filterAll('ALL',this)"
       style="background:#1e293b;border:1px solid #334155;
              border-radius:8px;padding:14px;cursor:pointer;
              transition:.2s;user-select:none">
    <div style="font-size:9px;color:#64748b;letter-spacing:.15em;
                margin-bottom:6px">📊 TOTAL</div>
    <div style="font-size:28px;font-weight:900;color:#f1f5f9">{total}</div>
    <div style="font-size:9px;color:#64748b;margin-top:4px">
        todos os tickers
    </div>
  </div>
</div>

<!-- DISTRIBUTION BAR -->
<div class="distribution">
  <div class="dist-bull"></div>
  <div class="dist-turn"></div>
  <div class="dist-bear"></div>
</div>

<!-- TABS -->
<div class="tabs">
  <div class="tab active" onclick="showTab('top',this)">🏆 Top</div>
  <div class="tab" onclick="showTab('vol',this)">📊 Volatilidade</div>
  <div class="tab" onclick="showTab('stocks',this)">📈 Stocks</div>
  <div class="tab" onclick="showTab('etfs',this)">🌍 ETFs</div>
  <div class="tab" onclick="showTab('fx',this)">💱 FX</div>
  <div class="tab" onclick="showTab('correlation',this)">💲 USD Corr</div>
  <div class="tab" onclick="showTab('commodities',this)">🛢️ Commodities</div>
  <div class="tab" onclick="showTab('options',this)">⚡ Opções</div>
  <div class="tab" onclick="showTab('macro',this)">🌐 Macro</div>
  <div class="tab" onclick="showTab('search',this)">🔍 Search</div>
  <div class="tab" onclick="showTab('portfolio',this)">💼</div>
</div>

<!-- TOP -->
<div id="top" class="tab-content active section">
  <div class="section-title">🏆 TOP 20 — UNIVERSE COMPLETO</div>
  <table id="top-table">
    <tr>{table_headers}</tr>{make_rows(all_ranked)}
  </table>
</div>

<!-- VOLATILIDADE -->
<div id="vol" class="tab-content section">
  <div class="vol-master">
    <div style="font-size:9px;color:#475569;letter-spacing:.15em;
                margin-bottom:8px">VOL MASTER SCORE</div>
    <div class="vol-score">{vol_master}/100</div>
    <div style="font-size:10px;color:#64748b;margin-top:8px">
        {master_interpretation(vol_master)[0]}
    </div>
  </div>
  <div class="section-title">📊 VOL UNIVERSE</div>
  <table>
    <tr>
      <th>Nome</th><th>Nível</th><th>Sinal</th><th>Score</th>
      <th>P/D Day</th><th>ROC</th><th>Z-TTM</th>
      <th>Term Structure</th><th>Brennan</th><th>Regime</th>
    </tr>
    {make_vol_rows(vol_results)}
  </table>
</div>

<!-- STOCKS -->
<div id="stocks" class="tab-content section">
  <div class="section-title">📈 STOCKS</div>
  <input class="search-box" placeholder="Filtrar stocks..."
         oninput="filterTable(this,'stocks-table')">
  <table id="stocks-table">
    <tr>{table_headers}</tr>{make_rows(stocks)}
  </table>
</div>

<!-- ETFs -->
<div id="etfs" class="tab-content section">
  <div class="section-title">🌍 ETFs</div>
  <input class="search-box" placeholder="Filtrar ETFs..."
         oninput="filterTable(this,'etfs-table')">
  <table id="etfs-table">
    <tr>{table_headers}</tr>{make_rows(etfs)}
  </table>
</div>

<!-- FX -->
<div id="fx" class="tab-content section">
  <div class="section-title">💱 FX & MACRO</div>
  <table id="fx-table">
    <tr>{table_headers}</tr>{make_rows(fx)}
  </table>
</div>

<!-- USD CORRELATION -->
<div id="correlation" class="tab-content section">
  <div class="section-title">💲 CORRELAÇÃO vs USD (DXY)</div>
  {corr_html}
</div>

<!-- COMMODITIES -->
<div id="commodities" class="tab-content section">
  <div class="section-title">🛢️ COMMODITIES</div>
  <table id="commodities-table">
    <tr>{table_headers}</tr>{make_rows(commodities)}
  </table>
</div>

<!-- OPÇÕES -->
<div id="options" class="tab-content section">
  <div class="section-title">⚡ OPÇÕES DEGIRO</div>
  <table id="options-table">
    <tr>{table_headers}</tr>{make_rows(options)}
  </table>
</div>

{macro_html}

<!-- SEARCH -->
<div id="search" class="tab-content section">
  <div class="section-title">🔍 SEARCH — UNIVERSE COMPLETO</div>
  <input class="search-box" id="global-search"
         placeholder="Pesquisa ticker, nome ou mercado..."
         oninput="globalSearch(this.value)">
  <div class="search-count" id="search-count">
    {total} tickers disponíveis
  </div>
  <table id="search-table">
    <tr>{table_headers}</tr>
    <tbody id="search-results"></tbody>
  </table>
</div>

<!-- PORTFOLIO -->
<div id="portfolio" class="tab-content section">
  <div class="section-title">💼 PORTFOLIO</div>
  <div class="chart-container">
    <div style="font-size:9px;color:#475569;letter-spacing:.15em;
                margin-bottom:12px">EVOLUÇÃO P&L HISTÓRICO</div>
    <canvas id="plChart" height="120"></canvas>
  </div>
  <button class="pl-toggle" onclick="togglePL()">
    👁️ Mostrar / Esconder valores
  </button>
  <table>
    <tr>
      <th>Ticker</th><th>Qty</th><th>Entrada</th>
      <th>Actual</th><th>Var %</th><th>P&L €</th>
    </tr>
    {portfolio_rows}
  </table>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>

function showTab(id, el) {{
  document.querySelectorAll('.tab-content')
          .forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab')
          .forEach(t => t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
}}

function filterAll(signal, el) {{
  document.querySelectorAll('[id^="banner-"]').forEach(b => {{
    b.classList.remove('banner-active');
  }});
  if (el) el.classList.add('banner-active');
  document.querySelectorAll('.tab-content')
          .forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab')
          .forEach(t => t.classList.remove('active'));
  document.getElementById('top').classList.add('active');
  document.querySelectorAll('.tab').forEach(t => {{
    if (t.textContent.includes('Top')) t.classList.add('active');
  }});
  document.querySelectorAll('tr.data-row').forEach(row => {{
    if (signal === 'ALL') {{
      row.style.display = '';
    }} else {{
      row.style.display =
        row.dataset.signal === signal ? '' : 'none';
    }}
  }});
}}

function filterTable(input, tableId) {{
  const q   = input.value.toLowerCase();
  const tbl = document.getElementById(tableId);
  if (!tbl) return;
  tbl.querySelectorAll('tr.data-row').forEach(row => {{
    const txt = row.dataset.symbol + ' ' +
                row.dataset.name   + ' ' +
                row.dataset.market;
    row.style.display = txt.includes(q) ? '' : 'none';
  }});
}}

const ALL_DATA = {search_data};

function globalSearch(q) {{
  const query   = q.toLowerCase().trim();
  const tbody   = document.getElementById('search-results');
  const counter = document.getElementById('search-count');
  if (query.length < 1) {{
    tbody.innerHTML = '';
    counter.textContent = '{total} tickers disponíveis';
    return;
  }}
  const matches = ALL_DATA.filter(r =>
    r.symbol.toLowerCase().includes(query) ||
    r.name.toLowerCase().includes(query)   ||
    r.market.toLowerCase().includes(query)
  );
  counter.textContent = matches.length + ' resultados';
  tbody.innerHTML = matches.map(r => {{
    const sig   = r.signal;
    const color = sig==='BULLISH' ? '#00d4aa22' :
                  sig==='BEARISH' ? '#f43f5e22' : '#f59e0b22';
    const badge = sig==='BULLISH' ? '#00d4aa' :
                  sig==='BEARISH' ? '#f43f5e' : '#f59e0b';
    const emoji = sig==='BULLISH' ? '🟢' :
                  sig==='BEARISH' ? '🔴' : '🟡';
    const sc   = (r.score >= 0 ? '+' : '') + r.score.toFixed(1);
    const pdc  = (r.pd_c  >= 0 ? '+' : '') + r.pd_c.toFixed(2)  + '%';
    const pd1w = (r.pd_1w >= 0 ? '+' : '') + r.pd_1w.toFixed(2) + '%';
    const pd1m = (r.pd_1m >= 0 ? '+' : '') + r.pd_1m.toFixed(2) + '%';
    return `<tr style="background:${{color}}" class="data-row"
               data-signal="${{sig}}">
      <td><strong>${{r.symbol}}</strong></td>
      <td>${{r.name}}</td><td>${{r.market}}</td>
      <td><strong>${{r.pfmt}}</strong></td>
      <td><span style="background:${{badge}}22;color:${{badge}};
          padding:2px 8px;border-radius:4px;
          font-size:11px;font-weight:700">
          ${{emoji}} ${{sig}}</span></td>
      <td><strong>${{sc}}</strong></td>
      <td>${{r.conv}}</td><td>${{r.h_d}}</td>
      <td>${{r.vp}}%</td>
      <td>${{pdc}}</td><td>${{pd1w}}</td><td>${{pd1m}}</td>
      <td>${{r.ttmz}}</td><td>${{r.comp}}</td><td>${{r.opt}}</td>
    </tr>`;
  }}).join('');
}}

let plVisible = false;
function togglePL() {{
  plVisible = !plVisible;
  document.querySelectorAll('.pl-value').forEach(el => {{
    el.classList.toggle('pl-hidden', !plVisible);
  }});
}}
document.addEventListener('DOMContentLoaded', () => {{
  document.querySelectorAll('.pl-value').forEach(el => {{
    el.classList.add('pl-hidden');
  }});
}});

const labels = {hist_labels};
const values = {hist_values};
const colors = values.map(v => v >= 0 ? '#00d4aa' : '#f43f5e');
const ctx = document.getElementById('plChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: labels,
    datasets: [{{
      label: 'P&L €',
      data: values,
      backgroundColor: colors,
      borderRadius: 4,
      borderSkipped: false,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{
        label: ctx => '€' + ctx.raw.toFixed(2)
      }} }}
    }},
    scales: {{
      x: {{ ticks: {{ color:'#475569', font:{{ size:9 }} }},
             grid:  {{ color:'#1e3a5f' }} }},
      y: {{ ticks: {{ color:'#475569', font:{{ size:9 }},
                      callback: v => '€' + v }},
             grid:  {{ color:'#1e3a5f' }},
             border:{{ dash:[4,4] }} }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html

if __name__ == "__main__":

    print("\n" + "="*60)
    print("  QDV3 MASTER SCANNER — A CORRER...")
    print("="*60)

    print("\n[1/7] VOL SCANNER...")
    vol_results, vol_master = run_volatility_scanner()

    print("\n[2/7] STOCKS SCANNER...")
    stocks = run_stocks_scanner()

    print("\n[3/7] ETFs SCANNER...")
    etfs = run_etfs_scanner()

    print("\n[4/7] FX + USD CORRELATION SCANNER...")
    fx, corr_results = run_fx_scanner()
    corr_html = generate_corr_html(corr_results)

    print("\n[5/7] COMMODITIES SCANNER...")
    commodities = run_commodities_scanner()

    print("\n[6/7] OPTIONS SCANNER...")
    options = run_options_scanner()

    print("\n[7/7] MACRO SCANNER...")
    macro_results = run_macro_scanner()
    macro_html    = generate_macro_html(macro_results)

    all_results = stocks + etfs + fx + commodities + vol_results

    print("\n📊 A gerar dashboard...")
    html = generate_dashboard(
        stocks, etfs, fx, commodities,
        vol_results, vol_master,
        options, all_results,
        macro_html, corr_html
    )

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        DASHBOARD_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard guardado: {path}")
    webbrowser.open(f"file:///{path}")
    print("🌐 Browser aberto!")
    print("\n" + "="*60)
    print(f"  CONCLUÍDO — {RUN_DATE}")
    print("="*60 + "\n")