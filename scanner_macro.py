# ============================================================
# SCANNER_MACRO.PY — Hedgeye Quad Framework + FRED API
# Quad I/II/III/IV | Growth vs Inflation | Risk Matrix
# ============================================================

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from config import FRED_API_KEY, RUN_DATE

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES = {
    # Growth
    "GDPC1":    "Real GDP QoQ",
    "INDPRO":   "Industrial Production",
    "UNRATE":   "Unemployment Rate",
    "PAYEMS":   "Non-Farm Payrolls",
    "RETAILSMNSA":"Retail Sales",
    "HOUST":    "Housing Starts",
    "UMCSENT":  "Consumer Sentiment",
    "DSPIC96":  "Real Disposable Income",
    # Inflation
    "CPIAUCSL": "CPI YoY",
    "CPILFESL": "Core CPI",
    "PCEPI":    "PCE",
    "PCEPILFE": "Core PCE",
    "PPIFIS":   "PPI",
    "MICH":     "Inflation Expectations",
    "T10YIE":   "10Y Breakeven",
    "DTWEXBGS": "Dollar Index",
    # Rates
    "DFF":      "Fed Funds Rate",
    "DGS10":    "10Y Treasury",
    "DGS2":     "2Y Treasury",
    "DGS30":    "30Y Treasury",
    "T10Y2Y":   "10Y-2Y Spread",
    "T10Y3M":   "10Y-3M Spread",
    # Financial Conditions
    "NFCI":     "Fin Conditions Chicago",
    "ANFCI":    "Adj Fin Conditions",
    "DCOILWTICO":"WTI Crude",
}

MARKET_INDICATORS = {
    "^VIX":      "VIX",
    "^TNX":      "10Y Yield",
    "^TYX":      "30Y Yield",
    "DX-Y.NYB":  "Dollar Index",
    "GC=F":      "Gold",
    "CL=F":      "WTI Crude",
    "SPY":       "S&P 500",
    "QQQ":       "Nasdaq",
    "TLT":       "20Y Bond",
    "HYG":       "High Yield",
    "LQD":       "IG Corp Bond",
    "EEM":       "Emerging Mkt",
    "GLD":       "Gold ETF",
    "SLV":       "Silver ETF",
    "BTC-USD":   "Bitcoin",
}

def fred_get(series_id, limit=12):
    try:
        params = {
            "series_id":       series_id,
            "api_key":         FRED_API_KEY,
            "file_type":       "json",
            "sort_order":      "desc",
            "observation_start":"2020-01-01",
            "limit":           limit,
        }
        r = requests.get(FRED_BASE, params=params, timeout=15)
        if r.status_code != 200: return None
        obs = r.json().get("observations", [])
        if not obs: return None
        df = pd.DataFrame(obs)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date")
    except:
        return None

def calc_yoy(series):
    try:
        if len(series) < 13: return None
        current = float(series.iloc[-1])
        ago12   = float(series.iloc[-13])
        if ago12 == 0: return None
        return round((current - ago12) / abs(ago12) * 100, 2)
    except:
        return None

def calc_acceleration(series):
    try:
        if len(series) < 3: return None
        c = float(series.iloc[-1])
        p = float(series.iloc[-2])
        pp= float(series.iloc[-3])
        roc1 = c - p
        roc2 = p - pp
        return round(roc1 - roc2, 4)
    except:
        return None

def classify_quad(growth_accel, inflation_accel):
    if growth_accel > 0 and inflation_accel > 0:
        return 2, "QUAD 2", "Growth ↑ Inflation ↑", "#fbbf24"
    if growth_accel > 0 and inflation_accel <= 0:
        return 1, "QUAD 1", "Growth ↑ Inflation ↓", "#4ade80"
    if growth_accel <= 0 and inflation_accel > 0:
        return 3, "QUAD 3", "Growth ↓ Inflation ↑", "#f97316"
    return 4, "QUAD 4", "Growth ↓ Inflation ↓", "#f43f5e"

QUAD_PLAYBOOK = {
    1: {
        "best":  ["Equities Crescimento","Small Caps","Crypto","Commodities"],
        "worst": ["Gold","Bonds","Defensivos"],
        "desc":  "Goldilocks — melhor ambiente para equities de crescimento",
        "action":"LONG equities crescimento, SHORT bonds, underweight defensivos",
    },
    2: {
        "best":  ["Commodities","Energy","Value Stocks","TIPS","Ouro"],
        "worst": ["Growth Equities","Long Bonds","Defensivos"],
        "desc":  "Reflation — commodities e value outperformam",
        "action":"LONG commodities e energy, SHORT growth e duration longa",
    },
    3: {
        "best":  ["Ouro","Defensivos","Short Duration","Cash","Dólar"],
        "worst": ["Equities","Commodities Crescimento","Crypto","EM"],
        "desc":  "Estagflação — o pior ambiente. Dólar e ouro como refúgio",
        "action":"CASH + GOLD + curto prazo. Reduz tudo o resto.",
    },
    4: {
        "best":  ["Long Bonds","Dólar","Utilities","Consumer Staples"],
        "worst": ["Commodities","Banks","EM","Energy","Crypto"],
        "desc":  "Recessão/Deflação — bonds e dólar como refúgio",
        "action":"LONG duration, SHORT commodities e banks, underweight EM",
    },
}

def analyse_macro_indicators():
    print(f"\n{'='*60}")
    print(f"  MACRO SCANNER — {RUN_DATE}")
    print(f"  Hedgeye Quad Framework | FRED API")
    print("="*60)

    fred_data = {}
    print("  → Fetching FRED data...")
    for series_id, label in FRED_SERIES.items():
        df = fred_get(series_id)
        if df is not None and not df.empty:
            latest    = float(df["value"].iloc[-1])
            prev      = float(df["value"].iloc[-2]) if len(df)>1 else latest
            yoy       = calc_yoy(df["value"])
            accel     = calc_acceleration(df["value"])
            last_date = str(df["date"].iloc[-1])[:10]
            fred_data[series_id] = {
                "label":     label,
                "value":     latest,
                "prev":      prev,
                "change":    round(latest-prev, 4),
                "yoy":       yoy,
                "accel":     accel,
                "date":      last_date,
                "series":    df["value"].tolist(),
            }
            print(f"  ✓ {label:30} {latest:.2f}  "
                  f"YoY:{yoy:+.2f}%" if yoy else
                  f"  ✓ {label:30} {latest:.2f}")
        else:
            print(f"  ✗ {series_id} — sem dados")

    # Market indicators
    print("\n  → Market indicators...")
    market_data = {}
    for symbol, label in MARKET_INDICATORS.items():
        try:
            end   = datetime.today()
            start = end - timedelta(days=90)
            df    = yf.download(symbol, start=start, end=end,
                                progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            closes = df["Close"].astype(float).values.flatten()
            if len(closes) < 2: continue
            price  = float(closes[-1])
            p1d    = float(closes[-2])
            p1w    = float(closes[-6])  if len(closes)>5  else price
            p1m    = float(closes[-22]) if len(closes)>21 else price
            market_data[symbol] = {
                "label":  label,
                "price":  round(price,2),
                "chg_1d": round((price-p1d)/p1d*100,2) if p1d else 0,
                "chg_1w": round((price-p1w)/p1w*100,2) if p1w else 0,
                "chg_1m": round((price-p1m)/p1m*100,2) if p1m else 0,
            }
        except:
            continue

    # Quad determination
    growth_accel    = None
    inflation_accel = None
    # Growth proxy: INDPRO acceleration
    if "INDPRO" in fred_data:
        growth_accel = fred_data["INDPRO"]["accel"]
    elif "GDPC1" in fred_data:
        growth_accel = fred_data["GDPC1"]["accel"]
    # Inflation proxy: CPI acceleration
    if "CPIAUCSL" in fred_data:
        inflation_accel = fred_data["CPIAUCSL"]["accel"]
    elif "PCEPILFE" in fred_data:
        inflation_accel = fred_data["PCEPILFE"]["accel"]

    if growth_accel is not None and inflation_accel is not None:
        quad_num, quad_label, quad_desc, quad_color = classify_quad(
            growth_accel, inflation_accel)
    else:
        quad_num = 0; quad_label = "AGUARDA DADOS"
        quad_desc  = "Dados insuficientes"
        quad_color = "#94a3b8"

    quad_playbook = QUAD_PLAYBOOK.get(quad_num, {})

    # Yield curve
    yield_curve = None
    if "DGS10" in fred_data and "DGS2" in fred_data:
        yield_curve = round(
            fred_data["DGS10"]["value"] -
            fred_data["DGS2"]["value"], 3)

    # Fed Funds
    fed_funds = fred_data.get("DFF", {}).get("value")

    # Real Rate = 10Y - Breakeven
    real_rate = None
    if "DGS10" in fred_data and "T10YIE" in fred_data:
        real_rate = round(
            fred_data["DGS10"]["value"] -
            fred_data["T10YIE"]["value"], 3)

    print(f"\n  ─────────────────────────────────────")
    print(f"  QUAD: {quad_label} — {quad_desc}")
    print(f"  Growth Accel:    {growth_accel:.4f}")
    print(f"  Inflation Accel: {inflation_accel:.4f}")
    print(f"  Yield Curve:     {yield_curve}")
    print(f"  Fed Funds:       {fed_funds}")
    print(f"  Real Rate:       {real_rate}")

    return {
        "fred":            fred_data,
        "market":          market_data,
        "quad_num":        quad_num,
        "quad_label":      quad_label,
        "quad_desc":       quad_desc,
        "quad_color":      quad_color,
        "quad_playbook":   quad_playbook,
        "growth_accel":    growth_accel,
        "inflation_accel": inflation_accel,
        "yield_curve":     yield_curve,
        "fed_funds":       fed_funds,
        "real_rate":       real_rate,
    }

def generate_macro_html(macro):
    if not macro: return ""
    qn  = macro["quad_num"]
    ql  = macro["quad_label"]
    qd  = macro["quad_desc"]
    qc  = macro["quad_color"]
    pb  = macro.get("quad_playbook", {})
    ga  = macro.get("growth_accel")
    ia  = macro.get("inflation_accel")
    yc  = macro.get("yield_curve")
    ff  = macro.get("fed_funds")
    rr  = macro.get("real_rate")

    # Quad matrix visualization
    def quad_box(n, label, color, active):
        border = f"border:2px solid {color};" if active else \
                 "border:1px solid #1e293b;"
        bg     = f"background:{color}22;" if active else "background:#0a1628;"
        scale  = "transform:scale(1.05);" if active else ""
        return (
            f"<div style='{bg}{border}{scale}border-radius:8px;"
            f"padding:12px;text-align:center'>"
            f"<div style='font-size:10px;color:#475569;margin-bottom:4px'>"
            f"Q{n}</div>"
            f"<div style='font-size:12px;font-weight:700;"
            f"color:{'#fff' if active else '#475569'}'>{label}</div>"
            f"</div>"
        )

    q1_box = quad_box(1,"G↑ I↓","#4ade80",qn==1)
    q2_box = quad_box(2,"G↑ I↑","#fbbf24",qn==2)
    q3_box = quad_box(3,"G↓ I↑","#f97316",qn==3)
    q4_box = quad_box(4,"G↓ I↓","#f43f5e",qn==4)

    best_html = "".join(
        f"<span style='background:#4ade8022;color:#4ade80;"
        f"font-size:9px;padding:2px 8px;border-radius:4px;"
        f"margin:2px'>{x}</span>"
        for x in pb.get("best",[])
    )
    worst_html = "".join(
        f"<span style='background:#f43f5e22;color:#f43f5e;"
        f"font-size:9px;padding:2px 8px;border-radius:4px;"
        f"margin:2px'>{x}</span>"
        for x in pb.get("worst",[])
    )

    # Fred rows
    fred_rows = ""
    key_series = [
        "CPIAUCSL","CPILFESL","INDPRO","PAYEMS",
        "UNRATE","DFF","DGS10","DGS2","T10Y2Y","NFCI",
        "UMCSENT","T10YIE",
    ]
    for sid in key_series:
        d = macro.get("fred",{}).get(sid)
        if not d: continue
        chg = d.get("change",0)
        yoy = d.get("yoy")
        cc  = "#4ade80" if chg>=0 else "#f43f5e"
        yc2 = "#4ade80" if (yoy or 0)>=0 else "#f43f5e"
        fred_rows += f"""
        <tr>
          <td>{d['label']}</td>
          <td><strong>{d['value']:.2f}</strong></td>
          <td style="color:{cc}">{chg:+.4f}</td>
          <td style="color:{yc2}">{f'{yoy:+.2f}%' if yoy else '—'}</td>
          <td style="color:#475569;font-size:9px">{d['date']}</td>
        </tr>"""

    # Market rows
    mkt_rows = ""
    for sym, d in macro.get("market",{}).items():
        c1 = "#4ade80" if d["chg_1d"]>0 else "#f43f5e"
        c2 = "#4ade80" if d["chg_1w"]>0 else "#f43f5e"
        c3 = "#4ade80" if d["chg_1m"]>0 else "#f43f5e"
        mkt_rows += f"""
        <tr>
          <td>{d['label']}</td>
          <td>{d['price']}</td>
          <td style="color:{c1}">{d['chg_1d']:+.2f}%</td>
          <td style="color:{c2}">{d['chg_1w']:+.2f}%</td>
          <td style="color:{c3}">{d['chg_1m']:+.2f}%</td>
        </tr>"""

    yc_color = "#f43f5e" if (yc or 0)<0 else "#4ade80"
    rr_color = "#f43f5e" if (rr or 0)<0 else "#4ade80"

    return f"""
    <div id="macro" class="tab-content section">
      <div class="section-title">MACRO — HEDGEYE QUAD FRAMEWORK</div>

      <div style="display:grid;grid-template-columns:2fr 1fr;
                  gap:20px;margin-bottom:20px">
        <div>
          <div style="background:linear-gradient(135deg,#0a1628,#1e293b);
                      border:2px solid {qc}44;border-radius:12px;padding:20px">
            <div style="display:grid;grid-template-columns:1fr 1fr;
                        gap:8px;margin-bottom:16px">
              {q1_box}{q2_box}{q3_box}{q4_box}
            </div>
            <div style="text-align:center">
              <div style="font-size:28px;font-weight:900;color:{qc}">
                  {ql}</div>
              <div style="color:{qc};font-size:12px;margin-top:4px">
                  {qd}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;
                          gap:8px;margin-top:12px">
                <div style="text-align:center">
                  <div style="font-size:9px;color:#475569">Growth Accel</div>
                  <div style="font-size:16px;font-weight:700;
                              color:{'#4ade80' if (ga or 0)>0 else '#f43f5e'}">
                      {'▲' if (ga or 0)>0 else '▼'} {f'{abs(ga):.4f}' if ga else '—'}</div>
                </div>
                <div style="text-align:center">
                  <div style="font-size:9px;color:#475569">Inflation Accel</div>
                  <div style="font-size:16px;font-weight:700;
                              color:{'#f43f5e' if (ia or 0)>0 else '#4ade80'}">
                      {'▲' if (ia or 0)>0 else '▼'} {f'{abs(ia):.4f}' if ia else '—'}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div style="background:#0a1628;border:1px solid {qc}44;
                      border-radius:8px;padding:14px;margin-bottom:8px">
            <div style="font-size:9px;color:#475569;margin-bottom:8px">
                CHAVE MAESTRA</div>
            <div style="font-size:10px;color:#64748b;line-height:1.6">
                {pb.get('action','—')}</div>
          </div>
          <div style="background:#0a1628;border:1px solid #1e3a5f;
                      border-radius:8px;padding:12px;margin-bottom:8px">
            <div style="font-size:9px;color:#475569;margin-bottom:6px">
                LONG</div>
            <div>{best_html}</div>
          </div>
          <div style="background:#0a1628;border:1px solid #1e3a5f;
                      border-radius:8px;padding:12px">
            <div style="font-size:9px;color:#475569;margin-bottom:6px">
                SHORT / EVITAR</div>
            <div>{worst_html}</div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);
                  gap:8px;margin-bottom:20px">
        <div style="background:#0a1628;border:1px solid #1e3a5f;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:9px;color:#475569">YIELD CURVE (10-2Y)</div>
          <div style="font-size:20px;font-weight:900;color:{yc_color}">
              {f'{yc:+.3f}%' if yc else '—'}</div>
          <div style="font-size:9px;color:#334155">
              {'Invertida = recessão' if (yc or 0)<0 else 'Normal'}</div>
        </div>
        <div style="background:#0a1628;border:1px solid #1e3a5f;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:9px;color:#475569">FED FUNDS</div>
          <div style="font-size:20px;font-weight:900;color:#94a3b8">
              {f'{ff:.2f}%' if ff else '—'}</div>
          <div style="font-size:9px;color:#334155">taxa actual</div>
        </div>
        <div style="background:#0a1628;border:1px solid #1e3a5f;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:9px;color:#475569">REAL RATE (10Y-BE)</div>
          <div style="font-size:20px;font-weight:900;color:{rr_color}">
              {f'{rr:+.3f}%' if rr else '—'}</div>
          <div style="font-size:9px;color:#334155">
              {'Restritivo' if (rr or 0)>1.5 else 'Acomodativo'}</div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;
                  gap:12px;margin-bottom:16px">
        <div>
          <div style="font-size:10px;font-weight:700;color:#64748b;
                      margin-bottom:8px">FRED — INDICADORES CHAVE</div>
          <div class="table-wrap">
            <table>
              <tr><th>Indicador</th><th>Valor</th><th>Δ</th>
                  <th>YoY</th><th>Data</th></tr>
              {fred_rows}
            </table>
          </div>
        </div>
        <div>
          <div style="font-size:10px;font-weight:700;color:#64748b;
                      margin-bottom:8px">MERCADOS</div>
          <div class="table-wrap">
            <table>
              <tr><th>Asset</th><th>Preço</th>
                  <th>1D</th><th>1W</th><th>1M</th></tr>
              {mkt_rows}
            </table>
          </div>
        </div>
      </div>
    </div>"""