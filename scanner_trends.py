# ============================================================
# SCANNER_TRENDS.PY — Google Trends Retail Sentiment
# FOMO detector | Contrarian signal
# Gratuito via pytrends (sem API key)
# pip install pytrends
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime
import warnings
import time
warnings.filterwarnings("ignore")

try:
    from pytrends.request import TrendReq
    PYTRENDS_OK = True
except ImportError:
    PYTRENDS_OK = False
    print("  ⚠️  pytrends não instalado. Executa: pip install pytrends")

from config import RUN_DATE

# Tickers para monitorizar interesse retail
TRENDS_TICKERS = [
    # US Mega Cap
    ("NVDA",    "NVIDIA stock"),
    ("AAPL",    "Apple stock"),
    ("TSLA",    "Tesla stock"),
    ("AMD",     "AMD stock"),
    ("META",    "META stock"),
    ("AMZN",    "Amazon stock"),
    ("MSTR",    "MicroStrategy stock"),
    ("PLTR",    "Palantir stock"),
    ("COIN",    "Coinbase stock"),
    ("HOOD",    "Robinhood stock"),
    # Crypto
    ("BTC-USD", "Bitcoin"),
    ("ETH-USD", "Ethereum"),
    ("SOL-USD", "Solana"),
    ("DOGE-USD","Dogecoin"),
    # Portugal/Iberia
    ("BCP.LS",  "BCP bolsa"),
    ("GALP.LS", "Galp bolsa"),
    ("EDP.LS",  "EDP bolsa"),
    ("SAN.MC",  "Santander bolsa"),
    ("BBVA.MC", "BBVA bolsa"),
    # EM
    ("PDD",     "PDD Holdings stock"),
    ("BABA",    "Alibaba stock"),
    ("NU",      "Nubank stock"),
]

# ── FETCH TRENDS ─────────────────────────────────────────────
def fetch_trends_batch(keywords, timeframe="today 3-m",
                        geo="", retries=3):
    """
    Busca interesse de pesquisa para um batch de keywords
    Máx 5 por chamada (limite do Google Trends)
    """
    if not PYTRENDS_OK:
        return None
    for attempt in range(retries):
        try:
            pytrends = TrendReq(hl="en-US", tz=0,
                                timeout=(10, 25))
            pytrends.build_payload(
                keywords[:5],
                timeframe=timeframe,
                geo=geo
            )
            df = pytrends.interest_over_time()
            if not df.empty:
                return df
            time.sleep(2)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    return None

# ── ANALYSE TRENDS TICKER ────────────────────────────────────
def analyse_trends(ticker, keyword, df_trends):
    """
    Analisa interesse de pesquisa de um ticker
    Z-Score do interesse actual vs histórico 3 meses
    """
    try:
        if df_trends is None or keyword not in df_trends.columns:
            return None

        series  = df_trends[keyword].values.astype(float)
        if len(series) < 4:
            return None

        current = float(series[-1])
        avg     = float(series.mean())
        std     = float(series.std())

        if std == 0:
            return None

        z = round((current - avg) / std, 2)

        # Peak recente (últimas 4 semanas)
        peak_recent = float(series[-4:].max())
        pct_from_peak = round((current - peak_recent) /
                              peak_recent * 100, 1) \
                        if peak_recent > 0 else 0

        # Trend da tendência (últimas 4 vs 4 anteriores)
        if len(series) >= 8:
            recent_avg  = float(series[-4:].mean())
            earlier_avg = float(series[-8:-4].mean())
            momentum = round((recent_avg - earlier_avg) /
                             max(earlier_avg, 1) * 100, 1)
        else:
            momentum = 0.0

        # Sinal contrarian
        # FOMO extremo (Z > 2) = risco de topo = bearish contrarian
        # Esquecimento (Z < -1.5) = ninguém fala = bullish contrarian
        if z >= 2.5:
            signal = "FOMO EXTREMO"
            action = "Contrarian BEARISH — topo de hype"
            color  = "#f43f5e"
        elif z >= 1.5:
            signal = "FOMO ELEVADO"
            action = "Cuidado — retail a entrar em massa"
            color  = "#f87171"
        elif z >= 0.5:
            signal = "INTERESSE CRESCENTE"
            action = "Monitoriza — momentum retail"
            color  = "#fbbf24"
        elif z <= -2.0:
            signal = "ESQUECIDO"
            action = "Contrarian BULLISH — ninguém olha"
            color  = "#4ade80"
        elif z <= -1.0:
            signal = "POUCO INTERESSE"
            action = "Potencial contrarian — quiet accumulation"
            color  = "#86efac"
        else:
            signal = "NEUTRO"
            action = "Interesse normal"
            color  = "#94a3b8"

        return {
            "ticker":         ticker,
            "keyword":        keyword,
            "interest":       int(current),
            "z_score":        z,
            "momentum":       momentum,
            "pct_from_peak":  pct_from_peak,
            "signal":         signal,
            "action":         action,
            "color":          color,
            "history":        list(series[-12:]),  # últimas 12 semanas
        }

    except:
        return None

# ── RUN TRENDS SCANNER ───────────────────────────────────────
def run_trends_scanner():
    print("\n" + "="*60)
    print(f"  GOOGLE TRENDS SCANNER — {RUN_DATE}")
    print(f"  Retail Sentiment | FOMO Detector | Contrarian")
    print("="*60)

    if not PYTRENDS_OK:
        print("  ⚠️  pytrends não disponível — instala: pip install pytrends")
        return []

    results = []

    # Processa em batches de 5
    for i in range(0, len(TRENDS_TICKERS), 5):
        batch   = TRENDS_TICKERS[i:i+5]
        tickers = [t[0] for t in batch]
        keywords= [t[1] for t in batch]

        print(f"  → Batch {i//5 + 1}: {', '.join(tickers)}")

        df_trends = fetch_trends_batch(keywords)

        for ticker, keyword in batch:
            try:
                r = analyse_trends(ticker, keyword, df_trends)
                if r:
                    results.append(r)
                    z   = r["z_score"]
                    sig = r["signal"]
                    print(f"     {ticker:12} Z:{z:+.2f}  {sig}")
            except:
                continue

        # Pausa entre batches para respeitar rate limits
        if i + 5 < len(TRENDS_TICKERS):
            time.sleep(3)

    fomo  = [r for r in results if "FOMO" in r["signal"]]
    esquec= [r for r in results if "ESQUEC" in r["signal"]]

    print(f"\n  FOMO: {len(fomo)} | Esquecidos: {len(esquec)} | "
          f"Total: {len(results)}")

    return results

# ── GET TRENDS SIGNAL ─────────────────────────────────────────
def get_trends_signal(ticker, keyword=None):
    """Helper rápido para um ticker"""
    if not PYTRENDS_OK:
        return None
    kw = keyword or f"{ticker} stock"
    df = fetch_trends_batch([kw])
    return analyse_trends(ticker, kw, df)

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_trends_html(results):
    if not results:
        return "<p style='color:#475569'>Sem dados Google Trends</p>"

    fomo  = [r for r in results if "FOMO" in r["signal"]]
    bullish_ct = [r for r in results
                  if "ESQUEC" in r["signal"] or "POUCO" in r["signal"]]

    rows = ""
    for r in sorted(results, key=lambda x: x["z_score"], reverse=True):
        z   = r["z_score"]
        c   = r["color"]
        m   = r["momentum"]
        mc  = "#4ade80" if m > 5 else "#f43f5e" if m < -5 else "#94a3b8"

        # Mini sparkline (texto)
        h      = r["history"]
        bar_max= max(h) if h else 1
        bars   = ""
        for v in h:
            ht = max(int(v/bar_max*10), 1)
            bars += f"<span style='display:inline-block;width:4px;" \
                    f"height:{ht}px;background:{c};margin-right:1px;" \
                    f"vertical-align:bottom'></span>"

        rows += f"""
        <tr>
            <td><strong>{r['ticker']}</strong></td>
            <td style="color:#64748b;font-size:10px">{r['keyword']}</td>
            <td style="color:{c};font-weight:700">{z:+.2f}</td>
            <td style="color:{c};font-size:11px">{r['signal']}</td>
            <td style="color:{mc}">{m:+.1f}%</td>
            <td style="color:#94a3b8">{r['interest']}/100</td>
            <td>{bars}</td>
            <td style="color:{c};font-size:10px">{r['action']}</td>
        </tr>"""

    return f"""
    <div id="trends" class="tab-content section">
      <div class="section-title">
          GOOGLE TRENDS — RETAIL SENTIMENT
      </div>
      <div style="color:#475569;font-size:9px;margin-bottom:16px">
        Interesse de pesquisa retail · Z-Score 3 meses
        · FOMO extremo = contrarian bearish
        · Esquecido = contrarian bullish
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;
                  gap:8px;margin-bottom:16px">
        <div style="background:#f43f5e22;border:1px solid #f43f5e44;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#f43f5e;margin-bottom:4px">
              FOMO</div>
          <div style="font-size:24px;font-weight:900;color:#f43f5e">
              {len(fomo)}</div>
          <div style="font-size:9px;color:#64748b">
              retail em modo euforia</div>
        </div>
        <div style="background:#4ade8022;border:1px solid #4ade8044;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#4ade80;margin-bottom:4px">
              ESQUECIDOS</div>
          <div style="font-size:24px;font-weight:900;color:#4ade80">
              {len(bullish_ct)}</div>
          <div style="font-size:9px;color:#64748b">
              oportunidade contrarian</div>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <tr>
            <th>Ticker</th><th>Keyword</th>
            <th>Z-Score</th><th>Sinal</th>
            <th>Momentum</th><th>Interesse</th>
            <th>12 Semanas</th><th>Acção</th>
          </tr>
          {rows}
        </table>
      </div>
    </div>"""


if __name__ == "__main__":
    results = run_trends_scanner()
    print(f"\nTrends scanner completo: {len(results)} tickers")