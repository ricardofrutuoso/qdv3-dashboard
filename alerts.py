# ============================================================
# ALERTAS.PY — QDV3 Telegram Bot
# Briefing diário 9h00 | Alertas em tempo real
# Nota psicológica | Top 3 setups | Portfolio
# ============================================================

import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import schedule
import time
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ───────────────────────────────────────────────────
TELEGRAM_TOKEN   = "8865063923:AAGKpnOJh2QUOOZCiw3QYgl-cOTE4SbRKRI"
TELEGRAM_CHAT_ID = "8797381859"
STATE_FILE       = "alertas_state.json"

# ── WATCH LIST ───────────────────────────────────────────────
WATCH_LIST = [
    # Portfolio
    ("NVDA",    "Nvidia",         "NASDAQ"),
    ("BCP.LS",  "BCP",            "XLIS"),
    ("PDD",     "PDD Holdings",   "NASDAQ"),
    # US
    ("AAPL",    "Apple",          "NASDAQ"),
    ("MSFT",    "Microsoft",      "NASDAQ"),
    ("QQQ",     "Nasdaq ETF",     "NASDAQ"),
    ("SPY",     "S&P500 ETF",     "NYSE"),
    ("MELI",    "MercadoLibre",   "NASDAQ"),
    ("NU",      "Nubank",         "NYSE"),
    ("SOFI",    "SoFi",           "NASDAQ"),
    # Europe
    ("ASML.AS", "ASML",           "XAMS"),
    ("QDV5.DE", "MSCI India",     "XETRA"),
    # EM
    ("MCHI",    "China ETF",      "NYSE"),
    ("INDA",    "India ETF",      "NYSE"),
    # Macro
    ("GLD",     "Gold ETF",       "NYSE"),
    ("TLT",     "20Y Bond ETF",   "NYSE"),
    ("^VIX",    "VIX",            "VOL"),
    ("GC=F",    "Gold",           "COMMODITY"),
    ("CL=F",    "WTI Crude",      "COMMODITY"),
    # FX
    ("EURUSD=X","EUR/USD",        "FX"),
    ("GBPUSD=X","GBP/USD",        "FX"),
    ("USDJPY=X","USD/JPY",        "FX"),
    ("GBPJPY=X","GBP/JPY",        "FX"),
    ("EURJPY=X","EUR/JPY",        "FX"),
    ("AUDJPY=X","AUD/JPY",        "FX"),
    ("USDBRL=X","USD/BRL",        "FX"),
    ("USDMXN=X","USD/MXN",        "FX"),
    ("USDTRY=X","USD/TRY",        "FX"),
    ("USDZAR=X","USD/ZAR",        "FX"),
    # Crypto
    ("BTC-USD", "Bitcoin",        "CRYPTO"),
    ("ETH-USD", "Ethereum",       "CRYPTO"),
    ("SOL-USD", "Solana",         "CRYPTO"),
    ("BNB-USD", "BNB",            "CRYPTO"),
    ("XRP-USD", "XRP",            "CRYPTO"),
    ("DOGE-USD","Dogecoin",       "CRYPTO"),
    # Crypto stocks
    ("COIN",    "Coinbase",       "NASDAQ"),
    ("MSTR",    "MicroStrategy",  "NASDAQ"),
]

# ── NOTAS PSICOLÓGICAS ROTATIVAS ─────────────────────────────
PSYCH_NOTES = [
    "\"A ticket is only a ticket.\" — Keith McCullough\nNão é a tua identidade. É apenas uma posição num modelo.",
    "O mercado não sabe que tens uma posição.\nEle não te deve nada. Segue o modelo.",
    "\"Size kills.\" — McCullough\nO tamanho da posição mata mais do que a direcção errada.",
    "Stop loss não é fraqueza.\nÉ o acto mais profissional que um trader pode fazer.",
    "Deixa os vencedores correr.\nO teu trabalho não é ter razão — é gerir o risco.",
    "Não adiciones a perdedores.\nUma posição negativa não merece mais capital.",
    "O Hurst baixo avisa-te.\nO momentum alto confirma-te. Usa os dois.",
    "Quad 2 favorece commodities e value.\nNão lutas contra o regime macro.",
    "Vol baixa = opção barata.\nCompra o bilhete quando está em saldo.",
    "\"Risk manage or go home.\" — McCullough\nA gestão de risco é o teu edge.",
    "Um mau trade não é um mau trader.\nO padrão ao longo do tempo é o que conta.",
    "Quando tens dúvida — não entras.\nO mercado vai sempre dar outra oportunidade.",
    "O modelo é o teu escudo emocional.\nQuando o viés humano fala — o modelo responde.",
    "Três timeframes alinhados = sinal forte.\nUm sozinho é ruído.",
    "Brennan compression é o teu amigo.\nA mola comprimida vai soltar — o modelo diz-te para onde.",
]

# ── TELEGRAM ─────────────────────────────────────────────────
def send_message(text):
    try:
        url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "HTML",
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"⚠️  Telegram erro: {e}")
        return False

# ── FETCH ────────────────────────────────────────────────────
def fetch(symbol, days=60):
    try:
        end   = datetime.today()
        start = end - timedelta(days=days)
        df    = yf.download(symbol, start=start, end=end,
                            progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df = df.droplevel(1, axis=1)
        closes = df["Close"].dropna().reset_index(drop=True)
        return closes
    except:
        return None

# ── INDICATORS ───────────────────────────────────────────────
def hurst(series):
    try:
        s    = np.array(series, dtype=float).flatten()
        lags = range(2, 20)
        tau  = [np.std(np.subtract(s[l:], s[:-l])) for l in lags]
        tau  = [t for t in tau if t > 0]
        if len(tau) < 2:
            return 0.50
        poly = np.polyfit(np.log(range(2, 2+len(tau))),
                          np.log(tau), 1)
        return float(np.clip(poly[0], 0.01, 0.99))
    except:
        return 0.50

def analyse_ticker(symbol):
    closes = fetch(symbol)
    if closes is None or len(closes) < 22:
        return None

    price = float(closes.iloc[-1])
    p1d   = float(closes.iloc[-2])
    p1w   = float(closes.iloc[-6])  if len(closes) > 5  else price
    p1m   = float(closes.iloc[-22]) if len(closes) > 21 else price
    p2d   = float(closes.iloc[-3])  if len(closes) > 2  else p1d

    pd_c  = (price-p1d)/p1d*100
    pd_y  = (p1d  -p2d)/p2d*100
    pd_1w = (price-p1w)/p1w*100
    pd_1m = (price-p1m)/p1m*100
    roc   = pd_c - pd_y
    h     = hurst(closes.iloc[-30:])

    score = 0
    score += 0.8 if pd_c  > 0 else -0.8
    score += 0.6 if pd_1w > 0 else -0.6
    score += 0.4 if pd_1m > 0 else -0.4
    score += 0.5 if roc   > 0 else -0.5
    score += 0.4 if h > 0.55 else (-0.4 if h < 0.45 else 0)
    score  = round(score, 2)

    if score >=  0.6: signal = "BULLISH"
    elif score <= -0.6: signal = "BEARISH"
    else: signal = "TURNING"

    # Rank
    rank = 0
    if pd_c > 0 and pd_1w > 0 and pd_1m > 0:    rank += 30
    elif pd_c < 0 and pd_1w < 0 and pd_1m < 0:  rank += 30
    elif (pd_1w > 0 and pd_1m > 0) or \
         (pd_1w < 0 and pd_1m < 0):              rank += 15
    if h >= 0.65:   rank += 25
    elif h >= 0.60: rank += 20
    elif h >= 0.55: rank += 15
    elif h >= 0.50: rank += 5
    ms = abs(score)
    if ms >= 2.0:   rank += 20
    elif ms >= 1.5: rank += 15
    elif ms >= 1.0: rank += 10
    elif ms >= 0.5: rank += 5

    # Brennan compression
    compressed = False
    if len(closes) >= 30:
        atr_now = float(closes.diff().abs().tail(5).mean())
        atr_avg = float(closes.diff().abs().tail(30).mean())
        if atr_avg > 0 and (atr_now/atr_avg) < 0.4:
            compressed = True
            rank += 10

    pfmt = f"{price:.4f}" if price < 10 else \
           f"{price:.3f}" if price < 100 else \
           f"{price:.2f}"

    return {
        "symbol":     symbol,
        "price":      price,
        "pfmt":       pfmt,
        "signal":     signal,
        "score":      score,
        "rank":       round(rank, 1),
        "h":          round(h, 2),
        "pd_c":       round(pd_c, 2),
        "pd_1w":      round(pd_1w, 2),
        "pd_1m":      round(pd_1m, 2),
        "roc":        round(roc, 2),
        "compressed": compressed,
    }

# ── STATE ────────────────────────────────────────────────────
def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except:
        pass

# ── VIX CONTEXT ──────────────────────────────────────────────
def get_vix_context(vix_price):
    if vix_price is None:
        return "N/A", "⚪"
    if vix_price >= 30:
        return f"😱 PÂNICO ({vix_price:.1f})", "🔴"
    if vix_price >= 25:
        return f"😨 STRESS ({vix_price:.1f})", "🟠"
    if vix_price >= 20:
        return f"😐 ELEVADO ({vix_price:.1f})", "🟡"
    if vix_price >= 15:
        return f"😊 NORMAL ({vix_price:.1f})", "🟢"
    return f"😴 COMPLACÊNCIA ({vix_price:.1f})", "⚠️"

# ── DAILY BRIEFING ───────────────────────────────────────────
def daily_briefing():
    now_str  = datetime.now().strftime("%d %b %Y %H:%M")
    weekday  = datetime.now().strftime("%A")
    days_pt  = {
        "Monday":"Segunda","Tuesday":"Terça",
        "Wednesday":"Quarta","Thursday":"Quinta",
        "Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"
    }
    day_pt = days_pt.get(weekday, weekday)

    print(f"\n{'='*50}")
    print(f"  BRIEFING DIÁRIO — {now_str}")
    print(f"{'='*50}")

    results   = []
    vix_price = None

    for symbol, name, category in WATCH_LIST:
        try:
            r = analyse_ticker(symbol)
            if r:
                r["name"]     = name
                r["category"] = category
                results.append(r)
                print(f"  ✓ {symbol:12} {r['pfmt']:>10}  "
                      f"{r['signal']:8}  Rank:{r['rank']}")
                if symbol == "^VIX":
                    vix_price = r["price"]
        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")

    if not results:
        send_message("⚠️ Briefing falhou — sem dados")
        return

    # VIX
    vix_label, vix_emoji = get_vix_context(vix_price)

    # Contagens
    bull = [r for r in results if r["signal"]=="BULLISH"]
    bear = [r for r in results if r["signal"]=="BEARISH"]
    turn = [r for r in results if r["signal"]=="TURNING"]

    # Crypto summary
    crypto = [r for r in results if r["category"]=="CRYPTO"]
    btc    = next((r for r in results if r["symbol"]=="BTC-USD"), None)

    # Top 3
    top3 = sorted(
        [r for r in results if r["signal"] in ["BULLISH","BEARISH"]],
        key=lambda x: x["rank"],
        reverse=True
    )[:3]

    # Portfolio
    from config import PORTFOLIO
    portfolio_lines = ""
    for p in PORTFOLIO:
        r = next((x for x in results
                  if x["symbol"]==p["ticker"]), None)
        if r:
            pl_pct = (r["price"] - p["entry"]) / p["entry"] * 100
            arrow  = "▲" if pl_pct >= 0 else "▼"
            emoji  = "🟢" if pl_pct >= 0 else "🔴"
            portfolio_lines += (
                f"\n{emoji} {p['ticker']:8} "
                f"{arrow} {pl_pct:+.2f}%"
                f"  [{r['signal']}]"
            )
        else:
            portfolio_lines += f"\n⚪ {p['ticker']:8} — sem dados"

    # Crypto lines
    crypto_lines = ""
    for r in crypto[:4]:
        emoji = "🟢" if r["signal"]=="BULLISH" else \
                "🔴" if r["signal"]=="BEARISH" else "🟡"
        crypto_lines += (
            f"\n{emoji} {r['symbol'].replace('-USD',''):6} "
            f"{r['pfmt']:>12}  "
            f"D:{r['pd_c']:+.2f}%"
        )

    # Nota psicológica
    day_num    = datetime.now().timetuple().tm_yday
    psych_note = PSYCH_NOTES[day_num % len(PSYCH_NOTES)]

    # Top 3 formatado
    top3_lines = ""
    medals     = {1:"🥇", 2:"🥈", 3:"🥉"}
    for i, r in enumerate(top3, 1):
        emoji = "🟢" if r["signal"]=="BULLISH" else "🔴"
        comp  = "🔥" if r["compressed"] else ""
        top3_lines += (
            f"\n{medals[i]} {r['symbol']:8} "
            f"{emoji} {r['signal']}"
            f"  Rank:{r['rank']}/100 {comp}"
            f"\n   Score:{r['score']:+.1f}  "
            f"H:{r['h']}  "
            f"D:{r['pd_c']:+.2f}%  "
            f"W:{r['pd_1w']:+.2f}%"
        )

    # Regime
    bull_pct = round(len(bull)/len(results)*100) if results else 0
    bear_pct = round(len(bear)/len(results)*100) if results else 0
    if bull_pct > 60:         regime = "🟢 BULL DOMINANTE"
    elif bear_pct > 60:       regime = "🔴 BEAR DOMINANTE"
    elif bull_pct > bear_pct: regime = "🟡 BULL FRACO"
    else:                     regime = "🟡 BEAR FRACO"

    # BTC context
    btc_line = ""
    if btc:
        btc_emoji = "🟢" if btc["signal"]=="BULLISH" else \
                    "🔴" if btc["signal"]=="BEARISH" else "🟡"
        btc_line = (f"\n₿ BTC: {btc_emoji} {btc['pfmt']}"
                    f"  D:{btc['pd_c']:+.2f}%"
                    f"  [{btc['signal']}]")

    # Regras
    rules = (
        "→ Stop loss -8% sem negociação\n"
        "→ Não adicionar a perdedores\n"
        "→ Deixa os vencedores correr\n"
        "→ Uma trade de cada vez\n"
        "→ O modelo manda — não o feeling"
    )

    msg = (
        f"🌅 <b>BOM DIA RICKY!</b>\n"
        f"{day_pt}, {now_str}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>MERCADO</b>\n"
        f"VIX: {vix_emoji} {vix_label}\n"
        f"Regime: {regime}\n"
        f"🟢 Bull: {len(bull)} | "
        f"🔴 Bear: {len(bear)} | "
        f"🟡 Turn: {len(turn)}\n"
        f"{btc_line}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"💼 <b>PORTFOLIO</b>"
        f"{portfolio_lines}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"₿ <b>CRYPTO</b>"
        f"{crypto_lines}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>TOP 3 SETUPS</b>"
        f"{top3_lines}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>REGRAS DO DIA</b>\n"
        f"{rules}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>NOTA PSICOLÓGICA</b>\n"
        f"{psych_note}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>QDV3 · Hurst · Fractal · Regime</i>"
    )

    success = send_message(msg)
    if success:
        print("  ✅ Briefing enviado!")
    else:
        print("  ❌ Briefing falhou!")

# ── ALERT CHECK ──────────────────────────────────────────────
def check_alerts():
    now_str = datetime.now().strftime("%d %b %Y %H:%M")
    print(f"\n{'='*50}")
    print(f"  ALERT CHECK — {now_str}")
    print(f"{'='*50}")

    state  = load_state()
    alerts = []

    for symbol, name, category in WATCH_LIST:
        try:
            r = analyse_ticker(symbol)
            if not r:
                continue

            price  = r["price"]
            signal = r["signal"]
            score  = r["score"]

            prev        = state.get(symbol, {})
            prev_signal = prev.get("signal", "UNKNOWN")
            prev_score  = prev.get("score",  0)

            signal_changed = (prev_signal != signal and
                              prev_signal != "UNKNOWN")
            score_jump     = abs(score - prev_score) >= 1.0

            emoji = "🟢" if signal=="BULLISH" else \
                    "🔴" if signal=="BEARISH" else "🟡"

            print(f"  {emoji} {symbol:12} {r['pfmt']:>10}  "
                  f"{signal:8}  Score:{score:+.1f}")

            # Mudança de regime
            if signal_changed:
                action = "📈 CONSIDERAR LONG" \
                         if signal=="BULLISH" else \
                         "📉 CONSIDERAR SHORT/SAIR" \
                         if signal=="BEARISH" else \
                         "⏳ AGUARDAR"
                alerts.append(
                    f"🔄 <b>MUDANÇA DE REGIME!</b>\n\n"
                    f"{emoji} <b>{name} ({symbol})</b>\n"
                    f"Preço: <b>{r['pfmt']}</b>\n\n"
                    f"Sinal:  {prev_signal} → <b>{signal}</b>\n"
                    f"Score:  {prev_score:+.1f} → <b>{score:+.1f}</b>\n"
                    f"Rank:   <b>{r['rank']}/100</b>\n"
                    f"Hurst:  <b>{r['h']}</b>\n"
                    f"P/D D:  <b>{r['pd_c']:+.2f}%</b>\n"
                    f"P/D W:  <b>{r['pd_1w']:+.2f}%</b>\n\n"
                    f"<b>{action}</b>\n\n"
                    f"🕐 {now_str}"
                )

            # Aceleração score
            elif score_jump:
                alerts.append(
                    f"⚡ <b>ACELERAÇÃO DE SCORE!</b>\n\n"
                    f"{emoji} <b>{name} ({symbol})</b>\n"
                    f"Preço: <b>{r['pfmt']}</b>\n"
                    f"Score: {prev_score:+.1f} → <b>{score:+.1f}</b>\n"
                    f"Sinal: <b>{signal}</b>\n\n"
                    f"🕐 {now_str}"
                )

            # VIX
            if symbol == "^VIX":
                if price > 25 and prev.get("price",0) <= 25:
                    alerts.append(
                        f"😨 <b>VIX ACIMA DE 25!</b>\n\n"
                        f"VIX: <b>{r['pfmt']}</b>\n"
                        f"Stress elevado — reduz exposição\n\n"
                        f"🕐 {now_str}"
                    )
                elif price < 15 and prev.get("price",0) >= 15:
                    alerts.append(
                        f"😴 <b>VIX ABAIXO DE 15!</b>\n\n"
                        f"VIX: <b>{r['pfmt']}</b>\n"
                        f"Complacência extrema — cuidado\n\n"
                        f"🕐 {now_str}"
                    )

            # Brennan compression
            if r["compressed"] and not prev.get("compressed", False):
                alerts.append(
                    f"🔥 <b>COMPRESSION DETECTADA!</b>\n\n"
                    f"{emoji} <b>{name} ({symbol})</b>\n"
                    f"Preço: <b>{r['pfmt']}</b>\n"
                    f"Vol muito comprimida\n"
                    f"Breakout iminente — sinal: {signal}\n\n"
                    f"🕐 {now_str}"
                )

            # BTC alerta especial
            if symbol == "BTC-USD":
                if price > 100000 and prev.get("price",0) <= 100000:
                    alerts.append(
                        f"🚀 <b>BTC ACIMA DE $100K!</b>\n\n"
                        f"Bitcoin: <b>{r['pfmt']}</b>\n"
                        f"Marco histórico atingido!\n\n"
                        f"🕐 {now_str}"
                    )

            # Portfolio alerts
            from config import PORTFOLIO
            port_map = {p["ticker"]: p for p in PORTFOLIO}
            if symbol in port_map:
                p      = port_map[symbol]
                pl_pct = (price - p["entry"]) / p["entry"] * 100

                if pl_pct < -8 and prev.get("pl_pct", 0) >= -8:
                    alerts.append(
                        f"🚨 <b>STOP LOSS!</b>\n\n"
                        f"<b>{name} ({symbol})</b>\n"
                        f"Entrada: {p['entry']:.4f}\n"
                        f"Actual:  {r['pfmt']}\n"
                        f"P&L: <b>{pl_pct:+.2f}%</b> 🔴\n\n"
                        f"⚠️ -8% atingido — considera fechar!\n\n"
                        f"🕐 {now_str}"
                    )

                if pl_pct > 15 and prev.get("pl_pct", 0) <= 15:
                    alerts.append(
                        f"🎯 <b>TAKE PROFIT!</b>\n\n"
                        f"<b>{name} ({symbol})</b>\n"
                        f"Entrada: {p['entry']:.4f}\n"
                        f"Actual:  {r['pfmt']}\n"
                        f"P&L: <b>{pl_pct:+.2f}%</b> 🟢\n\n"
                        f"💰 +15% atingido — considera realizar!\n\n"
                        f"🕐 {now_str}"
                    )

                state.setdefault(symbol, {})["pl_pct"] = pl_pct

            # Guarda estado
            state[symbol] = {
                **state.get(symbol, {}),
                "signal":     signal,
                "score":      score,
                "price":      price,
                "h":          r["h"],
                "compressed": r["compressed"],
            }

        except Exception as e:
            print(f"  ⚠️  {symbol} — {e}")
            continue

    if alerts:
        print(f"\n  📤 {len(alerts)} alertas...")
        for alert in alerts:
            send_message(alert)
            print(f"  ✅ Enviado")
    else:
        print(f"  ✅ Sem mudanças significativas")

    save_state(state)

# ── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "once":
        check_alerts()

    elif len(sys.argv) > 1 and sys.argv[1] == "briefing":
        daily_briefing()

    else:
        print("🤖 QDV3 Alerts Bot iniciado!")
        print("📅 Briefing: 09:00")
        print("🔔 Alertas:  09:00 + 21:00")
        print("⌨️  Ctrl+C para parar\n")

        send_message(
            f"🤖 <b>QDV3 Bot iniciado!</b>\n\n"
            f"📅 Briefing diário: 09:00\n"
            f"🔔 Alertas: 09:00 + 21:00\n\n"
            f"Monitoring activo:\n"
            f"• {len(WATCH_LIST)} tickers\n"
            f"• Stop loss -8%\n"
            f"• Take profit +15%\n"
            f"• Mudanças de regime\n"
            f"• Brennan compression\n"
            f"• VIX extremos\n"
            f"• BTC $100K alerta\n\n"
            f"🕐 {datetime.now().strftime('%d %b %Y %H:%M')}"
        )

        schedule.every().day.at("09:00").do(daily_briefing)
        schedule.every().day.at("21:00").do(check_alerts)

        check_alerts()

        while True:
            schedule.run_pending()
            time.sleep(60)