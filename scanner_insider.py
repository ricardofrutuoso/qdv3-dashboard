# ============================================================
# SCANNER_INSIDER.PY — SEC EDGAR Form 4 Insider Flow
# Cluster de compras = sinal bullish forte
# Gratuito — SEC EDGAR API pública
# ============================================================

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

from config import RUN_DATE

# User-Agent obrigatório pela SEC
SEC_HEADERS = {
    "User-Agent": "QDV3-Research ricky@qdv3.pt",
    "Accept-Encoding": "gzip, deflate",
    "Host": "efts.sec.gov",
}

# Tickers US para monitorizar insider flow
INSIDER_TICKERS = [
    ("NVDA",  "Nvidia"),
    ("AAPL",  "Apple"),
    ("MSFT",  "Microsoft"),
    ("AMD",   "AMD"),
    ("META",  "Meta"),
    ("AMZN",  "Amazon"),
    ("TSLA",  "Tesla"),
    ("GOOGL", "Alphabet"),
    ("JPM",   "JPMorgan"),
    ("GS",    "Goldman Sachs"),
    ("COIN",  "Coinbase"),
    ("PLTR",  "Palantir"),
    ("MSTR",  "MicroStrategy"),
    ("MELI",  "MercadoLibre"),
    ("SOFI",  "SoFi"),
    ("NU",    "Nubank"),
    ("HOOD",  "Robinhood"),
    ("LLY",   "Eli Lilly"),
    ("AVGO",  "Broadcom"),
    ("V",     "Visa"),
]

# ── FETCH INSIDER FILINGS ────────────────────────────────────
def fetch_insider_filings(ticker, days=30):
    """
    Busca Form 4 via SEC EDGAR full-text search
    Form 4 = insider transactions (obrigatório em 2 dias úteis)
    """
    try:
        start_date = (datetime.today() -
                      timedelta(days=days)).strftime("%Y-%m-%d")
        end_date   = datetime.today().strftime("%Y-%m-%d")

        url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q=%22{ticker}%22"
            f"&dateRange=custom"
            f"&startdt={start_date}"
            f"&enddt={end_date}"
            f"&forms=4"
        )

        headers = {
            "User-Agent": "QDV3-Research ricky@qdv3.pt",
            "Accept-Encoding": "gzip, deflate",
        }

        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            return []

        hits = r.json().get("hits", {}).get("hits", [])
        return hits

    except:
        return []

# ── PARSE INSIDER TRANSACTIONS ───────────────────────────────
def parse_insider_transactions(hits):
    """
    Extrai compras vs vendas dos Form 4
    P = Purchase (compra) | S = Sale (venda) | A = Award
    """
    buys      = 0
    sells     = 0
    awards    = 0
    buy_value = 0.0
    filings   = []

    for hit in hits:
        try:
            src = hit.get("_source", {})

            # Nome do insider
            entity = src.get("entity_name", "Unknown")
            date   = src.get("period_of_report",
                             src.get("file_date", "—"))

            # Tipo de transacção
            # A SEC usa codes: P=Purchase, S=Sale, A=Award, G=Gift
            # Tentamos extrair do display_names ou file_date
            display = str(src.get("display_names", "")).upper()
            form_id = str(src.get("id", ""))

            # Heurística simples baseada nos campos disponíveis
            # Form 4 com "PURCHASE" ou sem "SALE" = buy
            if "PURCHASE" in display or "BOUGHT" in display:
                buys += 1
            elif "SALE" in display or "SOLD" in display or "DISPOSE" in display:
                sells += 1
            else:
                # Default — usa contexto
                awards += 1

            filings.append({
                "entity": entity,
                "date":   str(date)[:10],
                "type":   "BUY" if "PURCHASE" in display else
                          "SELL" if "SALE" in display else "OTHER",
            })

        except:
            continue

    return buys, sells, awards, filings

# ── FETCH VIA COMPANY SEARCH ─────────────────────────────────
def fetch_via_company_facts(ticker, days=30):
    """
    Alternativa mais fiável usando CIK lookup + Form 4
    """
    try:
        # Step 1: Encontra CIK do ticker
        cik_url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q=%22{ticker}%22&forms=4"
            f"&dateRange=custom"
            f"&startdt={(datetime.today()-timedelta(days)).strftime('%Y-%m-%d')}"
            f"&enddt={datetime.today().strftime('%Y-%m-%d')}"
        )
        headers = {"User-Agent": "QDV3-Research ricky@qdv3.pt"}
        r = requests.get(cik_url, headers=headers, timeout=15)

        if r.status_code != 200:
            return 0, 0, 0, []

        data = r.json()
        hits = data.get("hits", {}).get("hits", [])

        if not hits:
            return 0, 0, 0, []

        return parse_insider_transactions(hits)

    except:
        return 0, 0, 0, []

# ── ANALYSE INSIDER ──────────────────────────────────────────
def analyse_insider(ticker, name, days=30):
    """
    Análise completa de insider flow para um ticker
    Classifica cluster de compras vs vendas
    """
    try:
        buys, sells, awards, filings = fetch_via_company_facts(
            ticker, days)

        total = buys + sells
        net   = buys - sells

        # Score insider
        if buys >= 4 and net >= 3:
            signal      = "CLUSTER BUY FORTE"
            action      = "Multiplos insiders a comprar — bullish historico"
            color       = "#4ade80"
        elif buys >= 2 and net >= 2:
            signal      = "CLUSTER BUY"
            action      = "Insiders a acumular — sinal positivo"
            color       = "#86efac"
        elif buys == 1 and sells == 0:
            signal      = "BUY ISOLADO"
            action      = "Um insider comprou — monitoriza"
            color       = "#fbbf24"
        elif sells >= 3 and net <= -3:
            signal      = "CLUSTER SELL"
            action      = "Multiplos insiders a vender — cautela"
            color       = "#f43f5e"
        elif sells >= 1 and buys == 0:
            signal      = "VENDA INSIDER"
            action      = "Insider a vender — pode ser diversificacao"
            color       = "#f87171"
        else:
            signal      = "NEUTRO"
            action      = "Sem actividade significativa"
            color       = "#475569"

        # Nota: vendas podem ser por exercício de opções ou diversificação
        # Apenas cluster de COMPRAS tem valor preditivo consistente
        nota = "Compras = sinal forte | Vendas = menos fiável (pode ser diversif.)"

        return {
            "ticker":  ticker,
            "name":    name,
            "buys":    buys,
            "sells":   sells,
            "awards":  awards,
            "net":     net,
            "total":   total,
            "signal":  signal,
            "action":  action,
            "color":   color,
            "nota":    nota,
            "filings": filings[:5],  # Últimos 5 filings
            "days":    days,
        }

    except:
        return None

# ── RUN INSIDER SCANNER ───────────────────────────────────────
def run_insider_scanner():
    print("\n" + "="*60)
    print(f"  INSIDER FLOW SCANNER — {RUN_DATE}")
    print(f"  SEC EDGAR Form 4 | Cluster Buy = sinal forte")
    print("="*60)

    results = []

    for ticker, name in INSIDER_TICKERS:
        try:
            print(f"  → {ticker:8} {name}...")
            r = analyse_insider(ticker, name)
            if r:
                results.append(r)
                print(f"     Buys:{r['buys']}  Sells:{r['sells']}  "
                      f"Net:{r['net']:+d}  {r['signal']}")
            time.sleep(0.5)  # Respeita rate limit SEC
        except Exception as e:
            print(f"  ⚠️  {ticker} — {e}")

    cluster_buy  = [r for r in results if "CLUSTER BUY" in r["signal"]]
    cluster_sell = [r for r in results if "CLUSTER SELL" in r["signal"]]

    print(f"\n  Cluster Buy: {len(cluster_buy)} | "
          f"Cluster Sell: {len(cluster_sell)} | "
          f"Total: {len(results)}")

    return results

# ── GET INSIDER SIGNAL ────────────────────────────────────────
def get_insider_signal(ticker, name=None):
    """Helper para uso noutros scanners"""
    return analyse_insider(ticker, name or ticker)

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_insider_html(results):
    if not results:
        return "<p style='color:#475569'>Sem dados insider</p>"

    cluster_buy  = [r for r in results if "CLUSTER BUY" in r["signal"]]
    cluster_sell = [r for r in results if "CLUSTER SELL" in r["signal"]]
    neutro       = [r for r in results if r["signal"] == "NEUTRO"]

    rows = ""
    for r in sorted(results, key=lambda x: x["net"], reverse=True):
        c   = r["color"]
        net = r["net"]
        nc  = "#4ade80" if net > 0 else "#f43f5e" if net < 0 else "#94a3b8"

        rows += f"""
        <tr>
            <td><strong>{r['ticker']}</strong></td>
            <td style="color:#64748b">{r['name']}</td>
            <td style="color:#4ade80;font-weight:700">{r['buys']}</td>
            <td style="color:#f43f5e;font-weight:700">{r['sells']}</td>
            <td style="color:{nc};font-weight:700">{net:+d}</td>
            <td><span style="background:{c}22;color:{c};
                padding:2px 8px;border-radius:4px;
                font-size:10px;font-weight:700">
                {r['signal']}</span></td>
            <td style="color:{c};font-size:10px">{r['action']}</td>
            <td style="color:#475569;font-size:9px">
                últimos {r['days']}d</td>
        </tr>"""

    return f"""
    <div id="insider" class="tab-content section">
      <div class="section-title">
          INSIDER FLOW — SEC EDGAR FORM 4
      </div>
      <div style="color:#475569;font-size:9px;margin-bottom:16px">
        Insiders têm de reportar em 2 dias úteis
        · Cluster de COMPRAS = sinal historicamente forte
        · Vendas menos fiáveis (diversificacao, impostos, etc.)
      </div>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);
                  gap:8px;margin-bottom:16px">
        <div style="background:#4ade8022;border:1px solid #4ade8044;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#4ade80;margin-bottom:4px">
              CLUSTER BUY</div>
          <div style="font-size:24px;font-weight:900;color:#4ade80">
              {len(cluster_buy)}</div>
          <div style="font-size:9px;color:#64748b">
              insiders a acumular</div>
        </div>
        <div style="background:#f43f5e22;border:1px solid #f43f5e44;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#f43f5e;margin-bottom:4px">
              CLUSTER SELL</div>
          <div style="font-size:24px;font-weight:900;color:#f43f5e">
              {len(cluster_sell)}</div>
          <div style="font-size:9px;color:#64748b">
              insiders a reduzir</div>
        </div>
        <div style="background:#1e293b;border:1px solid #334155;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#64748b;margin-bottom:4px">
              NEUTRO</div>
          <div style="font-size:24px;font-weight:900;color:#475569">
              {len(neutro)}</div>
          <div style="font-size:9px;color:#475569">sem actividade</div>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <tr>
            <th>Ticker</th><th>Nome</th>
            <th>Compras</th><th>Vendas</th><th>Net</th>
            <th>Sinal</th><th>Acção</th><th>Período</th>
          </tr>
          {rows}
        </table>
      </div>

      <div style="background:#0a1628;border:1px solid #1e3a5f;
                  border-radius:8px;padding:12px;margin-top:16px;
                  font-size:10px;color:#475569">
        Nota: Insiders incluem CEO, CFO, directores e accionistas &gt;10%
        · Compras com dinheiro próprio = maior convicção
        · Exercício de opções não conta como sinal
      </div>
    </div>"""


if __name__ == "__main__":
    results = run_insider_scanner()
    print(f"\nInsider scanner completo: {len(results)} tickers")