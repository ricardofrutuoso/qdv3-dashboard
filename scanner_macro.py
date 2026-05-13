# ============================================================
# SCANNER_MACRO.PY v2
# Hedgeye Quad Framework | Growth + Inflation
# PPI leads CPI | ROC MoM + QoQ + YoY
# Monthly + Quarterly Quads | Ticker Suggestions DeGiro
# ============================================================

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from config import FRED_API_KEY, RUN_DATE

QUAD_COLORS = {
    1: {"bg": "#052e16", "text": "#4ade80",
        "label": "QUAD 1 — Growth↑ Inflation↓",
        "desc":  "Melhor regime para equities de crescimento"},
    2: {"bg": "#14532d", "text": "#86efac",
        "label": "QUAD 2 — Growth↑ Inflation↑",
        "desc":  "Bom para commodities e value"},
    3: {"bg": "#713f12", "text": "#fbbf24",
        "label": "QUAD 3 — Growth↓ Inflation↑",
        "desc":  "Stagflação — ouro, energia, cash"},
    4: {"bg": "#7f1d1d", "text": "#f87171",
        "label": "QUAD 4 — Growth↓ Inflation↓",
        "desc":  "Deflação — bonds longos, ouro"},
    0: {"bg": "#1e293b", "text": "#94a3b8",
        "label": "N/A",
        "desc":  "Dados insuficientes"},
}

QUAD_ASSETS = {
    1: {
        "long":  ["Growth Equities", "Tech", "Consumer Disc"],
        "short": ["Gold", "Bonds", "Defensivos"],
        "etfs":  ["QQQ", "SPY", "XLK", "INDA", "QDV5"],
    },
    2: {
        "long":  ["Commodities", "Energy", "Financials", "EM"],
        "short": ["Long Bonds", "Utilities"],
        "etfs":  ["XLE", "XLF", "EEM", "GLD"],
    },
    3: {
        "long":  ["Gold", "TIPS", "Energy", "Cash"],
        "short": ["Growth Equities", "Long Duration"],
        "etfs":  ["GLD", "TIP", "XLE", "SHY"],
    },
    4: {
        "long":  ["Long Bonds", "Gold", "Utilities", "Cash"],
        "short": ["Equities", "Commodities", "Credit"],
        "etfs":  ["TLT", "GLD", "XLU", "IEF"],
    },
}

QUAD_TICKERS = {
    1: {
        "US":     [("QQQ","Nasdaq ETF","NASDAQ"),("SPY","S&P500","NYSE"),
                   ("NVDA","Nvidia","NASDAQ"),("AAPL","Apple","NASDAQ"),
                   ("MSFT","Microsoft","NASDAQ")],
        "EU":     [("EXS1.DE","EuroStoxx50","XETRA"),("DBXD.DE","DAX ETF","XETRA"),
                   ("SAP.DE","SAP","XETRA"),("ASML.AS","ASML","XAMS"),
                   ("AIR.PA","Airbus","XPAR")],
        "EM":     [("QDV5.DE","MSCI India","XETRA"),("INDA","India ETF","NYSE"),
                   ("MCHI","China ETF","NYSE")],
        "GLOBAL": [("IWDA.AS","MSCI World","XAMS"),("VUSA.AS","S&P500 EUR","XAMS")],
    },
    2: {
        "US":     [("XLE","Energy ETF","NYSE"),("XLF","Financials ETF","NYSE"),
                   ("GLD","Gold ETF","NYSE"),("SPY","S&P500","NYSE"),
                   ("XOM","Exxon","NYSE")],
        "EU":     [("TTE.PA","TotalEnergies","XPAR"),("ENEL.MI","Enel","XMIL"),
                   ("BAS.DE","BASF","XETRA"),("SAN.MC","Santander","XMAD"),
                   ("BCP.LS","BCP","XLIS")],
        "EM":     [("EEM","EM ETF","NYSE"),("MCHI","China ETF","NYSE"),
                   ("BABA","Alibaba","NYSE")],
        "GLOBAL": [("GLD","Gold ETF","NYSE"),("IWDA.AS","MSCI World","XAMS")],
    },
    3: {
        "US":     [("GLD","Gold ETF","NYSE"),("TLT","20Y Bond ETF","NYSE"),
                   ("XLE","Energy ETF","NYSE"),("SLV","Silver ETF","NYSE")],
        "EU":     [("TTE.PA","TotalEnergies","XPAR"),("GALP.LS","Galp","XLIS"),
                   ("EQNR.OL","Equinor","XOSL")],
        "EM":     [("GLD","Gold ETF","NYSE")],
        "GLOBAL": [("GLD","Gold ETF","NYSE"),("IBCK.DE","Bond Corp EUR","XETRA")],
    },
    4: {
        "US":     [("TLT","20Y Bond ETF","NYSE"),("IEF","7-10Y Bond","NYSE"),
                   ("GLD","Gold ETF","NYSE")],
        "EU":     [("EDP.LS","EDP","XLIS"),("ENEL.MI","Enel","XMIL"),
                   ("VER.VI","Verbund","XWBO")],
        "EM":     [("QDV5.DE","MSCI India","XETRA"),("INDA","India ETF","NYSE")],
        "GLOBAL": [("IWDA.AS","MSCI World","XAMS"),("GLD","Gold ETF","NYSE")],
    },
}

COUNTRY_REGION = {
    "US":"US","DE":"EU","FR":"EU","IT":"EU","ES":"EU",
    "PT":"EU","NL":"EU","BE":"EU","AT":"EU","FI":"EU",
    "SE":"EU","DK":"EU","NO":"EU","PL":"EU","CZ":"EU",
    "UK":"EU","CH":"EU","JP":"EM","CN":"EM","IN":"EM",
    "AU":"US","CA":"US","SG":"EM","HK":"EM",
}

COUNTRY_SERIES = {
    "US": ("CPIAUCSL",          "PPIACO",           "INDPRO"),
    "DE": ("DEUCPIALLMINMEI",   "DEUPPDMMINMEI",    None),
    "FR": ("FRACPIALLMINMEI",   None,               None),
    "IT": ("ITACPIALLMINMEI",   None,               None),
    "ES": ("ESPCIALLMINMEI",    None,               None),
    "PT": ("PRTCPIALLMINMEI",   None,               None),
    "NL": ("NLDCPIALLMINMEI",   None,               None),
    "BE": ("BELCPIALLMINMEI",   None,               None),
    "AT": ("AUTCPIALLMINMEI",   None,               None),
    "FI": ("FINCPIALLMINMEI",   None,               None),
    "SE": ("SWECPIALLMINMEI",   None,               None),
    "DK": ("DNKCPIALLMINMEI",   None,               None),
    "NO": ("NORCPIALLMINMEI",   None,               None),
    "PL": ("POLCPIALLMINMEI",   None,               None),
    "CZ": ("CZECPIALLMINMEI",   None,               None),
    "UK": ("GBRCPIALLMINMEI",   "WPPIUKQ",          None),
    "CH": ("CHECPIALLMINMEI",   None,               None),
    "JP": ("JPNCPIALLMINMEI",   "JPNPPDMMINMEI",    None),
    "CN": ("CHNCPIALLMINMEI",   "PIEATI01CNA661N",  None),
    "AU": ("AUSCPIALLMINMEI",   None,               None),
    "CA": ("CPALCY01CAM661N",   None,               None),
    "IN": ("INDCPIALLMINMEI",   None,               None),
    "SG": ("SGPCPIALLMINMEI",   None,               None),
    "HK": ("HKGCPIALLMINMEI",   None,               None),
}

MACRO_COUNTRIES = [
    ("US","🇺🇸 EUA"),   ("DE","🇩🇪 Alemanha"), ("FR","🇫🇷 França"),
    ("IT","🇮🇹 Itália"), ("ES","🇪🇸 Espanha"),  ("PT","🇵🇹 Portugal"),
    ("NL","🇳🇱 Holanda"),("BE","🇧🇪 Bélgica"),  ("AT","🇦🇹 Áustria"),
    ("FI","🇫🇮 Finlândia"),("SE","🇸🇪 Suécia"),  ("DK","🇩🇰 Dinamarca"),
    ("NO","🇳🇴 Noruega"), ("PL","🇵🇱 Polónia"),  ("CZ","🇨🇿 Rep. Checa"),
    ("UK","🇬🇧 Reino Unido"),("CH","🇨🇭 Suíça"), ("JP","🇯🇵 Japão"),
    ("CN","🇨🇳 China"),  ("AU","🇦🇺 Austrália"), ("CA","🇨🇦 Canadá"),
    ("IN","🇮🇳 Índia"),  ("SG","🇸🇬 Singapura"), ("HK","🇭🇰 Hong Kong"),
]

def fetch_fred(series_id, limit=36):
    try:
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={FRED_API_KEY}"
            f"&file_type=json&sort_order=desc&limit={limit}"
        )
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json().get("observations", [])
        records = []
        for obs in data:
            try:
                records.append({
                    "date":  pd.to_datetime(obs["date"]),
                    "value": float(obs["value"])
                })
            except:
                continue
        if not records:
            return None
        return pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    except:
        return None

def calc_roc(df, mom=1, qoq=3, yoy=12):
    if df is None or len(df) < 2:
        return None, None, None
    v     = df["value"].values
    r_mom = round((v[-1]/v[-1-mom] -1)*100, 2) if len(v) > mom  else None
    r_qoq = round((v[-1]/v[-1-qoq] -1)*100, 2) if len(v) > qoq  else None
    r_yoy = round((v[-1]/v[-1-yoy] -1)*100, 2) if len(v) > yoy  else None
    return r_mom, r_qoq, r_yoy

def roc_arrow(val):
    if val is None: return "—", "#94a3b8"
    c = "#4ade80" if val > 0 else "#f87171" if val < 0 else "#fbbf24"
    a = "▲" if val > 0 else "▼" if val < 0 else "→"
    return f"{a} {val:+.2f}%", c

def ppi_leads_cpi(ppi_df, cpi_df, lead=3):
    try:
        if ppi_df is None or cpi_df is None:
            return None, "N/A"
        ppi = ppi_df["value"].values
        cpi = cpi_df["value"].values
        if len(ppi) <= lead+1 or len(cpi) <= 1:
            return None, "N/A"
        ppi_lead = round((ppi[-1-lead]/ppi[-1-lead-1]-1)*100, 2)
        cpi_now  = round((cpi[-1]/cpi[-2]-1)*100, 2)
        if ppi_lead > cpi_now + 0.1:
            sig = "⚠️ INFLAÇÃO A CAMINHO"
        elif ppi_lead < cpi_now - 0.1:
            sig = "✅ INFLAÇÃO CONTROLADA"
        else:
            sig = "〰️ NEUTRO"
        return ppi_lead, sig
    except:
        return None, "N/A"

def yield_curve(y2, y10):
    if y2 is None or y10 is None:
        return "N/A", "#94a3b8"
    s = y10 - y2
    if s > 1.0: return f"NORMAL +{s:.2f}%",  "#4ade80"
    if s > 0:   return f"FLAT +{s:.2f}%",     "#fbbf24"
    return             f"INVERTIDA {s:.2f}%", "#f87171"

def detect_quad(growth_roc, inflation_roc):
    if growth_roc is None or inflation_roc is None:
        return 0
    g = growth_roc    > 0
    i = inflation_roc > 0
    if g and not i: return 1
    if g and i:     return 2
    if not g and i: return 3
    return 4

def analyse_country(code):
    result = {"country": code, "quad_m": 0, "quad_q": 0}
    series = COUNTRY_SERIES.get(code)
    if not series:
        return result
    cpi_id, ppi_id, growth_id = series
    cpi_df    = fetch_fred(cpi_id)    if cpi_id    else None
    ppi_df    = fetch_fred(ppi_id)    if ppi_id    else None
    growth_df = fetch_fred(growth_id) if growth_id else None
    cpi_mom, cpi_qoq, cpi_yoy = calc_roc(cpi_df)
    ppi_mom, ppi_qoq, ppi_yoy = calc_roc(ppi_df)
    gdp_mom, gdp_qoq, gdp_yoy = calc_roc(growth_df)
    ppi_lead, ppi_signal = ppi_leads_cpi(ppi_df, cpi_df)
    y2_df  = fetch_fred("DGS2")   if code=="US" else None
    y10_df = fetch_fred("DGS10")  if code=="US" else None
    bk_df  = fetch_fred("T10YIE") if code=="US" else None
    y2  = float(y2_df["value"].iloc[-1])  if y2_df  is not None else None
    y10 = float(y10_df["value"].iloc[-1]) if y10_df is not None else None
    bk  = float(bk_df["value"].iloc[-1])  if bk_df  is not None else None
    yc_label, yc_color = yield_curve(y2, y10)
    g_mom  = gdp_mom if gdp_mom is not None else cpi_mom
    i_mom  = ppi_mom if ppi_mom is not None else cpi_mom
    g_qoq  = gdp_qoq if gdp_qoq is not None else cpi_qoq
    i_qoq  = ppi_qoq if ppi_qoq is not None else cpi_qoq
    quad_m = detect_quad(g_mom, i_mom)
    quad_q = detect_quad(g_qoq, i_qoq)
    result.update({
        "quad_m": quad_m,   "quad_q": quad_q,
        "gdp_mom": gdp_mom, "gdp_qoq": gdp_qoq,
        "cpi_mom": cpi_mom, "cpi_qoq": cpi_qoq, "cpi_yoy": cpi_yoy,
        "ppi_mom": ppi_mom, "ppi_qoq": ppi_qoq, "ppi_yoy": ppi_yoy,
        "ppi_lead": ppi_lead, "ppi_signal": ppi_signal,
        "y2": y2, "y10": y10, "breakeven": bk,
        "yc_label": yc_label, "yc_color": yc_color,
        "region": COUNTRY_REGION.get(code, "GLOBAL"),
    })
    return result

def run_macro_scanner():
    print("\n" + "="*60)
    print(f"  MACRO SCANNER — {RUN_DATE}")
    print(f"  Quad Framework | PPI leads CPI | MoM + QoQ + YoY")
    print("="*60)
    results = []
    for code, name in MACRO_COUNTRIES:
        try:
            print(f"  → {name}...")
            r         = analyse_country(code)
            r["name"] = name
            results.append(r)
            qm = r.get("quad_m",0)
            qq = r.get("quad_q",0)
            print(f"     Monthly Q{qm} | Quarterly Q{qq}")
        except Exception as e:
            print(f"  ⚠️  {name} — erro: {e}")
    return results

def generate_macro_html(results):

    def fmt(val):
        if val is None:
            return "<td style='color:#475569'>—</td>"
        color = "#4ade80" if val > 0 else \
                "#f87171" if val < 0 else "#fbbf24"
        arrow = "▲" if val > 0 else "▼" if val < 0 else "→"
        return f"<td style='color:{color}'>{arrow} {val:+.2f}%</td>"

    def quad_badge(q):
        qd = QUAD_COLORS[q]
        return (f"<span style='background:{qd['bg']};"
                f"color:{qd['text']};border-radius:4px;"
                f"padding:2px 8px;font-weight:700;font-size:10px'>"
                f"Q{q if q else '?'}</span>")

    q1_m = [r["name"] for r in results if r.get("quad_m")==1]
    q2_m = [r["name"] for r in results if r.get("quad_m")==2]
    q3_m = [r["name"] for r in results if r.get("quad_m")==3]
    q4_m = [r["name"] for r in results if r.get("quad_m")==4]

    banners = ""
    for q, countries in [(1,q1_m),(2,q2_m),(3,q3_m),(4,q4_m)]:
        if not countries:
            continue
        qd = QUAD_COLORS[q]
        banners += f"""
        <div onclick="filterMacro({q})"
             style="background:{qd['bg']};color:{qd['text']};
                    border:1px solid {qd['text']}44;
                    border-radius:8px;padding:12px 16px;
                    cursor:pointer;transition:.2s;user-select:none"
             onmouseover="this.style.opacity='.8'"
             onmouseout="this.style.opacity='1'">
            <div style="font-size:9px;letter-spacing:.15em;
                        margin-bottom:4px">QUAD {q}</div>
            <div style="font-size:20px;font-weight:900;
                        margin-bottom:4px">{len(countries)}</div>
            <div style="font-size:9px;opacity:.8">
                {qd['label'].split('—')[1].strip()}
            </div>
        </div>"""

    banners += f"""
        <div onclick="filterMacro(0)"
             style="background:#1e293b;color:#64748b;
                    border:1px solid #334155;border-radius:8px;
                    padding:12px 16px;cursor:pointer;
                    transition:.2s;user-select:none"
             onmouseover="this.style.opacity='.8'"
             onmouseout="this.style.opacity='1'">
            <div style="font-size:9px;letter-spacing:.15em;
                        margin-bottom:4px">TODOS</div>
            <div style="font-size:20px;font-weight:900;
                        margin-bottom:4px">{len(results)}</div>
            <div style="font-size:9px;opacity:.8">países</div>
        </div>"""

    dominant_quad = max(
        {1:len(q1_m),2:len(q2_m),3:len(q3_m),4:len(q4_m)},
        key=lambda k: {1:len(q1_m),2:len(q2_m),
                       3:len(q3_m),4:len(q4_m)}[k]
    ) if any([q1_m,q2_m,q3_m,q4_m]) else 0

    ticker_html = ""
    if dominant_quad:
        qd      = QUAD_COLORS[dominant_quad]
        tickers = QUAD_TICKERS.get(dominant_quad, {})
        ticker_html += f"""
        <div style="background:{qd['bg']}22;
                    border:1px solid {qd['text']}44;
                    border-radius:8px;padding:16px;margin-bottom:16px">
            <div style="color:{qd['text']};font-weight:700;
                        font-size:12px;margin-bottom:12px">
                🎯 SUGESTÕES PARA REGIME DOMINANTE — {qd['label']}
            </div>
            <div style="display:grid;
                        grid-template-columns:repeat(4,1fr);gap:8px">"""
        for region, t_list in tickers.items():
            ticker_html += f"""
                <div>
                    <div style="color:#475569;font-size:9px;
                                letter-spacing:.1em;margin-bottom:6px">
                        {region}
                    </div>"""
            for sym, name, mkt in t_list[:4]:
                ticker_html += f"""
                    <div style="background:#0a1628;border-radius:4px;
                                padding:6px 8px;margin-bottom:4px;
                                font-size:10px">
                        <strong style="color:{qd['text']}">{sym}</strong>
                        <span style="color:#64748b"> · {name}</span>
                        <span style="color:#334155;font-size:9px">
                            [{mkt}]
                        </span>
                    </div>"""
            ticker_html += "</div>"
        ticker_html += "</div></div>"

    summary_cards = ""
    for q in [1,2,3,4]:
        qd          = QUAD_COLORS[q]
        m_countries = [r["name"] for r in results if r.get("quad_m")==q]
        q_countries = [r["name"] for r in results if r.get("quad_q")==q]
        if not m_countries and not q_countries:
            continue
        summary_cards += f"""
        <div style="background:{qd['bg']};
                    border:1px solid {qd['text']}44;
                    border-radius:8px;padding:14px">
            <div style="color:{qd['text']};font-weight:700;
                        font-size:11px;margin-bottom:8px">
                {qd['label']}
            </div>
            <div style="font-size:9px;color:#94a3b8;margin-bottom:4px">
                MONTHLY:
            </div>
            <div style="color:#cbd5e1;font-size:10px;margin-bottom:8px">
                {' · '.join(m_countries) if m_countries else '—'}
            </div>
            <div style="font-size:9px;color:#94a3b8;margin-bottom:4px">
                QUARTERLY:
            </div>
            <div style="color:#cbd5e1;font-size:10px;margin-bottom:8px">
                {' · '.join(q_countries) if q_countries else '—'}
            </div>
            <div style="color:#64748b;font-size:9px;
                        border-top:1px solid {qd['text']}22;
                        padding-top:8px">
                {qd['desc']}
            </div>
        </div>"""

    rows = ""
    for r in results:
        quad_m = r.get("quad_m", 0)
        quad_q = r.get("quad_q", 0)
        qd     = QUAD_COLORS[quad_m]
        name   = r.get("name","")
        aligned = quad_m == quad_q and quad_m != 0
        a_color = "#4ade80" if aligned else "#f59e0b"
        a_label = "✅ ALINHADO" if aligned else "⚠️ DIVERGENTE"
        ppi_sig = r.get("ppi_signal","—")
        ppi_col = "#f87171" if "CAMINHO"    in str(ppi_sig) else \
                  "#4ade80" if "CONTROLADA" in str(ppi_sig) else "#94a3b8"
        yc      = r.get("yc_label","—")
        yc_c    = r.get("yc_color","#94a3b8")
        bk      = r.get("breakeven")
        bk_s    = f"{bk:.2f}%" if bk else "—"

        rows += f"""
        <tr style="background:{qd['bg']}33"
            class="macro-row" data-quad="{quad_m}">
            <td><strong>{name}</strong></td>
            <td>{quad_badge(quad_m)}</td>
            <td>{quad_badge(quad_q)}</td>
            <td style="color:{a_color};font-size:10px">{a_label}</td>
            {fmt(r.get('gdp_mom'))}
            {fmt(r.get('gdp_qoq'))}
            {fmt(r.get('cpi_mom'))}
            {fmt(r.get('cpi_qoq'))}
            {fmt(r.get('cpi_yoy'))}
            {fmt(r.get('ppi_mom'))}
            {fmt(r.get('ppi_qoq'))}
            {fmt(r.get('ppi_yoy'))}
            <td style="color:{ppi_col};font-size:10px">{ppi_sig}</td>
            <td style="color:{yc_c};font-size:10px">{yc}</td>
            <td style="color:#94a3b8">{bk_s}</td>
        </tr>"""

    html = f"""
    <div id="macro" class="tab-content section">
      <div class="section-title">🌐 MACRO — GROWTH & INFLATION</div>

      <div style="display:grid;grid-template-columns:repeat(5,1fr);
                  gap:8px;margin-bottom:20px">
        {banners}
      </div>

      {ticker_html}

      <div style="display:grid;grid-template-columns:repeat(2,1fr);
                  gap:8px;margin-bottom:20px">
        {summary_cards}
      </div>

      <div class="section-title" style="font-size:11px;margin-top:8px">
        DADOS POR PAÍS — Monthly Quad | Quarterly Quad | Alinhamento
      </div>
      <table id="macro-table">
        <tr>
          <th>País</th>
          <th>Quad M</th><th>Quad Q</th><th>Alinhamento</th>
          <th>GDP MoM</th><th>GDP QoQ</th>
          <th>CPI MoM</th><th>CPI QoQ</th><th>CPI YoY</th>
          <th>PPI MoM</th><th>PPI QoQ</th><th>PPI YoY</th>
          <th>PPI Lead</th><th>Yield Curve</th><th>Breakeven</th>
        </tr>
        {rows}
      </table>

      <div style="color:#334155;font-size:9px;margin-top:12px;
                  text-align:right">
        ✅ Alinhado = Monthly e Quarterly no mesmo Quad
        · Fonte: FRED St. Louis Fed
      </div>
    </div>

    <script>
    function filterMacro(quad) {{
      document.querySelectorAll('.macro-row').forEach(row => {{
        row.style.display =
          (quad === 0 || row.dataset.quad == quad) ? '' : 'none';
      }});
    }}
    </script>"""

    return html

if __name__ == "__main__":
    results = run_macro_scanner()
    print("\n✅ Macro scanner completo!")