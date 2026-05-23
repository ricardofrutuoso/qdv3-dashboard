# ============================================================
# SCANNER_OPTIONS_ANALYTICS.PY — GEX + Max Pain + IV Skew
# Gamma Exposure | Max Pain | IV Surface
# Gratuito via yfinance
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from config import RUN_DATE

# Tickers com liquidez de opções suficiente
OPTIONS_TICKERS = [
    ("SPY",  "S&P500"),
    ("QQQ",  "Nasdaq"),
    ("IWM",  "Russell"),
    ("NVDA", "Nvidia"),
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("TSLA", "Tesla"),
    ("AMD",  "AMD"),
    ("META", "Meta"),
    ("AMZN", "Amazon"),
    ("GLD",  "Gold ETF"),
    ("TLT",  "20Y Bond"),
    ("MSTR", "MicroStrategy"),
    ("COIN", "Coinbase"),
    ("PLTR", "Palantir"),
]

# ── CALC MAX PAIN ─────────────────────────────────────────────
def calc_max_pain(chain_calls, chain_puts):
    """
    Max Pain = preço onde market makers minimizam perdas totais
    Importante: preço tende a gravitar para max pain perto da expiração
    """
    try:
        strikes = sorted(set(
            list(chain_calls["strike"].values) +
            list(chain_puts["strike"].values)
        ))

        pain = {}
        for s in strikes:
            # Dor dos calls (MMs short calls)
            calls_itm = chain_calls[chain_calls["strike"] < s]
            call_pain = float(
                ((s - calls_itm["strike"]) *
                 calls_itm["openInterest"]).sum()
            )
            # Dor dos puts (MMs short puts)
            puts_itm = chain_puts[chain_puts["strike"] > s]
            put_pain = float(
                ((puts_itm["strike"] - s) *
                 puts_itm["openInterest"]).sum()
            )
            pain[s] = call_pain + put_pain

        max_pain_strike = min(pain, key=pain.get)
        return max_pain_strike

    except:
        return None

# ── CALC GEX ─────────────────────────────────────────────────
def calc_gex(chain_calls, chain_puts, price):
    """
    Gamma Exposure = soma do gamma ponderado pelo OI e notional
    GEX positivo  → MMs short gamma → vendem rallies, compram quedas
                  → volatilidade comprimida, reversion to mean
    GEX negativo  → MMs long gamma  → amplificam movimentos
                  → volatilidade expansiva, breakouts mais violentos
    """
    try:
        spot = float(price)

        # Gamma exposure calls (MMs short calls = short gamma)
        calls_gex = (
            chain_calls["gamma"].astype(float) *
            chain_calls["openInterest"].astype(float) *
            100 *
            (spot ** 2) * 0.01
        ).sum()

        # Gamma exposure puts (MMs short puts = long gamma)
        puts_gex = (
            chain_puts["gamma"].astype(float) *
            chain_puts["openInterest"].astype(float) *
            100 *
            (spot ** 2) * 0.01 * -1
        ).sum()

        total_gex = calls_gex + puts_gex

        # Normaliza em biliões
        gex_bn = round(total_gex / 1e9, 3)

        # Zero Gamma Level — preço onde GEX = 0
        # Abaixo deste nível, MMs amplificam movimentos
        zgl = None
        try:
            all_strikes = pd.concat([
                chain_calls[["strike","gamma","openInterest"]].assign(type="call"),
                chain_puts[["strike","gamma","openInterest"]].assign(type="put"),
            ])
            all_strikes = all_strikes.groupby("strike").apply(
                lambda x: (
                    x[x["type"]=="call"]["gamma"].sum() * spot**2 * 0.01 *
                    x[x["type"]=="call"]["openInterest"].sum() -
                    x[x["type"]=="put"]["gamma"].sum() * spot**2 * 0.01 *
                    x[x["type"]=="put"]["openInterest"].sum()
                )
            ).reset_index()
            all_strikes.columns = ["strike","net_gex"]
            pos = all_strikes[all_strikes["net_gex"] > 0]
            neg = all_strikes[all_strikes["net_gex"] < 0]
            if not pos.empty and not neg.empty:
                zgl = float(pos["strike"].min() if gex_bn > 0 else neg["strike"].max())
        except:
            pass

        return gex_bn, zgl

    except:
        return None, None

# ── CALC IV SKEW ─────────────────────────────────────────────
def calc_iv_skew(chain_calls, chain_puts, price):
    """
    IV Skew = puts OTM vs calls OTM
    Skew positivo = puts mais caras = crash premium elevado
    Skew negativo = calls mais caras = rally premium (raro)
    """
    try:
        spot = float(price)
        otm_range = 0.05  # 5% OTM

        # Puts OTM (strikes abaixo do spot)
        puts_otm = chain_puts[
            (chain_puts["strike"] >= spot * (1 - otm_range * 2)) &
            (chain_puts["strike"] <= spot * (1 - otm_range * 0.5))
        ]

        # Calls OTM (strikes acima do spot)
        calls_otm = chain_calls[
            (chain_calls["strike"] >= spot * (1 + otm_range * 0.5)) &
            (chain_calls["strike"] <= spot * (1 + otm_range * 2))
        ]

        if puts_otm.empty or calls_otm.empty:
            return None

        iv_put  = float(puts_otm["impliedVolatility"].mean())
        iv_call = float(calls_otm["impliedVolatility"].mean())

        skew = round((iv_put - iv_call) * 100, 2)  # em %

        if skew > 10:
            label = "CRASH PREMIUM ALTO — mercado com medo"
        elif skew > 5:
            label = "Skew elevado — cautela"
        elif skew < -5:
            label = "CALL SKEW — bullish extremo (raro)"
        else:
            label = "Skew normal"

        return {
            "skew":     skew,
            "iv_put":   round(iv_put * 100, 1),
            "iv_call":  round(iv_call * 100, 1),
            "label":    label,
        }
    except:
        return None

# ── ANALYSE OPTIONS ───────────────────────────────────────────
def analyse_options_analytics(symbol, name):
    """
    Análise completa de opções para um ticker
    GEX + Max Pain + IV Skew
    """
    try:
        t    = yf.Ticker(symbol)
        info = t.info or {}

        price = info.get("regularMarketPrice") or \
                info.get("currentPrice") or \
                info.get("previousClose")
        if not price:
            return None

        exps = t.options
        if not exps:
            return None

        # Usa as primeiras 2 expirações (mais liquidez)
        results_by_exp = []

        for exp in exps[:3]:
            try:
                chain  = t.option_chain(exp)
                calls  = chain.calls
                puts   = chain.puts

                if calls.empty or puts.empty:
                    continue

                # Filtra strikes sem OI
                calls = calls[calls["openInterest"] > 0].copy()
                puts  = puts[puts["openInterest"] > 0].copy()

                if calls.empty or puts.empty:
                    continue

                # Max Pain
                max_pain = calc_max_pain(calls, puts)

                # GEX
                gex, zgl = calc_gex(calls, puts, price)

                # IV Skew
                iv_skew = calc_iv_skew(calls, puts, price)

                # PCR (Put/Call Ratio por OI)
                total_call_oi = float(calls["openInterest"].sum())
                total_put_oi  = float(puts["openInterest"].sum())
                pcr = round(total_put_oi / total_call_oi, 3) \
                      if total_call_oi > 0 else None

                # Put/Call por volume
                call_vol = float(calls["volume"].sum()) \
                           if "volume" in calls.columns else 0
                put_vol  = float(puts["volume"].sum()) \
                           if "volume" in puts.columns else 0
                pcr_vol  = round(put_vol / call_vol, 3) \
                           if call_vol > 0 else None

                # Max Pain vs Spot
                mp_pct = round((max_pain - price) / price * 100, 2) \
                         if max_pain else None

                results_by_exp.append({
                    "exp":      exp,
                    "max_pain": max_pain,
                    "mp_pct":   mp_pct,
                    "gex":      gex,
                    "zgl":      zgl,
                    "iv_skew":  iv_skew,
                    "pcr":      pcr,
                    "pcr_vol":  pcr_vol,
                })

            except:
                continue

        if not results_by_exp:
            return None

        # Resumo — usa 1ª expiração como referência
        first = results_by_exp[0]
        gex   = first["gex"]

        # GEX signal
        if gex is not None:
            if gex > 1.0:
                gex_signal = "GEX POSITIVO — vol comprimida"
                gex_color  = "#4ade80"
            elif gex > 0:
                gex_signal = "GEX levemente positivo"
                gex_color  = "#86efac"
            elif gex > -1.0:
                gex_signal = "GEX levemente negativo — cuidado"
                gex_color  = "#fbbf24"
            else:
                gex_signal = "GEX NEGATIVO — vol amplificada"
                gex_color  = "#f43f5e"
        else:
            gex_signal = "Sem dados GEX"
            gex_color  = "#94a3b8"

        pfmt = f"${price:.2f}" if price >= 1 else f"${price:.4f}"

        return {
            "symbol":     symbol,
            "name":       name,
            "price":      price,
            "pfmt":       pfmt,
            "expirations":results_by_exp,
            "gex":        gex,
            "gex_signal": gex_signal,
            "gex_color":  gex_color,
            "zgl":        first.get("zgl"),
            "max_pain":   first.get("max_pain"),
            "mp_pct":     first.get("mp_pct"),
            "iv_skew":    first.get("iv_skew"),
            "pcr":        first.get("pcr"),
            "pcr_vol":    first.get("pcr_vol"),
            "exp":        first.get("exp"),
        }

    except:
        return None

# ── RUN OPTIONS ANALYTICS ─────────────────────────────────────
def run_options_analytics():
    print("\n" + "="*60)
    print(f"  OPTIONS ANALYTICS — {RUN_DATE}")
    print(f"  GEX + Max Pain + IV Skew | via yfinance")
    print("="*60)

    results = []
    for symbol, name in OPTIONS_TICKERS:
        try:
            print(f"  → {symbol:8} {name}...")
            r = analyse_options_analytics(symbol, name)
            if r:
                results.append(r)
                gex = r["gex"]
                mp  = r["max_pain"]
                pcr = r["pcr"]
                print(f"     GEX:{gex:+.3f}Bn  "
                      f"MaxPain:{mp:.0f}  "
                      f"PCR:{pcr:.2f}  "
                      f"{r['gex_signal']}")
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")

    print(f"\n  {len(results)} tickers analisados")
    return results

# ── GET OPTIONS FOR TICKER ────────────────────────────────────
def get_options_signal(symbol):
    """Helper para usar noutros scanners"""
    return analyse_options_analytics(symbol, symbol)

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_options_analytics_html(results):
    if not results:
        return "<p style='color:#475569'>Sem dados de opções</p>"

    pos_gex = [r for r in results if r["gex"] and r["gex"] > 0]
    neg_gex = [r for r in results if r["gex"] and r["gex"] < 0]

    rows = ""
    for r in sorted(results,
                    key=lambda x: abs(x["gex"] or 0),
                    reverse=True):
        gex  = r["gex"]
        gc   = r["gex_color"]
        mp   = r["max_pain"]
        mpp  = r["mp_pct"]
        pcr  = r["pcr"]
        skew = r.get("iv_skew") or {}
        zgl  = r["zgl"]

        mp_color = "#4ade80" if mpp and mpp > 0 else "#f43f5e"
        pcr_color = "#4ade80" if pcr and pcr > 1.0 else \
                    "#f43f5e" if pcr and pcr < 0.7 else "#94a3b8"

        skew_val   = skew.get("skew", 0) if skew else 0
        skew_label = skew.get("label","—") if skew else "—"
        skew_color = "#f43f5e" if skew_val > 10 else \
                     "#fbbf24" if skew_val > 5  else \
                     "#4ade80" if skew_val < -5  else "#94a3b8"

        rows += f"""
        <tr>
            <td><strong>{r['symbol']}</strong></td>
            <td style="color:#64748b">{r['name']}</td>
            <td><strong>{r['pfmt']}</strong></td>
            <td style="color:{gc};font-weight:700">
                {f'{gex:+.3f}Bn' if gex is not None else '—'}</td>
            <td style="color:{gc};font-size:10px">
                {r['gex_signal']}</td>
            <td style="color:#94a3b8">
                {f'${zgl:.0f}' if zgl else '—'}</td>
            <td style="color:#94a3b8">
                {f'${mp:.0f}' if mp else '—'}</td>
            <td style="color:{mp_color}">
                {f'{mpp:+.1f}%' if mpp is not None else '—'}</td>
            <td style="color:{pcr_color};font-weight:700">
                {f'{pcr:.2f}' if pcr else '—'}</td>
            <td style="color:{skew_color};font-size:10px">
                {f'{skew_val:+.1f}%' if skew_val else '—'}</td>
            <td style="color:#475569;font-size:10px">{r['exp']}</td>
        </tr>"""

    return f"""
    <div id="opt_analytics" class="tab-content section">
      <div class="section-title">
          OPTIONS ANALYTICS — GEX + MAX PAIN + IV SKEW
      </div>
      <div style="color:#475569;font-size:9px;margin-bottom:16px">
        GEX = Gamma Exposure dos market makers
        · GEX+ = vol comprimida · GEX- = vol amplificada
        · Max Pain = gravidade das opções perto da expiração
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;
                  gap:8px;margin-bottom:16px">
        <div style="background:#4ade8022;border:1px solid #4ade8044;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#4ade80;margin-bottom:4px">
              GEX POSITIVO</div>
          <div style="font-size:24px;font-weight:900;color:#4ade80">
              {len(pos_gex)}</div>
          <div style="font-size:9px;color:#64748b">vol comprimida</div>
        </div>
        <div style="background:#f43f5e22;border:1px solid #f43f5e44;
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:10px;color:#f43f5e;margin-bottom:4px">
              GEX NEGATIVO</div>
          <div style="font-size:24px;font-weight:900;color:#f43f5e">
              {len(neg_gex)}</div>
          <div style="font-size:9px;color:#64748b">vol amplificada</div>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <tr>
            <th>Ticker</th><th>Nome</th><th>Preço</th>
            <th>GEX</th><th>GEX Sinal</th><th>Zero Gamma</th>
            <th>Max Pain</th><th>MP vs Spot</th>
            <th>PCR OI</th><th>IV Skew</th><th>Exp</th>
          </tr>
          {rows}
        </table>
      </div>

      <div style="background:#0a1628;border:1px solid #1e3a5f;
                  border-radius:8px;padding:14px;margin-top:16px;
                  font-size:10px">
        <div style="color:#94a3b8;font-weight:700;
                    margin-bottom:8px">COMO LER:</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;
                    gap:8px;color:#64748b">
          <div><span style="color:#4ade80">GEX+</span>
              = dealers vendem rallies e compram quedas
              = range trading, breakouts difíceis</div>
          <div><span style="color:#f43f5e">GEX-</span>
              = dealers amplificam movimentos
              = breakouts mais violentos, mais vol</div>
          <div><span style="color:#94a3b8">Zero Gamma</span>
              = nível abaixo do qual GEX inverte para negativo</div>
          <div><span style="color:#fbbf24">IV Skew &gt; 10%</span>
              = crash premium alto = mercado com medo de queda</div>
        </div>
      </div>
    </div>"""


if __name__ == "__main__":
    results = run_options_analytics()
    print(f"\nOptions analytics completo: {len(results)} tickers")