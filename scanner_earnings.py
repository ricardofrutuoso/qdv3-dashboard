# ============================================================
# SCANNER_EARNINGS.PY — Earnings Calendar + PODS + Setup
# EPS Surprise | Revenue Beat | Options Setup
# Gratuito via yfinance
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

from config import RUN_DATE
from indicators import analyse

EARNINGS_TICKERS = [
    ("NVDA",  "Nvidia"),   ("AAPL",  "Apple"),
    ("MSFT",  "Microsoft"),("AMD",   "AMD"),
    ("META",  "Meta"),     ("AMZN",  "Amazon"),
    ("GOOGL", "Alphabet"), ("TSLA",  "Tesla"),
    ("NFLX",  "Netflix"),  ("CRM",   "Salesforce"),
    ("AVGO",  "Broadcom"), ("ADBE",  "Adobe"),
    ("INTC",  "Intel"),    ("QCOM",  "Qualcomm"),
    ("JPM",   "JPMorgan"), ("GS",    "Goldman"),
    ("BAC",   "BofA"),     ("MS",    "Morgan Stanley"),
    ("V",     "Visa"),     ("MA",    "Mastercard"),
    ("LLY",   "Eli Lilly"),("UNH",   "UnitedHealth"),
    ("JNJ",   "J&J"),      ("PFE",   "Pfizer"),
    ("XOM",   "Exxon"),    ("CVX",   "Chevron"),
    ("WMT",   "Walmart"),  ("COST",  "Costco"),
    ("MELI",  "MercadoLibre"),("COIN","Coinbase"),
    ("PLTR",  "Palantir"), ("SNOW",  "Snowflake"),
    ("MSTR",  "MicroStrategy"),
]

def fetch_earnings_info(symbol, name):
    try:
        t    = yf.Ticker(symbol)
        info = t.info or {}

        # Dados financeiros
        eps_ttm      = info.get("trailingEps")
        eps_fwd      = info.get("forwardEps")
        rev_ttm      = info.get("totalRevenue")
        rev_growth   = info.get("revenueGrowth")
        eps_growth   = info.get("earningsGrowth")
        earnings_date= info.get("earningsTimestamp")
        pe_ttm       = info.get("trailingPE")
        pe_fwd       = info.get("forwardPE")
        peg          = info.get("pegRatio")
        price        = info.get("regularMarketPrice") or \
                       info.get("currentPrice") or \
                       info.get("previousClose")
        gross_margin = info.get("grossMargins")
        profit_margin= info.get("profitMargins")
        debt_equity  = info.get("debtToEquity")
        short_ratio  = info.get("shortRatio")

        # Próxima earnings
        next_earnings = None
        days_to_earnings = None
        if earnings_date:
            try:
                dt = datetime.fromtimestamp(earnings_date)
                next_earnings     = dt.strftime("%d %b %Y")
                days_to_earnings  = (dt - datetime.today()).days
            except:
                pass

        if not price: return None
        pfmt = f"${price:.2f}" if price >= 1 else f"${price:.4f}"

        # EPS surprise proxy
        surprise_pct = None
        if eps_ttm and eps_fwd:
            try:
                surprise_pct = round((eps_fwd-eps_ttm)/abs(eps_ttm)*100, 1) \
                               if eps_ttm != 0 else None
            except:
                pass

        # PODS score (Pre-Earnings Options Directional Setup)
        # Condições: volatilidade baixa + trend + compressão + momentum
        pods_score = 0
        r_tech = analyse(symbol, name, "NASDAQ")
        if r_tech:
            h  = r_tech.get("h_d", 0.5)
            vp = r_tech.get("vp", 50)
            pd_c = r_tech.get("pd_c", 0)
            comp = r_tech.get("comp", "")
            # Hurst
            if h >= 0.62: pods_score += 25
            elif h >= 0.55: pods_score += 15
            # Vol comprimida antes das earnings = ideal
            if vp <= 25: pods_score += 25
            elif vp <= 40: pods_score += 15
            elif vp <= 55: pods_score += 5
            # P/D alignment
            if pd_c < 0 and r_tech.get("pd_1w",0) < 0:
                pods_score += 20
            # Brennan compression
            if "COMPRESSION+TRENDING" in comp: pods_score += 20
            elif "COMPRESSED" in comp: pods_score += 10
            # Fundamentos
            if rev_growth and rev_growth > 0.10: pods_score += 10
            if eps_growth  and eps_growth  > 0:  pods_score += 10
        else:
            r_tech = {}

        pods_score = min(round(pods_score), 100)

        # Classificação PODS
        if pods_score >= 75:
            pods_label = "SETUP IDEAL"
            pods_color = "#4ade80"
        elif pods_score >= 50:
            pods_label = "SETUP BOM"
            pods_color = "#86efac"
        elif pods_score >= 30:
            pods_label = "SETUP FRACO"
            pods_color = "#fbbf24"
        else:
            pods_label = "AGUARDA"
            pods_color = "#94a3b8"

        # Recomendação de opção para earnings
        opt_rec = "—"
        if r_tech.get("score", 0) and r_tech.get("h_d"):
            sc = r_tech.get("score", 0)
            h  = r_tech.get("h_d", 0.5)
            vp = r_tech.get("vp", 50)
            if abs(sc) >= 0.6 and h >= 0.55:
                direction = "CALL" if sc < 0 else "PUT"
                timing    = "Long Vol" if vp < 30 else "Debit Spread"
                exp       = "Semanal" if days_to_earnings and days_to_earnings <= 7 else "Mensal"
                opt_rec   = f"{direction} | {timing} | {exp}"

        # Formatação de valores
        def fmt_pct(v):
            if v is None: return "—"
            return f"{v*100:+.1f}%"

        def fmt_num(v):
            if v is None: return "—"
            if v >= 1e9: return f"${v/1e9:.1f}Bn"
            if v >= 1e6: return f"${v/1e6:.0f}M"
            return f"${v:.2f}"

        return {
            "symbol":         symbol,
            "name":           name,
            "price":          price,
            "pfmt":           pfmt,
            "eps_ttm":        eps_ttm,
            "eps_fwd":        eps_fwd,
            "rev_ttm":        fmt_num(rev_ttm),
            "rev_growth":     fmt_pct(rev_growth),
            "eps_growth":     fmt_pct(eps_growth),
            "pe_ttm":         round(pe_ttm, 1) if pe_ttm else None,
            "pe_fwd":         round(pe_fwd, 1) if pe_fwd else None,
            "peg":            round(peg, 2) if peg else None,
            "gross_margin":   fmt_pct(gross_margin),
            "profit_margin":  fmt_pct(profit_margin),
            "debt_equity":    round(debt_equity, 2) if debt_equity else None,
            "short_ratio":    round(short_ratio, 1) if short_ratio else None,
            "next_earnings":  next_earnings or "—",
            "days_to_earnings":days_to_earnings,
            "surprise_pct":   surprise_pct,
            "pods_score":     pods_score,
            "pods_label":     pods_label,
            "pods_color":     pods_color,
            "opt_rec":        opt_rec,
            "h_d":            r_tech.get("h_d", 0.5) if r_tech else 0.5,
            "vp":             r_tech.get("vp", 50)    if r_tech else 50,
            "pd_c":           r_tech.get("pd_c", 0)   if r_tech else 0,
        }

    except Exception as e:
        return None

def run_earnings_scanner(limit=None):
    print(f"\n{'='*60}")
    print(f"  EARNINGS SCANNER — {RUN_DATE}")
    print(f"  PODS Score | EPS | Revenue | Options Setup")
    print("="*60)
    tickers = EARNINGS_TICKERS
    if limit: tickers = tickers[:limit]
    results = []
    for symbol, name in tickers:
        try:
            print(f"  → {symbol:8} {name}...")
            r = fetch_earnings_info(symbol, name)
            if r:
                results.append(r)
                days = r["days_to_earnings"]
                days_str = f"em {days}d" if days and 0<days<365 else \
                           "passou" if days and days<=0 else "—"
                print(f"     PODS:{r['pods_score']}/100 "
                      f"{r['pods_label']} | "
                      f"EPS:{r['eps_ttm']} → {r['eps_fwd']} | "
                      f"Earnings:{days_str}")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")

    results.sort(key=lambda x: x["pods_score"], reverse=True)
    ideal = [r for r in results if "IDEAL" in r["pods_label"]]
    bom   = [r for r in results if "BOM"   in r["pods_label"]]
    prox  = [r for r in results
             if r.get("days_to_earnings") and 0<=r["days_to_earnings"]<=30]
    print(f"\n  Total:{len(results)} | PODS Ideal:{len(ideal)} | "
          f"Bom:{len(bom)} | Próximos 30d:{len(prox)}")
    return results

def generate_earnings_html(results):
    if not results: return ""
    ideal = [r for r in results if "IDEAL" in r["pods_label"]]
    bom   = [r for r in results if "BOM"   in r["pods_label"]]
    prox  = [r for r in results
             if r.get("days_to_earnings") and 0<=r["days_to_earnings"]<=30]

    def rows_html(lst):
        rows = ""
        for r in lst:
            pc = r["pods_color"]
            hc = "#4ade80" if r.get("h_d",0.5)>0.62 else \
                 "#fbbf24" if r.get("h_d",0.5)>0.52 else "#f87171"
            vc = "#4ade80" if (r.get("vp",50) or 50)<35 else \
                 "#f43f5e" if (r.get("vp",50) or 50)>70 else "#94a3b8"
            dc = r.get("days_to_earnings")
            day_color = "#4ade80" if dc and dc<=14 else \
                        "#fbbf24" if dc and dc<=30 else "#94a3b8"
            rows += f"""
            <tr>
              <td><strong>{r['symbol']}</strong></td>
              <td style="color:#64748b">{r['name'][:14]}</td>
              <td><strong>{r['pfmt']}</strong></td>
              <td style="background:{pc}22;color:{pc};border-radius:4px;
                  padding:2px 6px;font-size:10px;font-weight:700">
                  {r['pods_score']}</td>
              <td style="color:{pc};font-size:10px">
                  {r['pods_label']}</td>
              <td style="color:{hc}">{r.get('h_d',0.5):.2f}</td>
              <td style="color:{vc}">{r.get('vp',50):.0f}%</td>
              <td style="color:#94a3b8">{r.get('eps_ttm','—')}</td>
              <td style="color:#94a3b8">{r.get('eps_fwd','—')}</td>
              <td style="color:#64748b">{r.get('rev_growth','—')}</td>
              <td style="color:#475569">
                  {r.get('pe_fwd','—')}</td>
              <td style="color:{day_color};font-size:10px">
                  {r['next_earnings']}</td>
              <td style="color:#64748b;font-size:10px">
                  {r.get('opt_rec','—')}</td>
            </tr>"""
        return rows

    header = """<tr>
        <th>Ticker</th><th>Nome</th><th>Preço</th>
        <th>PODS</th><th>Setup</th>
        <th>Hurst</th><th>Vol%</th>
        <th>EPS TTM</th><th>EPS Fwd</th>
        <th>Rev Growth</th><th>P/E Fwd</th>
        <th>Próx Earnings</th><th>Opção</th>
    </tr>"""

    return f"""
    <div id="earnings" class="tab-content section">
      <div class="section-title">
          EARNINGS — PODS SCORE + OPTIONS SETUP
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);
                  gap:8px;margin-bottom:16px">
        <div style="background:#4ade8022;border:1px solid #4ade8044;
                    border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:9px;color:#4ade80">PODS IDEAL</div>
          <div style="font-size:24px;font-weight:900;color:#4ade80">
              {len(ideal)}</div></div>
        <div style="background:#86efac22;border:1px solid #86efac44;
                    border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:9px;color:#86efac">PODS BOM</div>
          <div style="font-size:24px;font-weight:900;color:#86efac">
              {len(bom)}</div></div>
        <div style="background:#fbbf2422;border:1px solid #fbbf2444;
                    border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:9px;color:#fbbf24">PRÓX 30 DIAS</div>
          <div style="font-size:24px;font-weight:900;color:#fbbf24">
              {len(prox)}</div></div>
      </div>

      <div style="color:#64748b;font-size:11px;font-weight:700;
                  margin-bottom:8px">
          🏆 TOP PODS SCORES</div>
      <div class="table-wrap">
        <table>{header}{rows_html(results[:20])}</table>
      </div>

      <div style="color:#64748b;font-size:11px;font-weight:700;
                  margin:16px 0 8px">
          ⏰ PRÓXIMAS EARNINGS (30 dias)</div>
      <div class="table-wrap">
        <table>{header}{rows_html(prox)}</table>
      </div>

      <div style="background:#0a1628;border:1px solid #1e3a5f;
                  border-radius:8px;padding:12px;margin-top:16px;
                  font-size:10px;color:#475569">
        PODS = Pre-Earnings Options Directional Setup
        · Alto PODS + vol comprimida + hurst trending = setup ideal para direcional
        · Usa spreads para limitar custo de vega
      </div>
    </div>"""