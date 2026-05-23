# ============================================================
# SCANNER_COT.PY — CFTC Commitment of Traders
# Commercial Hedgers Z-Score | Smart Money Signal
# Gratuito — sem API key necessária
# ============================================================

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from config import RUN_DATE

# URL do CFTC — Disaggregated COT Report (formato CSV público)
CFTC_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"

# Mapeamento ticker -> código CFTC
from universe import COT_CODES

# ── FETCH COT DATA ────────────────────────────────────────────
def fetch_cot_data():
    """
    Faz download do COT report completo do CFTC
    Publicado às sextas-feiras
    Retorna DataFrame com todos os mercados
    """
    try:
        print("  → Fetching CFTC COT data...")
        r = requests.get(CFTC_URL, timeout=30)
        if r.status_code != 200:
            print(f"  ⚠️  CFTC erro: {r.status_code}")
            return None

        from io import StringIO
        df = pd.read_csv(StringIO(r.text), low_memory=False)
        print(f"  ✓ COT data: {len(df)} registos")
        return df

    except Exception as e:
        print(f"  ⚠️  COT fetch erro: {e}")
        return None

# ── ANALYSE COT TICKER ────────────────────────────────────────
def analyse_cot(cot_df, ticker, name):
    """
    Analisa posicionamento COT para um ticker
    Foca nos Commercial Hedgers (smart money)
    Z-Score do net commercial sobre 52 semanas
    """
    try:
        code = COT_CODES.get(ticker)
        if not code or cot_df is None:
            return None

        # Filtra por código CFTC
        mask = cot_df["CFTC_Contract_Market_Code"].astype(str).str.strip() == str(code)
        df   = cot_df[mask].copy()

        if df.empty:
            return None

        # Ordena por data
        df["Report_Date"] = pd.to_datetime(
            df["As_of_Date_In_Form_YYMMDD"].astype(str),
            format="%y%m%d", errors="coerce"
        )
        df = df.sort_values("Report_Date").tail(104)  # 2 anos

        if len(df) < 10:
            return None

        # Net Positioning
        # Large Specs (especuladores — momentum followers)
        try:
            df["net_large_spec"] = (
                df["NonComm_Positions_Long_All"].astype(float) -
                df["NonComm_Positions_Short_All"].astype(float)
            )
        except:
            df["net_large_spec"] = 0

        # Commercials (hedgers — smart money contrarian)
        try:
            df["net_commercial"] = (
                df["Comm_Positions_Long_All"].astype(float) -
                df["Comm_Positions_Short_All"].astype(float)
            )
        except:
            df["net_commercial"] = 0

        # Z-Score comercial (janela 52 semanas)
        w = min(52, len(df))
        roll_mean = df["net_commercial"].rolling(w).mean()
        roll_std  = df["net_commercial"].rolling(w).std()

        df["commercial_z"] = (
            (df["net_commercial"] - roll_mean) / roll_std
        ).replace([np.inf, -np.inf], np.nan)

        # Z-Score large spec (contrarian)
        roll_mean_s = df["net_large_spec"].rolling(w).mean()
        roll_std_s  = df["net_large_spec"].rolling(w).std()

        df["spec_z"] = (
            (df["net_large_spec"] - roll_mean_s) / roll_std_s
        ).replace([np.inf, -np.inf], np.nan)

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        commercial_z = float(last["commercial_z"]) \
                       if not pd.isna(last["commercial_z"]) else 0.0
        spec_z       = float(last["spec_z"]) \
                       if not pd.isna(last["spec_z"]) else 0.0

        net_comm = float(last["net_commercial"])
        net_spec = float(last["net_large_spec"])

        # Velocidade (mudança semana a semana)
        comm_roc = float(last["net_commercial"] - prev["net_commercial"]) \
                   if len(df) > 1 else 0.0

        # Sinal COT
        # Lógica contrarian:
        # Commercials muito long (Z > +1.5) = sinal BULLISH
        # Commercials muito short (Z < -1.5) = sinal BEARISH
        # Large specs extremamente long = risco de reversão
        if commercial_z >= 2.0:
            cot_signal = "BULLISH FORTE"
            cot_color  = "#4ade80"
            cot_action = "Smart money muito long — setup de compra"
        elif commercial_z >= 1.5:
            cot_signal = "BULLISH"
            cot_color  = "#86efac"
            cot_action = "Comerciais a acumular long"
        elif commercial_z <= -2.0:
            cot_signal = "BEARISH FORTE"
            cot_color  = "#f43f5e"
            cot_action = "Smart money muito short — evitar longs"
        elif commercial_z <= -1.5:
            cot_signal = "BEARISH"
            cot_color  = "#f87171"
            cot_action = "Comerciais a acumular short"
        else:
            cot_signal = "NEUTRO"
            cot_color  = "#94a3b8"
            cot_action = "Sem extremos — aguardar"

        # Divergencia com large specs (sinal contrarian forte)
        divergence = ""
        if commercial_z >= 1.5 and spec_z <= -1.0:
            divergence = "MAXIMA BULLISH — comerciais long, specs short"
        elif commercial_z <= -1.5 and spec_z >= 1.0:
            divergence = "MAXIMA BEARISH — comerciais short, specs long"

        return {
            "ticker":        ticker,
            "name":          name,
            "commercial_z":  round(commercial_z, 2),
            "spec_z":        round(spec_z, 2),
            "net_comm":      int(net_comm),
            "net_spec":      int(net_spec),
            "comm_roc":      int(comm_roc),
            "cot_signal":    cot_signal,
            "cot_color":     cot_color,
            "cot_action":    cot_action,
            "divergence":    divergence,
            "date":          str(last["Report_Date"])[:10],
        }

    except Exception as e:
        return None

# ── RUN COT SCANNER ──────────────────────────────────────────
def run_cot_scanner():
    print("\n" + "="*60)
    print(f"  COT SCANNER — {RUN_DATE}")
    print(f"  CFTC Commitment of Traders | Smart Money")
    print("="*60)

    cot_df  = fetch_cot_data()
    results = []

    if cot_df is None:
        print("  ⚠️  Sem dados COT disponíveis")
        return results

    for ticker, code in COT_CODES.items():
        try:
            name = ticker.replace("=X","").replace("=F","")
            r    = analyse_cot(cot_df, ticker, name)
            if r:
                results.append(r)
                sig = r["cot_signal"]
                z   = r["commercial_z"]
                div = " | DIV!" if r["divergence"] else ""
                print(f"  {'↑' if 'BULL' in sig else '↓' if 'BEAR' in sig else '–'} "
                      f"{ticker:12} Z:{z:+.2f}  {sig}{div}")
        except:
            continue

    bull = sum(1 for r in results if "BULL" in r["cot_signal"])
    bear = sum(1 for r in results if "BEAR" in r["cot_signal"])
    print(f"\n  Bullish: {bull} | Bearish: {bear} | "
          f"Total: {len(results)}")

    return results

# ── GET COT FOR TICKER ────────────────────────────────────────
def get_cot_signal(ticker, cot_df=None):
    """
    Helper — retorna sinal COT para um ticker específico
    Usado pelos outros scanners para enriquecer análise
    """
    if cot_df is None:
        return None
    name = ticker.replace("=X","").replace("=F","")
    return analyse_cot(cot_df, ticker, name)

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_cot_html(results):
    if not results:
        return "<p style='color:#475569'>Sem dados COT</p>"

    bull_r = [r for r in results if "BULL" in r["cot_signal"]]
    bear_r = [r for r in results if "BEAR" in r["cot_signal"]]
    div_r  = [r for r in results if r["divergence"]]

    rows = ""
    for r in sorted(results,
                    key=lambda x: abs(x["commercial_z"]),
                    reverse=True):
        zc = r["commercial_z"]
        zs = r["spec_z"]
        c  = r["cot_color"]

        zc_color = "#4ade80" if zc > 1.5 else \
                   "#f43f5e" if zc < -1.5 else "#94a3b8"
        zs_color = "#f43f5e" if zs > 1.5 else \
                   "#4ade80" if zs < -1.5 else "#94a3b8"

        div_badge = (
            f"<span style='background:#6366f122;color:#6366f1;"
            f"font-size:9px;padding:2px 6px;border-radius:4px;"
            f"margin-left:6px'>DIV!</span>"
        ) if r["divergence"] else ""

        rows += f"""
        <tr>
            <td><strong>{r['ticker']}</strong></td>
            <td style="color:#64748b">{r['name']}</td>
            <td><span style="background:{c}22;color:{c};
                padding:2px 8px;border-radius:4px;
                font-size:11px;font-weight:700">
                {r['cot_signal']}</span>{div_badge}</td>
            <td style="color:{zc_color};font-weight:700">
                {zc:+.2f}</td>
            <td style="color:{zs_color}">{zs:+.2f}</td>
            <td style="color:#94a3b8;font-size:11px">
                {r['cot_action']}</td>
            <td style="color:#475569;font-size:10px">
                {r['date']}</td>
        </tr>"""

    html = f"""
    <div id="cot" class="tab-content section">
      <div class="section-title">
          COT — COMMITMENT OF TRADERS (CFTC)
      </div>
      <div style="color:#475569;font-size:9px;margin-bottom:16px">
        Fonte: CFTC.gov — publicado sextas-feiras
        · Commercial Hedgers = smart money (contrarian)
        · Z-Score sobre 52 semanas
        · Bullish forte quando Z comercial &gt; +1.5
      </div>

      <div style="display:grid;
                  grid-template-columns:repeat(3,1fr);
                  gap:8px;margin-bottom:20px">
        <div style="background:#4ade8022;border:1px solid #4ade8044;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#4ade80;margin-bottom:4px">
              BULLISH</div>
          <div style="font-size:28px;font-weight:900;color:#4ade80">
              {len(bull_r)}</div>
          <div style="font-size:9px;color:#64748b">smart money long</div>
        </div>
        <div style="background:#f43f5e22;border:1px solid #f43f5e44;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#f43f5e;margin-bottom:4px">
              BEARISH</div>
          <div style="font-size:28px;font-weight:900;color:#f43f5e">
              {len(bear_r)}</div>
          <div style="font-size:9px;color:#64748b">smart money short</div>
        </div>
        <div style="background:#6366f122;border:1px solid #6366f144;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#6366f1;margin-bottom:4px">
              DIVERGENCIAS</div>
          <div style="font-size:28px;font-weight:900;color:#6366f1">
              {len(div_r)}</div>
          <div style="font-size:9px;color:#64748b">max. contrarian</div>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <tr>
            <th>Ticker</th><th>Nome</th><th>Sinal COT</th>
            <th>Z Comercial</th><th>Z Specs</th>
            <th>Acção</th><th>Data</th>
          </tr>
          {rows}
        </table>
      </div>

      <div style="background:#0a1628;border:1px solid #1e3a5f;
                  border-radius:8px;padding:14px;margin-top:16px;
                  font-size:10px">
        <div style="color:#94a3b8;font-weight:700;
                    margin-bottom:8px">COMO LER O COT:</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;
                    gap:8px;color:#64748b">
          <div>
              <span style="color:#4ade80">Z Comercial &gt; +1.5</span>
              = hedgers acumulando long = bullish contrarian
          </div>
          <div>
              <span style="color:#f43f5e">Z Comercial &lt; -1.5</span>
              = hedgers acumulando short = bearish contrarian
          </div>
          <div>
              <span style="color:#6366f1">DIVERGENCIA</span>
              = comerciais e specs em lados opostos = sinal mais forte
          </div>
          <div>
              Comerciais = produtores/hedgers — conhecem o mercado real
              · Specs = fundos de CTA — seguem momentum
          </div>
        </div>
      </div>
    </div>"""

    return html


if __name__ == "__main__":
    results = run_cot_scanner()
    print(f"\nCOT scanner completo: {len(results)} mercados")