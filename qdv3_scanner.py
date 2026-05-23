# ============================================================
# QDV3_SCANNER.PY — Standalone Scanner v5
# DFA Hurst + P/D VWAP + Brennan + Risk Score
# Todos os mercados num único ficheiro
# Executa sem precisar dos outros módulos
# ============================================================

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG INLINE ─────────────────────────────────────────────
CAPITAL            = 3347.00
RISK_PER_TRADE_PCT = 0.10
LOOKBACK           = 400
TOP_N              = 20
MIN_HURST          = 0.48
MIN_VOLUME         = 50000
RUN_DATE           = datetime.today().strftime("%d %b %Y — %H:%M")

# Universo condensado para scanner standalone
TICKERS = [
    # US Mega Cap
    ("NVDA","Nvidia","NASDAQ"),("AAPL","Apple","NASDAQ"),
    ("MSFT","Microsoft","NASDAQ"),("AMD","AMD","NASDAQ"),
    ("META","Meta","NASDAQ"),("AMZN","Amazon","NASDAQ"),
    ("GOOGL","Alphabet","NASDAQ"),("TSLA","Tesla","NASDAQ"),
    ("PLTR","Palantir","NYSE"),("COIN","Coinbase","NASDAQ"),
    ("MSTR","MicroStrategy","NASDAQ"),("ARM","ARM","NASDAQ"),
    ("MELI","MercadoLibre","NASDAQ"),("BABA","Alibaba","NYSE"),
    ("PDD","PDD","NASDAQ"),("LLY","Eli Lilly","NYSE"),
    ("AVGO","Broadcom","NASDAQ"),("V","Visa","NYSE"),
    # Europe
    ("ASML.AS","ASML","XAMS"),("SAP.DE","SAP","XETRA"),
    ("MC.PA","LVMH","XPAR"),("NOVO-B.CO","Novo Nordisk","XCSE"),
    ("BCP.LS","BCP","XLIS"),("EDP.LS","EDP","XLIS"),
    ("GALP.LS","Galp","XLIS"),
    # ETFs
    ("SPY","S&P500","NYSE"),("QQQ","Nasdaq ETF","NASDAQ"),
    ("IWM","Russell 2000","NYSE"),("GLD","Gold ETF","NYSE"),
    ("TLT","20Y Bond","NYSE"),("EEM","EM ETF","NYSE"),
    ("GDX","Gold Miners","NYSE"),("INDA","India ETF","NYSE"),
    # FX
    ("EURUSD=X","EUR/USD","FX"),("GBPUSD=X","GBP/USD","FX"),
    ("USDJPY=X","USD/JPY","FX"),("AUDUSD=X","AUD/USD","FX"),
    ("USDCAD=X","USD/CAD","FX"),
    # Commodities
    ("GC=F","Gold","COMMODITY"),("CL=F","WTI Crude","COMMODITY"),
    ("NG=F","Nat Gas","COMMODITY"),("SI=F","Silver","COMMODITY"),
    ("HG=F","Copper","COMMODITY"),("ZC=F","Corn","COMMODITY"),
    # Vol
    ("^VIX","VIX","VOL"),("^SKEW","SKEW","VOL"),
    ("^VVIX","VVIX","VOL"),
    # Crypto
    ("BTC-USD","Bitcoin","CRYPTO"),("ETH-USD","Ethereum","CRYPTO"),
    ("SOL-USD","Solana","CRYPTO"),
]

# ── FETCH ─────────────────────────────────────────────────────
def fetch(symbol):
    try:
        end   = datetime.today()
        start = end - timedelta(days=LOOKBACK)
        df    = yf.download(symbol, start=start, end=end,
                            progress=False, auto_adjust=True)
        if df.empty or len(df) < 60: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        cols = [c for c in ["Open","High","Low","Close","Volume"]
                if c in df.columns]
        return df[cols].dropna()
    except:
        return None

# ── HURST DFA ─────────────────────────────────────────────────
def hurst_dfa(series):
    try:
        s = np.array(series, dtype=float).flatten()
        n = len(s)
        if n < 20: return 0.50
        profile  = np.cumsum(s - s.mean())
        max_box  = n // 4
        box_sizes= np.unique(
            np.logspace(np.log10(4),
                        np.log10(max(max_box,5)), 20).astype(int))
        fluc, valid = [], []
        for box in box_sizes:
            if box < 4 or box > n // 2: continue
            n_boxes = n // box
            if n_boxes < 4: continue
            rms = []
            for j in range(n_boxes):
                seg  = profile[j*box:(j+1)*box]
                x    = np.arange(len(seg))
                c    = np.polyfit(x, seg, 1)
                res  = seg - np.polyval(c, x)
                rms.append(np.sqrt(np.mean(res**2)))
            if rms:
                fluc.append(np.mean(rms))
                valid.append(box)
        if len(valid) < 4:
            # Fallback R/S
            lags = range(2, 20)
            tau  = [np.std(np.subtract(s[l:], s[:-l])) for l in lags]
            tau  = [t for t in tau if t > 0]
            if len(tau) < 2: return 0.50
            poly = np.polyfit(np.log(range(2,2+len(tau))), np.log(tau), 1)
            return float(np.clip(poly[0], 0.01, 0.99))
        poly = np.polyfit(np.log(valid), np.log(fluc), 1)
        return float(np.clip(poly[0], 0.01, 0.99))
    except:
        return 0.50

# ── ATR ───────────────────────────────────────────────────────
def atr(df, p=14):
    h = df["High"].astype(float); l=df["Low"].astype(float)
    c = df["Close"].astype(float)
    tr= pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(p).mean()

# ── VWAP ──────────────────────────────────────────────────────
def vwap(df, n):
    try:
        n = min(n, len(df))
        c = df["Close"].astype(float).tail(n)
        if "Volume" in df.columns:
            v = df["Volume"].astype(float).tail(n)
            v = v.replace(0,np.nan).fillna(c.mean())
            if v.sum()==0: return float(c.mean())
            return float((c*v).sum()/v.sum())
        return float(c.mean())
    except:
        return float(df["Close"].astype(float).tail(n).mean())

# ── ZSCORE ────────────────────────────────────────────────────
def zscore(s, w):
    if len(s)<w: return None
    x = s[-w:]; sd=np.std(x)
    if sd==0: return 0.0
    return round(float((s[-1]-np.mean(x))/sd),2)

# ── ANALYSE ───────────────────────────────────────────────────
def analyse(symbol, name, market):
    df = fetch(symbol)
    if df is None: return None
    closes = df["Close"].astype(float).values.flatten()
    if len(closes) < 25: return None
    price  = float(closes[-1])
    low52  = float(np.min(closes[-252:])) if len(closes)>=252 else float(np.min(closes))
    high52 = float(np.max(closes[-252:])) if len(closes)>=252 else float(np.max(closes))

    # P/D via VWAP
    def pd_calc(v):
        return round((price-v)/v*100,2) if v and v>0 else 0.0
    pd_c  = pd_calc(vwap(df,5))
    pd_y  = pd_calc(vwap(df,10))
    pd_1w = pd_calc(vwap(df,22))
    pd_1m = pd_calc(vwap(df,66))
    pd_str= pd_calc(vwap(df,min(252,len(df))))
    roc   = round(pd_c-pd_y,2)

    # Hurst DFA
    h_d  = hurst_dfa(closes[-30:]) if len(closes)>=30 else 0.50
    h_w  = hurst_dfa(closes[-60:]) if len(closes)>=60 else 0.50
    h_roc= round(h_d-h_w,2)
    h_sig= "fortalecer" if h_roc>0.03 else \
           "enfraquecer" if h_roc<-0.03 else "estavel"

    # Vol / Brennan
    if "High" in df.columns and "Low" in df.columns:
        atr_s = atr(df)
        vp    = round(float(atr_s.rank(pct=True).iloc[-1]*100),1)
        comp  = "COMPRESSION+TRENDING" \
                if vp<25 and h_roc>0.03 else \
                "COMPRESSED" if vp<25 else \
                "EXPANDING"  if vp>75 else "NORMAL"
    else:
        vp    = 50.0
        comp  = "N/A"

    # ADX
    adx_v = 0.0
    try:
        if "High" in df.columns and "Low" in df.columns:
            h_s=df["High"].astype(float); l_s=df["Low"].astype(float)
            c_s=df["Close"].astype(float)
            pdm=h_s.diff().clip(lower=0); mdm=(-l_s.diff()).clip(lower=0)
            pdm[pdm<mdm]=0; mdm[mdm<pdm]=0
            tr2=pd.concat([h_s-l_s,(h_s-c_s.shift()).abs(),(l_s-c_s.shift()).abs()],axis=1).max(axis=1)
            atr2=tr2.rolling(14).mean()
            pdi=100*pdm.rolling(14).mean()/atr2
            mdi=100*mdm.rolling(14).mean()/atr2
            dx=(abs(pdi-mdi)/(pdi+mdi)*100).rolling(14).mean()
            adx_v=round(float(dx.iloc[-1]),1)
    except: pass

    # Z-Scores
    ttmz = zscore(closes, min(252,len(closes)))
    yr3z = zscore(closes, min(756,len(closes)))

    # Volume avg
    avg_vol = float(df["Volume"].tail(20).mean()) \
              if "Volume" in df.columns else 0

    # Momentum Score
    ms  = 0
    ms += 0.8 if pd_c<0  else -0.8
    ms += 0.6 if pd_1w<0 else -0.6
    ms += 0.4 if pd_1m<0 else -0.4
    ms += 0.5 if roc<0   else -0.5
    ms += 0.4 if h_d>0.55 else (-0.4 if h_d<0.45 else 0)
    score = round(ms,2)

    # Signal
    if score>= 0.6:  sig="BULLISH"
    elif score<=-0.6:sig="BEARISH"
    else:             sig="TURNING"

    # Conviction
    pts=0
    pts+=2 if abs(score)>=1.5 else (1 if abs(score)>=0.8 else 0)
    pts+=2 if h_d>0.62         else (1 if h_d>0.55 else 0)
    pts+=1 if adx_v>25         else 0
    pts+=1 if 15<vp<85         else 0
    conv="MUITO ALTA" if pts>=5 else "ALTA" if pts>=3 else \
         "MEDIA"      if pts>=2 else "BAIXA"

    # Fractal levels
    rm  = 1.1 if h_d>0.55 else 0.9
    sk  = 1.08
    ts, ns, als = 0.040*rm, 0.120*rm, 0.280*rm
    lvl = {
        "trade":(round(price*(1-ts*sk),4), round(price*(1+ts),4)),
        "trend":(round(price*(1-ns*sk),4), round(price*(1+ns),4)),
        "tail": (round(max(low52*0.95,price*(1-als*sk)),4),
                 round(min(high52*1.05,price*(1+als)),4)),
    }

    # Entry quality
    if (pd_c<0 and pd_1w<0 and pd_1m<0 and h_d>0.55 and
            vp<40 and adx_v>20 and "COMPRES" in comp and score<=-0.8):
        eq="✅ IDEAL"
    elif (pd_c<0 and pd_1w<0 and h_d>0.52 and vp<55 and score<=-0.6):
        eq="🟡 ACEITÁVEL"
    elif (pd_c>0 and pd_1w>0 and h_d>0.55 and vp<40 and "COMPRES" in comp):
        eq="✅ IDEAL LONG"
    elif pd_c>0.05:  eq="⚠️ EXTENDED"
    elif vp>80:      eq="🚨 EXTREMO"
    else:            eq="⏳ AGUARDA"

    # Rank 0-100
    rank = 0
    rank += sum([1 if pd_c<0 else 0, 1 if pd_1w<0 else 0,
                 1 if pd_1m<0 else 0, 1 if pd_str<0 else 0]) * 7.5
    rank += 25 if h_d>=0.70 else 18 if h_d>=0.62 else \
            12 if h_d>=0.55 else  6 if h_d>=0.48 else 0
    rank += min(abs(score)*10,20)
    if 15<=vp<=35: rank+=15
    elif 35<vp<=55:rank+=10
    elif vp<15:    rank+=5
    z2 = abs(ttmz or 0)
    rank += 10 if z2>=2.0 else 7 if z2>=1.5 else 4 if z2>=1.0 else 0
    if "COMPRESSION+TRENDING" in comp: rank+=10
    elif "COMPRESSED" in comp:         rank+=6
    rank = min(round(rank),100)

    pfmt = f"{price:.4f}" if price<10 else \
           f"{price:.3f}" if price<100 else f"{price:.2f}"

    return {
        "symbol":symbol, "name":name, "market":market,
        "price":price,   "pfmt":pfmt,
        "h_d":round(h_d,2), "h_w":round(h_w,2),
        "h_roc":h_roc,   "h_sig":h_sig,
        "pd_c":pd_c,     "pd_y":pd_y,
        "pd_1w":pd_1w,   "pd_1m":pd_1m,
        "pd_str":pd_str, "roc":roc,
        "vp":vp,         "comp":comp,
        "adx":adx_v,     "score":score,
        "signal":sig,    "conv":conv,
        "ttmz":ttmz,     "yr3z":yr3z,
        "avg_vol":avg_vol,"lvl":lvl,
        "entry_q":eq,    "rank":rank,
        "low52":low52,   "high52":high52,
    }

# ── POSITION SIZE ─────────────────────────────────────────────
def position_size(price, market, vp):
    risk_capital = CAPITAL * RISK_PER_TRADE_PCT
    atr_est = price * (vp/100) * 0.02
    sl_dist = max(atr_est*1.5, price*0.03)
    comms = {"NASDAQ":1.00,"NYSE":1.00,"XETRA":3.90,
             "XPAR":3.90,"XAMS":3.90,"XLIS":1.00,"FX":0.00,
             "COMMODITY":1.00,"CRYPTO":0.00,"VOL":1.00}
    comm = comms.get(market, 3.90)
    if sl_dist<=0: return 0,0.0,0.0
    qty      = max(1, int((risk_capital-comm*2)/sl_dist))
    notional = round(qty*price,2)
    sl_price = round(price-sl_dist,4)
    return qty, notional, sl_price

# ── PRINT RESULT ──────────────────────────────────────────────
def print_result(r, rank=0):
    CYAN  = "\033[96m"; GREEN = "\033[92m"; RED   = "\033[91m"
    YELL  = "\033[93m"; GREY  = "\033[90m"; BOLD  = "\033[1m"
    RESET = "\033[0m"

    eq = r["entry_q"]
    ec = GREEN if "IDEAL" in eq else YELL if "ACEIT" in eq else \
         RED   if "EXTREM" in eq else GREY

    hc = GREEN if r["h_d"]>0.62 else YELL if r["h_d"]>0.52 else RED
    pc = GREEN if r["pd_c"]<0   else RED

    print(f"\n  {BOLD}{rank:02d}. {CYAN}{r['symbol']:12}{RESET} "
          f"{r['name'][:18]:18} [{GREY}{r['market']}{RESET}]")
    print(f"      Preço: {r['pfmt']:>10}  "
          f"Hurst(DFA): {hc}{r['h_d']:.2f}{RESET} "
          f"({r['h_sig']})")
    print(f"      P/D:   {pc}{r['pd_c']:+.2f}%{RESET} D  "
          f"{r['pd_1w']:+.2f}% W  {r['pd_1m']:+.2f}% M")
    print(f"      Comp:  {r['comp']:22} "
          f"Vol:{r['vp']:.0f}%  ADX:{r['adx']:.1f}")
    print(f"      Z-TTM: {str(r['ttmz']):8}  "
          f"Score:{r['score']:+.2f}  {r['signal']} ({r['conv']})")
    print(f"      Entry: {ec}{eq}{RESET}  Rank:{BOLD}{r['rank']}/100{RESET}")

    if "IDEAL" in eq or "ACEIT" in eq:
        qty, not_, sl = position_size(r["price"], r["market"], r["vp"])
        if qty > 0:
            print(f"      {BOLD}Position: {qty}x  "
                  f"Notional:{not_:.0f}  SL:{sl:.4f}{RESET}")
        lvl = r.get("lvl",{})
        if lvl:
            t, n, ta = lvl.get("trade"),lvl.get("trend"),lvl.get("tail")
            if t: print(f"      Trade:{t[0]:.4f}↔{t[1]:.4f}  "
                        f"Trend:{n[0]:.4f}↔{n[1]:.4f}")

# ── RUN SCANNER ───────────────────────────────────────────────
def run_scanner():
    print(f"\n{'='*60}")
    print(f"  QDV3 STANDALONE SCANNER v5")
    print(f"  {RUN_DATE}")
    print(f"  DFA Hurst + P/D VWAP + Brennan + Risk")
    print("="*60)

    results = []
    by_market = {}

    for symbol, name, market in TICKERS:
        try:
            print(f"  → {symbol:14} {name[:18]:18}", end="", flush=True)
            r = analyse(symbol, name, market)
            if r is None:
                print("  ✗ sem dados"); continue
            if market not in ["FX","VOL","CRYPTO","MACRO","COMMODITY"]:
                if r["avg_vol"] < MIN_VOLUME:
                    print(f"  ✗ baixo volume"); continue
            if r["h_d"] < MIN_HURST:
                print(f"  ✗ Hurst < {MIN_HURST}"); continue

            results.append(r)
            if market not in by_market: by_market[market] = []
            by_market[market].append(r)

            eq = r["entry_q"]
            ic = "✅" if "IDEAL" in eq else "🟡" if "ACEIT" in eq else \
                 "⚠️" if "EXTEND" in eq else "·"
            print(f"  {ic} H:{r['h_d']:.2f} "
                  f"P/D:{r['pd_c']:+.2f}% "
                  f"R:{r['rank']}")
        except Exception as e:
            print(f"  ⚠️  {e}")

    results.sort(key=lambda x: x["rank"], reverse=True)
    ideal = [r for r in results if "IDEAL" in r.get("entry_q","")]
    aceit = [r for r in results if "ACEIT" in r.get("entry_q","")]

    print(f"\n{'='*60}")
    print(f"  ✅ SETUPS IDEAIS ({len(ideal)})")
    print("="*60)
    for i,r in enumerate(ideal[:10],1):
        print_result(r,i)

    if aceit:
        print(f"\n{'='*60}")
        print(f"  🟡 SETUPS ACEITÁVEIS ({len(aceit)})")
        print("="*60)
        for i,r in enumerate(aceit[:5],1):
            print_result(r,i)

    print(f"\n{'='*60}")
    print(f"  🏆 TOP {TOP_N} — RANKING GERAL")
    print("="*60)
    for i,r in enumerate(results[:TOP_N],1):
        print_result(r,i)

    print(f"\n{'='*60}")
    print(f"  RESUMO QDV3")
    print(f"  Total analisado:  {len(results)}")
    print(f"  Setups Ideais:    {len(ideal)}")
    print(f"  Setups Aceitáveis:{len(aceit)}")
    print(f"  Capital:          €{CAPITAL:,.2f}")
    print(f"  Risco/trade:      €{CAPITAL*RISK_PER_TRADE_PCT:.2f} (10%)")
    print("="*60)

    return results, ideal, aceit

if __name__ == "__main__":
    results, ideal, aceit = run_scanner()