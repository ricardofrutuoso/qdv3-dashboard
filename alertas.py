# ============================================================
# ALERTAS.PY — Sistema de Alertas QDV3
# Telegram | Portfolio Monitor | Price Alerts | Risk Alerts
# ============================================================

import requests
import yfinance as yf
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from config import (CAPITAL, PORTFOLIO, CLOSED_TRADES,
                    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, RUN_DATE)

# ── TELEGRAM ─────────────────────────────────────────────────
def telegram_send(msg):
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       msg,
            "parse_mode": "HTML",
        }
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"  ⚠️  Telegram erro: {e}")
        return False

def telegram_send_html(title, body):
    msg = f"<b>🤖 QDV3 — {title}</b>\n\n{body}"
    return telegram_send(msg)

# ── FETCH PRICE ───────────────────────────────────────────────
def get_current_price(ticker):
    try:
        t = yf.Ticker(ticker)
        data = t.history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        info = t.info
        return (info.get("regularMarketPrice") or
                info.get("currentPrice") or
                info.get("previousClose"))
    except:
        return None

# ── PORTFOLIO P&L ─────────────────────────────────────────────
def calc_portfolio_pnl():
    positions = []
    total_pnl  = 0.0
    total_invested = 0.0

    for pos in PORTFOLIO:
        try:
            price = get_current_price(pos["ticker"])
            if price is None:
                continue
            entry = pos["entry"]
            qty   = pos["qty"]
            pnl   = (price - entry) * qty
            pnl_pct = (price - entry) / entry * 100
            invested  = entry * qty
            total_pnl      += pnl
            total_invested  += invested
            positions.append({
                **pos,
                "current":  round(price, 4),
                "pnl":      round(pnl, 2),
                "pnl_pct":  round(pnl_pct, 2),
                "invested": round(invested, 2),
            })
        except:
            continue

    total_pnl_pct = (total_pnl / total_invested * 100
                     if total_invested > 0 else 0.0)
    return positions, round(total_pnl, 2), round(total_pnl_pct, 2)

# ── CLOSED TRADES P&L ────────────────────────────────────────
def calc_closed_pnl():
    total = 0.0
    trades_detail = []
    for t in CLOSED_TRADES:
        pnl = (t["exit"] - t["entry"]) * t["qty"]
        total += pnl
        trades_detail.append({**t, "pnl": round(pnl, 2)})
    return round(total, 2), trades_detail

# ── PORTFOLIO ALERT ───────────────────────────────────────────
def portfolio_alert(send_telegram=True):
    positions, total_pnl, total_pnl_pct = calc_portfolio_pnl()
    closed_pnl, closed_trades           = calc_closed_pnl()
    global_pnl = total_pnl + closed_pnl

    print(f"\n{'='*60}")
    print(f"  PORTFOLIO MONITOR — {RUN_DATE}")
    print("="*60)

    lines_telegram = []
    for p in positions:
        pnl_icon = "▲" if p["pnl"] >= 0 else "▼"
        pnl_color= "🟢" if p["pnl"] >= 0 else "🔴"
        print(f"  {pnl_color} {p['ticker']:10} {p['name'][:16]}")
        print(f"     Entry: {p['entry']:.4f} → "
              f"Current: {p['current']:.4f}")
        print(f"     P&L: {p['pnl_pct']:+.2f}% "
              f"({pnl_icon}{abs(p['pnl']):.2f} {p['currency']})")

        lines_telegram.append(
            f"{pnl_color} <b>{p['ticker']}</b> {p['name']}\n"
            f"   Entry: {p['entry']:.4f} → Now: {p['current']:.4f}\n"
            f"   P&L: {p['pnl_pct']:+.2f}% ({pnl_icon}{abs(p['pnl']):.2f} {p['currency']})"
        )

    icon = "🟢" if total_pnl >= 0 else "🔴"
    print(f"\n  {icon} P&L ABERTO:  {total_pnl:+.2f} "
          f"({total_pnl_pct:+.2f}%)")
    print(f"  💰 P&L FECHADO: {closed_pnl:+.2f}")
    print(f"  📊 P&L GLOBAL:  {global_pnl:+.2f}")

    if send_telegram:
        body = "\n\n".join(lines_telegram)
        body += (f"\n\n{icon} <b>P&L Aberto:</b> "
                 f"{total_pnl:+.2f} ({total_pnl_pct:+.2f}%)\n"
                 f"💰 <b>P&L Fechado:</b> {closed_pnl:+.2f}\n"
                 f"📊 <b>P&L Global:</b> {global_pnl:+.2f}")
        telegram_send_html("PORTFOLIO UPDATE", body)

    return positions, total_pnl, closed_pnl, global_pnl

# ── PRICE ALERTS ─────────────────────────────────────────────
PRICE_ALERTS = [
    # Format: (ticker, name, direction, level, note)
    # direction: "above" ou "below"
    ("^VIX",    "VIX",      "above", 25.0,  "Stress — considera hedge"),
    ("^VIX",    "VIX",      "above", 35.0,  "PANICO — oportunidade historica"),
    ("^VIX",    "VIX",      "below", 12.0,  "Complacencia extrema — reduz"),
    ("^SKEW",   "SKEW",     "above", 145.0, "Tail risk elevado"),
    ("GC=F",    "Gold",     "above", 3500.0,"Gold em ATH — breakout"),
    ("BTC-USD", "Bitcoin",  "above", 120000,"BTC breakout nivel historico"),
    ("BTC-USD", "Bitcoin",  "below", 60000, "BTC suporte — entrada potencial"),
    ("SPY",     "S&P500",   "below", 520.0, "S&P retest suporte"),
    ("NVDA",    "Nvidia",   "below", 100.0, "NVDA suporte zona de entrada"),
    ("BCP.LS",  "BCP",      "above", 1.00,  "BCP acima de 1€ — nivel chave"),
    ("EURUSD=X","EUR/USD",  "above", 1.15,  "EUR/USD breakout importante"),
    ("EURUSD=X","EUR/USD",  "below", 1.05,  "EUR/USD suporte chave"),
]

def check_price_alerts(send_telegram=True):
    print(f"\n{'='*60}")
    print(f"  PRICE ALERTS — {RUN_DATE}")
    print("="*60)
    triggered = []
    for ticker, name, direction, level, note in PRICE_ALERTS:
        try:
            price = get_current_price(ticker)
            if price is None: continue
            hit = (price >= level if direction == "above"
                   else price <= level)
            if hit:
                icon = "🔔" if direction == "above" else "🔕"
                msg  = (f"{icon} {name} ({ticker}): "
                        f"${price:.2f} {'≥' if direction=='above' else '≤'} "
                        f"${level:.2f}\n   → {note}")
                print(f"  ⚡ ALERTA: {msg}")
                triggered.append({
                    "ticker":    ticker,
                    "name":      name,
                    "price":     price,
                    "level":     level,
                    "direction": direction,
                    "note":      note,
                    "msg":       msg,
                })
        except:
            continue

    if triggered and send_telegram:
        body = "\n\n".join(t["msg"] for t in triggered)
        telegram_send_html(f"PRICE ALERTS ({len(triggered)})", body)

    print(f"\n  {len(triggered)} alertas disparados de {len(PRICE_ALERTS)}")
    return triggered

# ── RISK ALERTS ───────────────────────────────────────────────
def check_risk_alerts(market_risk_score=None, risk_flags=[],
                      send_telegram=True):
    alerts = []
    print(f"\n{'='*60}")
    print(f"  RISK ALERTS — {RUN_DATE}")
    print("="*60)

    if market_risk_score and market_risk_score >= 70:
        alert = (f"🚨 RISCO ALTO: Market Risk Score = "
                 f"{market_risk_score}/100\n"
                 f"Reduz exposição imediatamente.")
        alerts.append(alert)
        print(f"  ⚡ {alert}")

    if risk_flags:
        for f in risk_flags:
            print(f"    → {f}")

    if send_telegram and alerts:
        body = "\n\n".join(alerts)
        if risk_flags:
            body += "\n\n<b>Flags:</b>\n" + "\n".join(f"• {f}" for f in risk_flags)
        telegram_send_html("RISK ALERT", body)

    return alerts

# ── CRYPTO ALERTS ─────────────────────────────────────────────
CRYPTO_TICKERS = [
    ("BTC-USD",  "Bitcoin"),
    ("ETH-USD",  "Ethereum"),
    ("SOL-USD",  "Solana"),
    ("BNB-USD",  "BNB"),
]

def check_crypto_alerts(send_telegram=True):
    print(f"\n{'='*60}")
    print(f"  CRYPTO MONITOR — {RUN_DATE}")
    print("="*60)
    results = []
    for ticker, name in CRYPTO_TICKERS:
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="5d")
            if h.empty: continue
            closes = h["Close"].values.flatten()
            price  = float(closes[-1])
            chg_1d = round((price-float(closes[-2]))/float(closes[-2])*100, 2) \
                     if len(closes)>1 else 0
            chg_5d = round((price-float(closes[-min(5,len(closes))]))/
                           float(closes[-min(5,len(closes))])*100, 2)
            icon   = "🟢" if chg_1d >= 0 else "🔴"
            print(f"  {icon} {name:12} ${price:,.2f}  "
                  f"1d:{chg_1d:+.2f}%  5d:{chg_5d:+.2f}%")
            results.append({
                "ticker": ticker,
                "name":   name,
                "price":  price,
                "chg_1d": chg_1d,
                "chg_5d": chg_5d,
            })
        except:
            continue
    if results and send_telegram:
        lines = []
        for r in results:
            ic = "🟢" if r["chg_1d"]>=0 else "🔴"
            lines.append(
                f"{ic} <b>{r['name']}</b>: "
                f"${r['price']:,.0f}  "
                f"1d:{r['chg_1d']:+.1f}%"
            )
        telegram_send_html("CRYPTO UPDATE", "\n".join(lines))
    return results

# ── MORNING BRIEFING ──────────────────────────────────────────
def morning_briefing(market_risk_score=None, quad_label=None,
                     send_telegram=True):
    print(f"\n{'='*60}")
    print(f"  MORNING BRIEFING QDV3 — {RUN_DATE}")
    print("="*60)
    positions, total_pnl, total_pnl_pct = calc_portfolio_pnl()
    closed_pnl, _   = calc_closed_pnl()
    global_pnl = total_pnl + closed_pnl
    triggered_alerts = check_price_alerts(send_telegram=False)

    pnl_icon = "🟢" if total_pnl >= 0 else "🔴"
    brief = (
        f"📊 <b>QDV3 Morning Briefing — {RUN_DATE}</b>\n\n"
        f"{'─'*30}\n"
        f"<b>PORTFOLIO</b>\n"
    )
    for p in positions:
        ic = "▲" if p["pnl"]>=0 else "▼"
        brief += (f"• {p['ticker']}: "
                  f"{ic} {p['pnl_pct']:+.2f}% "
                  f"({p['pnl']:+.2f} {p['currency']})\n")

    brief += (
        f"\n{pnl_icon} P&L Aberto: {total_pnl:+.2f}\n"
        f"📈 Global: {global_pnl:+.2f}\n\n"
    )
    if market_risk_score is not None:
        risk_icon = "🚨" if market_risk_score>=70 else \
                    "⚠️" if market_risk_score>=50 else "✅"
        brief += f"{'─'*30}\n<b>RISCO</b>\n"
        brief += f"{risk_icon} Market Risk: {market_risk_score}/100\n"
    if quad_label:
        brief += f"📐 Quad: {quad_label}\n"
    if triggered_alerts:
        brief += f"\n{'─'*30}\n<b>ALERTAS ({len(triggered_alerts)})</b>\n"
        for a in triggered_alerts[:3]:
            brief += f"🔔 {a['name']}: {a['note']}\n"

    print(brief)
    if send_telegram:
        telegram_send(brief)
    return brief

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_portfolio_html(positions, total_pnl, closed_pnl, global_pnl):
    rows = ""
    for p in positions:
        ic = "#4ade80" if p["pnl"]>=0 else "#f43f5e"
        rows += f"""
        <tr>
          <td><strong>{p['ticker']}</strong></td>
          <td style="color:#64748b">{p['name']}</td>
          <td style="color:#475569">{p['market']}</td>
          <td>{p['qty']} × {p['entry']:.4f}</td>
          <td><strong style="color:{ic}">{p['current']:.4f}</strong></td>
          <td style="color:{ic};font-weight:700">{p['pnl_pct']:+.2f}%</td>
          <td style="color:{ic};font-weight:700">{p['pnl']:+.2f}</td>
          <td style="color:#475569">{p['currency']}</td>
          <td style="color:#334155;font-size:9px">{p['date']}</td>
        </tr>"""

    gic = "#4ade80" if global_pnl>=0 else "#f43f5e"
    return f"""
    <div id="portfolio" class="tab-content section">
      <div class="section-title">PORTFOLIO — DEGIRO</div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);
                  gap:8px;margin-bottom:16px">
        <div style="background:{'#4ade8022' if total_pnl>=0 else '#f43f5e22'};
                    border:1px solid {'#4ade8044' if total_pnl>=0 else '#f43f5e44'};
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:9px;color:#475569">P&L ABERTO</div>
          <div style="font-size:24px;font-weight:900;
                      color:{'#4ade80' if total_pnl>=0 else '#f43f5e'}">
              {total_pnl:+.2f}€</div></div>
        <div style="background:{'#4ade8022' if closed_pnl>=0 else '#f43f5e22'};
                    border:1px solid {'#4ade8044' if closed_pnl>=0 else '#f43f5e44'};
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:9px;color:#475569">P&L FECHADO</div>
          <div style="font-size:24px;font-weight:900;
                      color:{'#4ade80' if closed_pnl>=0 else '#f43f5e'}">
              {closed_pnl:+.2f}€</div></div>
        <div style="background:{'#4ade8022' if global_pnl>=0 else '#f43f5e22'};
                    border:1px solid {'#4ade8044' if global_pnl>=0 else '#f43f5e44'};
                    border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:9px;color:#475569">TOTAL GLOBAL</div>
          <div style="font-size:24px;font-weight:900;color:{gic}">
              {global_pnl:+.2f}€</div></div>
      </div>
      <div class="table-wrap">
        <table>
          <tr>
            <th>Ticker</th><th>Nome</th><th>Mercado</th>
            <th>Posição</th><th>Actual</th><th>P&L %</th>
            <th>P&L €</th><th>Moeda</th><th>Data</th>
          </tr>
          {rows}
        </table>
      </div>
    </div>"""