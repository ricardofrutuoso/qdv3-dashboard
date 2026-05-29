# ============================================================
# SCANNER_MACRO.PY — Global Macro QDV3 v4
# Hedgeye Quad Framework — Metodologia Correcta
#
# METODOLOGIA:
# 1. Calcula ROC (YoY% ou MoM%) de cada indicador
# 2. Calcula ACELERAÇÃO = variação do ROC vs período anterior
# 3. Agrega acelerações (ponderadas) → Growth Score + Inflation Score
# 4. Sinal do score composto determina o Quad:
#    Growth Score > 0  AND  Inflation Score > 0  → QUAD 2
#    Growth Score > 0  AND  Inflation Score < 0  → QUAD 1
#    Growth Score < 0  AND  Inflation Score > 0  → QUAD 3
#    Growth Score < 0  AND  Inflation Score < 0  → QUAD 4
#
# GDP e PCE = leading indicators do growth
# PPI = leading indicator do inflation (lidera CPI ~3-6m)
# ============================================================

import requests, numpy as np, pandas as pd, os, pickle
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from config import FRED_API_KEY, RUN_DATE

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# ── OECD IP CACHE (previne rate-limit 429) ────────────────────
_OECD_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "oecd_ip_cache.pkl")
_OECD_CACHE_TTL_H = 12   # horas — dados mensais, não precisam de refresh frequente
_oecd_ip_mem: dict = {}   # cache in-memory para o run actual

def _oecd_cache_load() -> dict:
    try:
        with open(_OECD_CACHE_FILE, "rb") as f:
            obj = pickle.load(f)
        age_h = (datetime.now() - obj["ts"]).total_seconds() / 3600
        return obj.get("data", {}) if age_h < _OECD_CACHE_TTL_H else {}
    except Exception:
        return {}

def _oecd_cache_save(data: dict):
    try:
        with open(_OECD_CACHE_FILE, "wb") as f:
            pickle.dump({"ts": datetime.now(), "data": data}, f)
    except Exception:
        pass

# Carrega o cache de disco no arranque do módulo
_oecd_ip_mem = _oecd_cache_load()

# ── OECD IP DIRECTO (bypass lag do FRED mirror) ───────────────
def _oecd_ip_fresh(iso3, start_year=2018):
    """
    Fetches IP index from OECD DF_INDSERV (PRVM+BTE+IX+Y).
    Equivalente ao PRINTO01.IXOBSAM do antigo MEI_REAL.
    Tipicamente 2-3 meses mais recente do que o mirror FRED.
    Devolve pd.DataFrame com colunas 'date','value' ou None.
    Usa cache de disco (12h TTL) para evitar rate-limit 429.
    """
    global _oecd_ip_mem

    # ── Cache hit ─────────────────────────────────────────────
    if iso3 in _oecd_ip_mem:
        return _oecd_ip_mem[iso3]   # pode ser None (429 anterior)

    # ── Fetch OECD API ────────────────────────────────────────
    result = None
    for activity in ("BTE", "C", "_T"):
        url = (
            f"https://sdmx.oecd.org/public/rest/data/"
            f"OECD.SDD.STES,DSD_STES@DF_INDSERV/"
            f"{iso3}.M.PRVM.IX.{activity}.Y._Z._Z.N"
            f"?startPeriod={start_year}-01&format=jsondata"
        )
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 429:
                break                 # rate-limit — não tentar mais países
            if r.status_code != 200:
                continue
            raw = r.json()
            data_block = raw.get("data", {})
            datasets   = data_block.get("dataSets", [{}])
            structures = data_block.get("structures", [{}])
            if not datasets or not structures:
                continue
            obs_dims = (structures[0].get("dimensions", {})
                                     .get("observation", []))
            time_dim = next(
                (d for d in obs_dims if d.get("id") == "TIME_PERIOD"), None
            )
            if time_dim is None:
                continue
            time_values = [v["id"] for v in time_dim.get("values", [])]
            series_dict = datasets[0].get("series", {})
            rows = {}
            for _, sdata in series_dict.items():
                for t_str, vals in sdata.get("observations", {}).items():
                    t_idx = int(t_str)
                    if (t_idx < len(time_values)
                            and vals and vals[0] is not None):
                        try:
                            yr, mo = time_values[t_idx].split("-")
                            dt = (pd.Timestamp(int(yr), int(mo), 1)
                                  + pd.offsets.MonthEnd(0))
                            rows[dt] = float(vals[0])
                        except Exception:
                            continue
            if len(rows) >= 14:
                s = pd.Series(rows).sort_index()
                result = pd.DataFrame({"date": s.index, "value": s.values})
                result = result.sort_values("date").reset_index(drop=True)
                break
        except Exception:
            continue

    # ── Guardar em cache ─────────────────────────────────────
    _oecd_ip_mem[iso3] = result
    if result is not None:
        # Só persiste resultados válidos — falhas (429) não são guardadas
        # no disco para que o próximo run tente de novo
        _oecd_cache_save({k: v for k, v in _oecd_ip_mem.items()
                          if v is not None})
    return result

# ── CORES DOS QUADS (Q1 verde escuro → Q4 vermelho) ───────────
# Dicas baseadas em dados reais do quad_playbook_data.json (5 anos, SPY+TIP/IEF proxy)
QUAD_PLAYBOOK = {
    1: {
        "label":"QUAD 1","desc":"Growth ↑  Inflation ↓",
        "color":"#15803d","color_bg":"#14532d",
        "icon":"■","text":"Goldilocks",
        # Dados reais: Korea +63%, Silver +63%, IWM +52%, Brasil +54%, Taiwan +42%,
        # Platinum +43%, IBEX +40%, XLC +40%, XLK +39%, QQQ +37%, EEM +37%
        "best":  ["Small Caps (IWM +52%)", "EM Ásia (Korea +63%, Taiwan +42%)",
                  "Prata/Platina (+63%/+43%)", "Tech/Comm (XLK +39%, XLC +40%)",
                  "EU Periféria (IBEX +40%, MIB +35%)", "Brasil (EWZ +54%)"],
        # Dados reais: NatGas -86%, Sugar -19%, Soybeans -14%, USD fraco
        "worst": ["NatGas (-86%)", "Soft Commodities (Sugar, Corn, Soja)",
                  "USD Index (fraco)", "Bonds Longos (fraca alpha)"],
        "action": "MAX risk-on global · LONG small caps, EM, EU periféria, preciosos · AVOID natgas e soft commodities",
        # Highlights para display rápido
        "highlights": [
            ("Korea KOSPI", "+63%"), ("IWM Small Cap", "+52%"), ("Brasil EWZ", "+54%"),
            ("Silver", "+63%"), ("QQQ Tech", "+37%"), ("IBEX Espanha", "+40%"),
        ],
        "avoid_highlights": [
            ("NatGas", "-86%"), ("Sugar", "-19%"), ("Soybeans", "-14%"),
        ],
    },
    2: {
        "label":"QUAD 2","desc":"Growth ↑  Inflation ↑",
        "color":"#4ade80","color_bg":"#166534",
        "icon":"■","text":"Reflação",
        # Dados reais: NatGas +87%, WTI +46%, Coffee +47%, Brent +45%, Cocoa +36%,
        # XLE Energy +37%, QQQ +35%, SPY +26%, XLK +27%, IBCK EUR bonds +18%
        "best":  ["Energy (XLE +37%, WTI +46%)", "NatGas (+87%)",
                  "Soft Comm (Coffee +47%, Cocoa +36%)", "US Equities (QQQ +35%, SPY +26%)",
                  "EUR IG Bonds (IBCK +18%)", "USD Index (+9%)"],
        # Dados reais: TLT -9%, JPY -10%, Brasil -17%, TIP flat
        "worst": ["Long Duration (TLT -9%)", "JPY/USD (-11%)",
                  "Brasil EWZ (-17%)", "EU Periféria (underperforma US)"],
        "action": "LONG energy sector e commodities duras · LONG US equities (value > growth) · SHORT JPY e duration longa",
        "highlights": [
            ("NatGas", "+87%"), ("XLE Energy", "+37%"), ("WTI Oil", "+46%"),
            ("Coffee", "+47%"), ("QQQ", "+35%"), ("USD Index", "+9%"),
        ],
        "avoid_highlights": [
            ("TLT 20Y", "-9%"), ("JPY/USD", "-11%"), ("Brasil EWZ", "-17%"),
        ],
    },
    3: {
        "label":"QUAD 3","desc":"Growth ↓  Inflation ↑",
        "color":"#f97316","color_bg":"#422006",
        "icon":"■","text":"Estagflação",
        # Dados reais: NatGas +91%, WTI +59%, XLE +48%, Cocoa +46%, Brent +37%, Wheat +43%
        # NOTA: Ouro FLAT (-0.4%!) em Q3 — não é refúgio aqui. Energia é o refúgio.
        # IBEX Espanha único índice EU positivo (+21.5%)
        "best":  ["NatGas (+91%)", "WTI/Brent (+59%/+37%)", "XLE Energy (+48%)",
                  "Hard Commodities (Wheat +43%, Cocoa +46%)", "Cash/USD",
                  "IBEX Espanha (+22% — único EU positivo)"],
        # Dados reais: XLY -34%, TLT -34%, XLC -27%, JPY -21%, QQQ -16%, IWM -16%,
        # China -17%, Taiwan -16%, Ouro -0.4% (flat, não refúgio!)
        "worst": ["Consumer Discr XLY (-34%!)", "Long Bonds TLT (-34%)",
                  "Comm/Tech (XLC -27%, QQQ -16%)", "EM Ásia (China -17%, Taiwan -16%)",
                  "JPY/USD (-21%)", "OURO (flat -0.4%, não é refúgio em Q3!)"],
        "action": "LONG energia e hard commodities · CASH · Reduce ALL equities · EVITAR: XLY, bonds longos, EM Ásia, JPY",
        "highlights": [
            ("NatGas", "+91%"), ("XLE Energy", "+48%"), ("WTI Oil", "+59%"),
            ("Wheat", "+43%"), ("IBEX Espanha", "+22%"), ("Cash USD", "refúgio"),
        ],
        "avoid_highlights": [
            ("XLY Cons.Discr", "-34%"), ("TLT 20Y", "-34%"), ("China FXI", "-17%"),
            ("JPY/USD", "-21%"), ("Ouro", "flat -0.4%"),
        ],
    },
    4: {
        "label":"QUAD 4","desc":"Growth ↓  Inflation ↓",
        "color":"#ef4444","color_bg":"#7f1d1d",
        "icon":"■","text":"Recessão/Deflação",
        # Dados reais: NatGas +106% (sazonal!), TLT +22%, IBCK EUR bonds +20%,
        # Brasil +26% (único EM positivo!), JPY +11%, GLD +18%, IEF +12%
        "best":  ["NatGas (+106% — sazonal)", "Long Duration (TLT +22%, IEF +12%)",
                  "EUR Bonds (IBCK +20%)", "Brasil EWZ (+26% — único EM!)",
                  "JPY/USD (+11%)", "Ouro GLD (+18%)"],
        # Dados reais: China -48%!, WTI -53%, Korea -29%, Germany -27%, XLB -35%, XLC -28%
        "worst": ["China FXI (-48%!!! — pior asset)", "WTI/Brent (-53%/-40%)",
                  "Korea KOSPI (-29%)", "Germany DAX (-27%)",
                  "Materials XLB (-35%)", "Comm/Tech XLC (-28%)"],
        "action": "LONG duration e ouro · LONG NatGas (sazonal) · LONG JPY · SHORT China e EM · SHORT energia e materiais",
        "highlights": [
            ("NatGas", "+106%"), ("TLT 20Y", "+22%"), ("Brasil EWZ", "+26%"),
            ("JPY/USD", "+11%"), ("Ouro GLD", "+18%"), ("IBCK EUR", "+20%"),
        ],
        "avoid_highlights": [
            ("China FXI", "-48%"), ("WTI Oil", "-53%"), ("Korea KOSPI", "-29%"),
            ("XLB Materiais", "-35%"), ("Germany DAX", "-27%"),
        ],
    },
    0: {
        "label":"—","desc":"Dados insuficientes",
        "color":"#475569","color_bg":"#1e293b",
        "icon":"·","text":"Aguarda",
        "best":[],"worst":[],"action":"Aguarda dados",
        "highlights":[],"avoid_highlights":[],
    },
}

# ── INDICADORES POR ECONOMIA ──────────────────────────────────
# Cada indicador tem: série FRED, peso, tipo (growth/inflation), frequência
# Leading indicators têm peso maior

INDICATOR_DEFS = {
    # ── US ───────────────────────────────────────────────────
    "US_GROWTH": [
        # Quarterly — GDP mais recente possível
        ("GDPC1",        "GDP Real",         3, "quarterly"),
        # GDPC1 pode ter lag - A939RX0Q048SBEA como backup
        ("A939RX0Q048SBEA","GDP per Capita",  2, "quarterly"),
        # NOTA: A191RL1Q225SBEA REMOVIDO — é uma TAXA (% change anualizado),
        # não um nível. Aplicar-lhe YoY% gera acelerações explosivas (+440)
        # que sequestram o score. GDP já coberto por GDPC1 + per Capita (níveis).
        # Monthly — PCE tem lag de 1 mês vs IP/Payrolls
        # Peso equilibrado para não deixar PCE (lagado) dominar
        ("PCEC96",       "PCE Real",          2, "monthly"),    # leading mas lag 1m
        ("INDPRO",       "Prod Industrial",   3, "monthly"),    # mais recente
        ("PAYEMS",       "Non-Farm Payroll",  3, "monthly"),    # mais recente
        ("RETAILSMNSA",  "Retail Sales",      2, "monthly"),
        ("UMCSENT",      "Consumer Sent",     2, "monthly"),
        ("HOUST",        "Housing Starts",    1, "monthly"),
        ("DGORDER",      "Durable Goods",     1, "monthly"),
        ("TOTALSA",      "Auto Sales",        1, "monthly"),
    ],
    "US_INFLATION": [
        # PPI como leading indicator (lidera CPI 3-6m)
        ("PPIFIS",   "PPI Final Demand", 4, "monthly"),
        ("PPIACO",   "PPI All Comm",     3, "monthly"),
        # CPI/PCE como confirmação
        ("CPIAUCSL", "CPI",              3, "monthly"),
        ("CPILFESL", "Core CPI",         3, "monthly"),
        ("PCEPILFE", "Core PCE",         2, "monthly"),
        # Market-based expectativas
        ("T10YIE",   "Breakeven 10Y",    2, "daily"),
        ("MICH",     "UMich Infl Exp",   1, "monthly"),
    ],
    # ── EUROZONA ─────────────────────────────────────────────
    "EZ_GROWTH": [
        ("CLVMNACSCAB1GQEA","GDP EZ",   4, "quarterly"),
        ("EUGLORMAN",       "IP EZ",    2, "monthly"),
    ],
    "EZ_INFLATION": [
        ("CP0000EZ19M086NEST","HICP EZ",4, "monthly"),
    ],
    # ── ALEMANHA ─────────────────────────────────────────────
    "DE_GROWTH": [
        ("CLVMNACSCAB1GQDE","GDP DE",   4, "quarterly"),
        ("DEUPROINDQISMEI", "IP DE",    3, "monthly"),
    ],
    "DE_INFLATION": [
        ("DEUCPIALLMINMEI","CPI DE",    3, "monthly"),
    ],
    # ── FRANÇA ───────────────────────────────────────────────
    "FR_GROWTH": [
        ("CLVMNACSCAB1GQFR","GDP FR",   4, "quarterly"),
        ("FRAPROINDQISMEI", "IP FR",    3, "monthly"),
    ],
    "FR_INFLATION": [
        ("FRACPIALLMINMEI","CPI FR",    3, "monthly"),
    ],
    # ── UK ───────────────────────────────────────────────────
    "GB_GROWTH": [
        # CLVMNACSCAB1GQUK REMOVIDO — série DESCONTINUADA na FRED: última
        # observação 2020-07-01 (rebound COVID), last_updated 2021-02. O QoQ
        # do ressalto COVID dava accel +12 (capado a +10) → "crescimento forte"
        # fake → UK preso em Q1. (Os pares DE/FR/IT/ES usam CLVMNACSCAB1GQxx
        # que continuam VIVOS até Q1-2026; só o do UK morreu.)
        # Substituído pelo real GDP vivo + IP mensal (mesmo padrão dos pares).
        ("NGDPRSAXDCGBQ",   "GDP UK",   4, "quarterly"),  # real GDP SA, fresco Q1-2026
        ("GBRPROINDMISMEI", "IP UK",    3, "monthly"),     # IP mensal; [:3]=GBR → refresh OECD-direct (radar)
    ],
    "GB_INFLATION": [
        ("GBRCPIALLMINMEI","CPI UK",    3, "monthly"),
    ],
    # ── JAPÃO ────────────────────────────────────────────────
    "JP_GROWTH": [
        ("JPNRGDPEXP",      "GDP JP",   4, "quarterly"),
        ("JPNPROINDQISMEI", "IP JP",    3, "monthly"),
    ],
    "JP_INFLATION": [
        ("JPNCPIALLMINMEI","CPI JP",    3, "monthly"),
    ],
    # ── CANADÁ ───────────────────────────────────────────────
    "CA_GROWTH": [
        # CLVMNACSCAB1GQCA REMOVIDO — série DESCONTINUADA na FRED (HTTP 400
        # "does not exist"): fred_get devolvia None → CA corria só com IP, sem o
        # sinal de GDP que os pares europeus têm (degradado, não lixo). Substituído
        # pelo real GDP vivo (mesma família NGDPRSAXDCxx do fix UK), fresco Q1-2026.
        ("NGDPRSAXDCCAQ",   "GDP CA",   4, "quarterly"),  # real GDP SA, last_updated 2026-05-11
        ("CANPROINDQISMEI", "IP CA",    3, "monthly"),
    ],
    "CA_INFLATION": [
        ("CANCPIALLMINMEI","CPI CA",    3, "monthly"),
    ],
    # ── AUSTRÁLIA ────────────────────────────────────────────
    "AU_GROWTH": [
        ("AUSGDPNADSMEI",   "GDP AU",   4, "quarterly"),
        ("AUSPROINDQISMEI", "IP AU",    3, "monthly"),
    ],
    "AU_INFLATION": [
        ("AUSCPIALLQINMEI","CPI AU",    3, "quarterly"),
    ],
    # ── CHINA ────────────────────────────────────────────────
    "CN_GROWTH": [
        ("CHNGDPNQDSMEI",   "GDP CN",   4, "quarterly"),
    ],
    "CN_INFLATION": [
        ("CHNCPIALLMINMEI","CPI CN",    3, "monthly"),
    ],
    # ── CORÉIA ───────────────────────────────────────────────
    "KR_GROWTH": [
        # CLVMNACSCAB1GQKR REMOVIDO — série DESCONTINUADA na FRED (HTTP 400
        # "does not exist"): fred_get devolvia None → KR corria só com IP.
        # Substituído pelo real GDP vivo (mesma família NGDPRSAXDCxx), fresco Q1-2026.
        ("NGDPRSAXDCKRQ",   "GDP KR",  4, "quarterly"),  # real GDP SA, last_updated 2026-04-27
        ("KORPROINDQISMEI", "IP KR",   3, "monthly"),
    ],
    "KR_INFLATION": [
        ("KORCPIALLMINMEI","CPI KR",   3, "monthly"),
    ],
    # ── ITÁLIA ───────────────────────────────────────────────
    "IT_GROWTH": [
        ("CLVMNACSCAB1GQIT","GDP IT",  4, "quarterly"),
        ("ITAPROINDQISMEI", "IP IT",   3, "monthly"),
    ],
    "IT_INFLATION": [
        ("ITACPIALLMINMEI","CPI IT",   3, "monthly"),
    ],
    # ── ESPANHA ──────────────────────────────────────────────
    "ES_GROWTH": [
        ("CLVMNACSCAB1GQES","GDP ES",  4, "quarterly"),
        ("ESPPROINDQISMEI", "IP ES",   3, "monthly"),
    ],
    "ES_INFLATION": [
        ("ESPNHICP","HICP ES",         3, "monthly"),
    ],
    # ── PAÍSES BAIXOS ────────────────────────────────────────
    "NL_GROWTH": [
        ("CLVMNACSCAB1GQNL","GDP NL",  4, "quarterly"),
        ("NLDPROINDQISMEI", "IP NL",   3, "monthly"),
    ],
    "NL_INFLATION": [
        ("NLDCPIALLMINMEI","CPI NL",   3, "monthly"),
    ],
    # ── SUÉCIA ───────────────────────────────────────────────
    "SE_GROWTH": [
        ("CLVMNACSCAB1GQSE","GDP SE",  4, "quarterly"),
        ("SWEPROINDQISMEI", "IP SE",   3, "monthly"),
    ],
    "SE_INFLATION": [
        ("SWECPIALLMINMEI","CPI SE",   3, "monthly"),
    ],
    # ── NORUEGA ──────────────────────────────────────────────
    "NO_GROWTH": [
        ("CLVMNACSCAB1GQNO","GDP NO",  4, "quarterly"),
        ("NORPROINDQISMEI", "IP NO",   3, "monthly"),
    ],
    "NO_INFLATION": [
        ("NORCPIALLMINMEI","CPI NO",   3, "monthly"),
    ],
    # ── POLÓNIA ──────────────────────────────────────────────
    "PL_GROWTH": [
        ("CLVMNACSCAB1GQPL","GDP PL",  4, "quarterly"),
        ("POLPROINDQISMEI", "IP PL",   3, "monthly"),
    ],
    "PL_INFLATION": [
        ("POLCPIALLMINMEI","CPI PL",   3, "monthly"),
    ],
    # ── SUÍÇA ────────────────────────────────────────────────
    "CH_GROWTH": [
        ("CLVMNACSCAB1GQCH","GDP CH",  4, "quarterly"),
        ("CHEPROINDQISMEI", "IP CH",   3, "monthly"),
    ],
    "CH_INFLATION": [
        ("CHECPIALLMINMEI","CPI CH",   3, "monthly"),
    ],
}

# ── ECONOMIAS ────────────────────────────────────────────────
ECONOMIES = [
    {"code":"US","name":"United States",  "flag":"🇺🇸","region":"Americas",     "markets":["NASDAQ","NYSE"],"etf":"SPY",   "rate_fred":"DFF"},
    {"code":"CA","name":"Canada",         "flag":"🇨🇦","region":"Americas",     "markets":["TSX"],          "etf":"EWC",   "rate_fred":None},
    {"code":"EZ","name":"Eurozone",       "flag":"🇪🇺","region":"Eurozone",     "markets":["multi-EU"],     "etf":"EXS1.DE","rate_fred":"ECBDFR"},
    {"code":"DE","name":"Germany",        "flag":"🇩🇪","region":"Eurozone",     "markets":["XETRA"],        "etf":"EWG",   "rate_fred":None},
    {"code":"FR","name":"France",         "flag":"🇫🇷","region":"Eurozone",     "markets":["XPAR"],         "etf":"EWQ",   "rate_fred":None},
    {"code":"IT","name":"Italy",          "flag":"🇮🇹","region":"Eurozone",     "markets":["XMIL"],         "etf":"EWI",   "rate_fred":None},
    {"code":"ES","name":"Spain",          "flag":"🇪🇸","region":"Eurozone",     "markets":["XMAD"],         "etf":"EWP",   "rate_fred":None},
    {"code":"NL","name":"Netherlands",    "flag":"🇳🇱","region":"Eurozone",     "markets":["XAMS"],         "etf":"EWN",   "rate_fred":None},
    {"code":"PT","name":"Portugal",       "flag":"🇵🇹","region":"Eurozone",     "markets":["XLIS"],         "etf":None,    "rate_fred":None},
    {"code":"BE","name":"Belgium",        "flag":"🇧🇪","region":"Eurozone",     "markets":["XBRU"],         "etf":None,    "rate_fred":None},
    {"code":"IE","name":"Ireland",        "flag":"🇮🇪","region":"Eurozone",     "markets":["XDUB"],         "etf":None,    "rate_fred":None},
    {"code":"AT","name":"Austria",        "flag":"🇦🇹","region":"Eurozone",     "markets":["XWBO"],         "etf":None,    "rate_fred":None},
    {"code":"FI","name":"Finland",        "flag":"🇫🇮","region":"Eurozone",     "markets":["XHEL"],         "etf":None,    "rate_fred":None},
    {"code":"GR","name":"Greece",         "flag":"🇬🇷","region":"Eurozone",     "markets":["XATH"],         "etf":"GREK",  "rate_fred":None},
    {"code":"GB","name":"United Kingdom", "flag":"🇬🇧","region":"Europe",       "markets":["LSE"],          "etf":"EWU",   "rate_fred":"BOERUKM"},
    {"code":"CH","name":"Switzerland",    "flag":"🇨🇭","region":"Europe",       "markets":["SWX"],          "etf":"EWL",   "rate_fred":None},
    {"code":"SE","name":"Sweden",         "flag":"🇸🇪","region":"Europe",       "markets":["XSTO"],         "etf":"EWD",   "rate_fred":None},
    {"code":"DK","name":"Denmark",        "flag":"🇩🇰","region":"Europe",       "markets":["XCSE"],         "etf":None,    "rate_fred":None},
    {"code":"NO","name":"Norway",         "flag":"🇳🇴","region":"Europe",       "markets":["XOSL"],         "etf":"ENOR",  "rate_fred":None},
    {"code":"PL","name":"Poland",         "flag":"🇵🇱","region":"Europe",       "markets":["XWAR"],         "etf":"EPOL",  "rate_fred":None},
    {"code":"CZ","name":"Czech Republic", "flag":"🇨🇿","region":"Europe",       "markets":["XPRA"],         "etf":None,    "rate_fred":None},
    {"code":"JP","name":"Japan",          "flag":"🇯🇵","region":"Asia-Pacific", "markets":["TSE"],          "etf":"EWJ",   "rate_fred":"IRSTCI01JPM156N"},
    {"code":"CN","name":"China",          "flag":"🇨🇳","region":"Asia-Pacific", "markets":["HKEX"],         "etf":"MCHI",  "rate_fred":None},
    {"code":"AU","name":"Australia",      "flag":"🇦🇺","region":"Asia-Pacific", "markets":["ASX"],          "etf":"EWA",   "rate_fred":"IRSTCI01AUM156N"},
    {"code":"KR","name":"South Korea",    "flag":"🇰🇷","region":"Asia-Pacific", "markets":["KRX"],          "etf":"EWY",   "rate_fred":None},
    {"code":"SG","name":"Singapore",      "flag":"🇸🇬","region":"Asia-Pacific", "markets":["SGX"],          "etf":"EWS",   "rate_fred":None},
    {"code":"IN","name":"India",          "flag":"🇮🇳","region":"Asia-Pacific", "markets":["NSE"],          "etf":"INDA",  "rate_fred":None},
]

# ── FRED FETCH ────────────────────────────────────────────────
def fred_get(series_id, limit=48):
    try:
        r = requests.get(FRED_BASE, params={
            "series_id":        series_id,
            "api_key":          FRED_API_KEY,
            "file_type":        "json",
            "sort_order":       "desc",
            "observation_start":"2018-01-01",
            "limit":            limit,
        }, timeout=12)
        if r.status_code != 200: return None
        obs = r.json().get("observations", [])
        if not obs: return None
        df = pd.DataFrame(obs)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)
    except: return None

# ── ACELERAÇÃO DO INDICADOR ───────────────────────────────────
def calc_indicator_accel(df, freq="monthly"):
    """
    1) Calcula o ROC do indicador (YoY% para monthly, QoQ% para quarterly)
    2) Calcula a ACELERAÇÃO (T) = ROC(T) - ROC(T-1)    ← define o Quad
    3) Calcula a ACELERAÇÃO (T-1) = ROC(T-1) - ROC(T-2) ← para ROC do score composto

    Retorna: (roc_atual, accel_t, accel_t1, nivel_atual)
    accel_t  = aceleração actual (usada no score composto)
    accel_t1 = aceleração anterior (usada para calcular ROC do score composto)
    """
    try:
        v  = df["value"].values.astype(float)
        lv = float(v[-1])

        if freq == "monthly":
            # Aceleração SUAVIZADA a 3 meses (= radar quad_countries + forecast).
            # 1 mês isolado é demasiado ruidoso perto de inflexões e faz o badge
            # gritar "FORTE Q2" num simples ressalto. A média 3m é a 2ª derivada
            # honesta: accel = (YoY_t - YoY_{t-3}) / 3.
            if len(v) < 18: return None, None, None, lv
            def _yoy(k):
                base = v[-k-12]
                return (v[-k]-base)/abs(base)*100 if base != 0 else 0.0
            yoy_t  = _yoy(1)
            accel_t  = round((_yoy(1) - _yoy(4)) / 3.0, 4)   # média accel últimos 3m
            accel_t1 = round((_yoy(2) - _yoy(5)) / 3.0, 4)   # janela 3m anterior
            roc      = round(yoy_t, 4)

        elif freq == "quarterly":
            if len(v) < 7: return None, None, None, lv
            qoq_t   = (v[-1]-v[-5])/abs(v[-5])*100 if v[-5]!=0 else 0
            qoq_t1  = (v[-2]-v[-6])/abs(v[-6])*100 if v[-6]!=0 else 0
            qoq_t2  = (v[-3]-v[-7])/abs(v[-7])*100 if len(v)>=7 and v[-7]!=0 else qoq_t1
            accel_t  = round(qoq_t  - qoq_t1, 4)
            accel_t1 = round(qoq_t1 - qoq_t2, 4)
            roc      = round(qoq_t, 4)

        else:  # daily
            if len(v) < 6: return None, None, None, lv
            roc      = round((v[-1]-v[-22])/abs(v[-22])*100, 4) if v[-22]!=0 else 0
            accel_t  = round(v[-1]-v[-2], 4)
            accel_t1 = round(v[-2]-v[-3], 4) if len(v)>=3 else accel_t

        # ── GUARDA DURA ANTI-LIXO ─────────────────────────────
        # Uma aceleração (2ª derivada) > ±CAP pontos é quase sempre uma série
        # malformada: taxa tratada como nível, revisão, mudança de unidade ou
        # série trimestral processada como mensal. Protege cestos FINOS (UK, China,
        # 1-2 indicadores) onde a winsorização do score (que exige ≥3) não aplica.
        CAP = 10.0
        if accel_t  is not None: accel_t  = round(max(-CAP, min(CAP, accel_t)),  4)
        if accel_t1 is not None: accel_t1 = round(max(-CAP, min(CAP, accel_t1)), 4)
        return roc, accel_t, accel_t1, lv
    except: return None, None, None, None

# ── COMPOSITE SCORE ───────────────────────────────────────────
def calc_composite_score(indicators_data):
    """
    Score composto ponderado das acelerações.
    > 0 = aceleração líquida positiva (up para este lado do Quad)
    < 0 = aceleração líquida negativa (down)

    Também calcula o score do período anterior para determinar
    o ROC do score composto (2ª derivada do score):
    score_roc > 0 = aceleração a aumentar (quad a consolidar)
    score_roc < 0 = aceleração a diminuir (quad late, transição próxima)
    """
    # ── WINSORIZAÇÃO ROBUSTA (anti-outlier) ───────────────────
    # Indicadores macro têm escalas MUITO diferentes (Durable Goods oscila ±15pp,
    # CPI ±0.5pp). Numa média crua, o mais volátil (ou uma série malformada)
    # sequestra o regime. Cortamos cada aceleração à banda mediana ± 3·MAD
    # (com piso), para o score reflectir a AMPLITUDE do sinal, não o outlier.
    def _median(xs):
        s = sorted(xs); n = len(s)
        if n == 0: return 0.0
        m = n // 2
        return s[m] if n % 2 else (s[m-1] + s[m]) / 2.0

    raw_t = [it[2] for it in indicators_data if it[2] is not None]
    if len(raw_t) >= 3:
        med  = _median(raw_t)
        mad  = _median([abs(x - med) for x in raw_t])
        span = max(3.0 * 1.4826 * mad, 2.0)   # piso 2.0 evita cortar sinal legítimo
        lo, hi = med - span, med + span
    else:
        lo, hi = float("-inf"), float("inf")

    def _clip(x):
        if x is None: return None
        return min(max(x, lo), hi)

    w_sum_t  = 0.0   # aceleração actual
    w_sum_t1 = 0.0   # aceleração anterior
    total_w  = 0.0
    details  = []

    for item in indicators_data:
        name, roc, accel_t, accel_t1, level, weight = item
        a_t  = _clip(accel_t)    # winsorizado p/ o SCORE
        a_t1 = _clip(accel_t1)
        if a_t is not None:
            w_sum_t  += a_t  * weight
            total_w  += weight
        if a_t1 is not None:
            w_sum_t1 += a_t1 * weight
        details.append({
            "name":     name,
            "roc":      roc,
            "accel":    accel_t,    # valor REAL no display (transparência)
            "accel_t1": accel_t1,
            "level":    level,
            "weight":   weight,
        })

    if total_w == 0:
        return None, None, None, details

    # Clamp final de higiene: um score composto saudável vive em ~±1. Valores
    # além de ±SC indicam dados maus do país (não foram apanhados pelo cap por
    # cesto fino). Limitamos para não exibir magnitudes/fases absurdas.
    SC = 3.0
    score      = round(max(-SC, min(SC, w_sum_t  / total_w)), 4)
    score_prev = round(max(-SC, min(SC, w_sum_t1 / total_w)), 4)
    score_roc  = round(score - score_prev, 4)   # ROC do score composto

    return score, score_prev, score_roc, details

# ── CLASSIFY QUAD ─────────────────────────────────────────────
def classify_quad(g_score, i_score):
    """
    Quad determinado pelo SINAL do score composto de acelerações.
    g_score > 0 = crescimento a acelerar (Growth ↑)
    i_score > 0 = inflação a acelerar   (Inflation ↑)
    """
    if g_score is None or i_score is None: return 0
    if g_score >  0 and i_score <= 0: return 1
    if g_score >  0 and i_score >  0: return 2
    if g_score <= 0 and i_score >  0: return 3
    return 4

# ── QUAD PHASE ────────────────────────────────────────────────
def quad_phase(g_score, i_score, g_score_roc, i_score_roc, quad_num):
    """
    Fase não-linear dentro do Quad.

    Usa TRÊS camadas:
    1. Sinal do score → determina o Quad actual
    2. Magnitude do score → intensidade (fraco/forte)
    3. ROC do score (2ª derivada) → fase na curva:
       - g_score_roc > 0 = aceleração do crescimento a aumentar → quad a consolidar
       - g_score_roc < 0 = aceleração do crescimento a DIMINUIR → mesmo com g_score>0
                           o Quad vai enfraquecer → LATE stage
    """
    if quad_num == 0 or g_score is None or i_score is None:
        return "AGUARDA", "#94a3b8"

    c  = QUAD_PLAYBOOK[quad_num]["color"]
    gs = g_score; is_ = i_score
    gr = g_score_roc or 0  # ROC do score composto de crescimento
    ir = i_score_roc or 0  # ROC do score composto de inflação

    # ── INFLEXÃO: scores próximos de zero ────────────────────
    near_g = abs(gs) < 0.05
    near_i = abs(is_) < 0.05
    if near_g and near_i:
        return "⚠️ INFLEXÃO TOTAL — transição iminente", "#f97316"

    # ── LATE: score positivo/negativo MAS ROC contrário ──────
    # Este é o sinal não-linear chave:
    # O Quad ainda está activo MAS a 2ª derivada diz que vai acabar

    if quad_num == 1:  # G↑ I↓
        # LATE se crescimento a desacelerar (gr<0) mas ainda positivo
        if gs > 0 and gr < -0.02:
            return f"⚠️ LATE Q1 G+ROC- ({gs:+.3f} Δ{gr:+.3f})", "#f97316"
        # LATE se inflação a subir de volta (ir>0) mas ainda negativa
        if is_ < 0 and ir > 0.02:
            return f"⚠️ LATE Q1 I-ROC+ ({is_:+.3f} Δ{ir:+.3f})", "#f97316"
        if near_g: return f"⚠️ LATE Q1 G≈0", "#f97316"
        if near_i: return f"⚠️ LATE Q1 I≈0", "#f97316"
        if gs > 0.2 and gr >= 0:  return f"FORTE Q1 ({gs:+.3f}↗)", c
        return f"Q1 ({gs:+.3f}/{is_:+.3f})", c

    if quad_num == 2:  # G↑ I↑
        # LATE→Q3: crescimento a desacelerar
        if gs > 0 and gr < -0.02:
            return f"⚠️ LATE Q2→Q3 G+ROC- ({gs:+.3f} Δ{gr:+.3f})", "#f97316"
        # LATE→Q1: inflação a desacelerar
        if is_ > 0 and ir < -0.02:
            return f"⚠️ LATE Q2→Q1 I+ROC- ({is_:+.3f} Δ{ir:+.3f})", "#15803d"
        if near_g: return f"⚠️ LATE Q2 G≈0", "#f97316"
        if near_i: return f"⚠️ LATE Q2 I≈0", "#15803d"
        if gs > 0.2 and is_ > 0.2 and gr >= 0 and ir >= 0:
            return f"FORTE Q2 ({gs:+.3f}/{is_:+.3f})", c
        return f"Q2 ({gs:+.3f}/{is_:+.3f})", c

    if quad_num == 3:  # G↓ I↑
        # LATE→Q4: inflação a desacelerar
        if is_ > 0 and ir < -0.02:
            return f"⚠️ LATE Q3→Q4 I+ROC- ({is_:+.3f} Δ{ir:+.3f})", "#ef4444"
        # LATE→Q2: crescimento a recuperar
        if gs < 0 and gr > 0.02:
            return f"⚠️ LATE Q3→Q2 G-ROC+ ({gs:+.3f} Δ{gr:+.3f})", "#4ade80"
        if near_g: return f"⚠️ LATE Q3 G≈0", "#fbbf24"
        if near_i: return f"⚠️ LATE Q3 I≈0", "#ef4444"
        if abs(gs) > 0.2 and abs(is_) > 0.2:
            return f"DEEP Q3 STAG ({gs:+.3f}/{is_:+.3f})", c
        return f"Q3 ({gs:+.3f}/{is_:+.3f})", c

    if quad_num == 4:  # G↓ I↓
        # LATE→Q1: crescimento a recuperar (sinal mais bullish)
        if gs < 0 and gr > 0.02:
            return f"⚠️ LATE Q4→Q1 G-ROC+ ({gs:+.3f} Δ{gr:+.3f})", "#15803d"
        # Deflação a piorar
        if is_ < 0 and ir < -0.02:
            return f"⚠️ DEEP Q4 DEFLAÇÃO ({is_:+.3f} Δ{ir:+.3f})", "#ef4444"
        if near_g: return f"⚠️ LATE Q4 G≈0", "#fbbf24"
        if near_i: return f"⚠️ LATE Q4 I≈0", "#fbbf24"
        if abs(gs) > 0.2 and abs(is_) > 0.2:
            return f"DEEP Q4 RECESSÃO ({gs:+.3f}/{is_:+.3f})", c
        return f"Q4 ({gs:+.3f}/{is_:+.3f})", c

    return f"Q{quad_num}", c

# ── ETF PROXY ─────────────────────────────────────────────────
def etf_accel_proxy(etf_sym):
    """Proxy de aceleração via ETF quando sem dados FRED"""
    try:
        if not etf_sym: return None, None
        df = yf.download(etf_sym,
                         start=(datetime.today()-timedelta(days=400)).strftime("%Y-%m-%d"),
                         end=datetime.today().strftime("%Y-%m-%d"),
                         progress=False, auto_adjust=True)
        if df.empty: return None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        c = df["Close"].astype(float).values.flatten()
        if len(c) < 66: return None, None
        # ROC 3M e 6M
        roc_3m   = (c[-1]-c[-66])/c[-66]*100 if c[-66]!=0 else 0
        roc_3m_p = (c[-22]-c[-88])/c[-88]*100 if len(c)>=88 and c[-88]!=0 else 0
        accel    = round(roc_3m - roc_3m_p, 4)
        roc      = round(roc_3m, 4)
        return roc, accel
    except: return None, None

# ── ANALYSE ECONOMY ───────────────────────────────────────────
def analyse_economy(eco):
    code = eco["code"]
    key_g = f"{code}_GROWTH"
    key_i = f"{code}_INFLATION"

    growth_defs    = INDICATOR_DEFS.get(key_g, [])
    inflation_defs = INDICATOR_DEFS.get(key_i, [])

    # Fallback para EZ quando código não tem def própria
    if not growth_defs and code in ["PT","BE","IE","AT","FI","GR","DK","CZ"]:
        growth_defs    = INDICATOR_DEFS.get("EZ_GROWTH", [])
        inflation_defs = INDICATOR_DEFS.get("EZ_INFLATION", [])

    g_indicators = []
    i_indicators = []

    # ── Crescimento — cada série protegida por try/except ────
    for series_def in growth_defs:
        try:
            series_id, name, weight, freq = series_def
            df = fred_get(series_id, limit=48)

            # Para séries IP mensais (XXXPROIND...): actualizar com OECD
            # directo se o dado FRED tiver > 60 dias de atraso
            if (freq == "monthly" and "PROIND" in series_id
                    and df is not None and len(df) >= 6):
                last_obs = df["date"].max()
                if (pd.Timestamp.today() - last_obs).days > 60:
                    iso3 = series_id[:3]        # "KOR", "JPN", "CAN"…
                    df_oecd = _oecd_ip_fresh(iso3)
                    if (df_oecd is not None
                            and df_oecd["date"].max() > last_obs):
                        df   = df_oecd
                        name = f"{name} [OECD↑]"

            if df is not None and len(df) >= 6:
                result_accel = calc_indicator_accel(df, freq)
                if result_accel and result_accel[0] is not None:
                    roc, accel_t, accel_t1, level = result_accel
                    g_indicators.append((name, roc, accel_t, accel_t1, level, weight))
        except Exception:
            continue

    # ── Inflação — cada série protegida por try/except ───────
    for series_def in inflation_defs:
        try:
            series_id, name, weight, freq = series_def
            df = fred_get(series_id, limit=48)
            if df is not None and len(df) >= 6:
                result_accel = calc_indicator_accel(df, freq)
                if result_accel and result_accel[0] is not None:
                    roc, accel_t, accel_t1, level = result_accel
                    i_indicators.append((name, roc, accel_t, accel_t1, level, weight))
        except Exception:
            continue

    # ── Fallback ETF proxy ────────────────────────────────────
    has_g = len(g_indicators) > 0
    has_i = len(i_indicators) > 0
    data_quality = "FRED" if (has_g or has_i) else "SEM DADOS"

    if not has_g:
        try:
            etf_sym = eco.get("etf")
            if etf_sym:
                etf_roc, etf_accel = etf_accel_proxy(etf_sym)
                if etf_accel is not None:
                    g_indicators.append((
                        f"ETF {etf_sym}", etf_roc, etf_accel, None, None, 1
                    ))
                    data_quality = "ETF PROXY"
        except Exception:
            pass

    if not has_i:
        if data_quality == "FRED":
            data_quality = "PARCIAL (sem inflação)"

    # ── Scores compostos + ROC do score (2ª derivada) ────────
    g_score, g_score_prev, g_score_roc, g_details = calc_composite_score(g_indicators)
    i_score, i_score_prev, i_score_roc, i_details = calc_composite_score(i_indicators)

    # ── Classificação Quad ────────────────────────────────────
    qm = classify_quad(g_score, i_score)
    # Quarterly: usa GDP + PCE quarterly
    try:
        g_q_indicators = [
            (n,r,a,a1,l,w) for (n,r,a,a1,l,w) in g_indicators
            if any(x in n for x in ["GDP","Growth Rate","per Capita"])
        ]
        if g_q_indicators:
            g_score_q, _, _, _ = calc_composite_score(g_q_indicators)
        else:
            # Fallback: usa score mensal se sem dados trimestrais
            g_score_q = g_score
        i_score_q, _, _, _ = calc_composite_score(list(i_indicators))
    except Exception:
        g_score_q = g_score
        i_score_q = i_score
    qq = classify_quad(g_score_q, i_score_q)

    # Fase não-linear (usa score + ROC do score)
    try:
        phase_label, phase_color = quad_phase(g_score, i_score, g_score_roc, i_score_roc, qm)
    except Exception:
        phase_label, phase_color = "—", "#94a3b8"

    # Taxa de referência
    rate = None
    if eco.get("rate_fred"):
        df_r = fred_get(eco["rate_fred"], limit=5)
        if df_r is not None and not df_r.empty:
            rate = round(float(df_r["value"].iloc[-1]), 2)

    # CPI YoY para display
    cpi_yoy = None
    try:
        for item in i_indicators:
            n, roc = item[0], item[1]
            if "CPI" in n and roc is not None:
                cpi_yoy = roc; break
        if cpi_yoy is None:
            for item in i_indicators:
                roc = item[1]
                if roc is not None: cpi_yoy = roc; break
    except Exception:
        pass

    return {
        "code":         code,
        "name":         eco["name"],
        "flag":         eco["flag"],
        "region":       eco["region"],
        "markets":      eco["markets"],
        # Scores compostos (determinam Quad)
        "g_score":      g_score,
        "i_score":      i_score,
        "g_score_q":    g_score_q,
        "i_score_q":    i_score_q,
        # ROC dos scores compostos (2ª derivada — fase não-linear)
        "g_score_roc":  g_score_roc,   # > 0 = quad a consolidar | < 0 = late, transição
        "i_score_roc":  i_score_roc,
        "g_score_prev": g_score_prev,
        "i_score_prev": i_score_prev,
        # Quad
        "quad_m":       qm,
        "quad_m_label": QUAD_PLAYBOOK[qm]["label"],
        "quad_m_color": QUAD_PLAYBOOK[qm]["color"],
        "quad_q":       qq,
        "quad_q_label": QUAD_PLAYBOOK[qq]["label"],
        "quad_q_color": QUAD_PLAYBOOK[qq]["color"],
        # Fase
        "quad_phase":       phase_label,
        "quad_phase_color": phase_color,
        # Detalhes
        "g_details":    g_details,
        "i_details":    i_details,
        "cpi_yoy":      cpi_yoy,
        "rate":         rate,
        "data_quality": data_quality,
    }

# ── RECENT MACRO RELEASES ─────────────────────────────────────
# Verifica que dados FRED foram publicados nos últimos N dias
# e classifica o impacto no Quad (Growth vs Inflation, accel/decel)

_RELEASE_WATCHLIST = [
    # (series_id, display_name, country_code, flag, type, freq)
    # US — os mais importantes
    ("PAYEMS",               "NFP Payrolls",  "US", "🇺🇸", "growth",    "monthly"),
    ("CPIAUCSL",             "CPI",           "US", "🇺🇸", "inflation", "monthly"),
    ("CPILFESL",             "Core CPI",      "US", "🇺🇸", "inflation", "monthly"),
    ("PPIFIS",               "PPI Final",     "US", "🇺🇸", "inflation", "monthly"),
    ("PPIACO",               "PPI All Comm",  "US", "🇺🇸", "inflation", "monthly"),
    ("INDPRO",               "Prod. Ind.",    "US", "🇺🇸", "growth",    "monthly"),
    ("PCEC96",               "PCE Real",      "US", "🇺🇸", "growth",    "monthly"),
    ("UMCSENT",              "Michigan Sent", "US", "🇺🇸", "growth",    "monthly"),
    ("GDPC1",                "GDP Real",      "US", "🇺🇸", "growth",    "quarterly"),
    ("A191RL1Q225SBEA",      "GDP Growth%",   "US", "🇺🇸", "growth",    "quarterly"),
    ("RETAILSMNSA",          "Retail Sales",  "US", "🇺🇸", "growth",    "monthly"),
    ("DGORDER",              "Durable Goods", "US", "🇺🇸", "growth",    "monthly"),
    ("T10YIE",               "Breakeven 10Y", "US", "🇺🇸", "inflation", "daily"),
    # Eurozona
    ("CP0000EZ19M086NEST",   "HICP",          "EZ", "🇪🇺", "inflation", "monthly"),
    ("CLVMNACSCAB1GQEA",     "GDP",           "EZ", "🇪🇺", "growth",    "quarterly"),
    ("EUGLORMAN",            "Prod. Ind.",    "EZ", "🇪🇺", "growth",    "monthly"),
    # Alemanha
    ("DEUCPIALLMINMEI",      "CPI",           "DE", "🇩🇪", "inflation", "monthly"),
    ("DEUPROINDQISMEI",      "Prod. Ind.",    "DE", "🇩🇪", "growth",    "monthly"),
    ("CLVMNACSCAB1GQDE",     "GDP",           "DE", "🇩🇪", "growth",    "quarterly"),
    # França
    ("FRACPIALLMINMEI",      "CPI",           "FR", "🇫🇷", "inflation", "monthly"),
    ("FRAPROINDQISMEI",      "Prod. Ind.",    "FR", "🇫🇷", "growth",    "monthly"),
    # UK
    ("GBRCPIALLMINMEI",      "CPI",           "UK", "🇬🇧", "inflation", "monthly"),
    ("GBRPROINDMISMEI",      "Prod. Ind.",    "UK", "🇬🇧", "growth",    "monthly"),
    ("NGDPRSAXDCGBQ",        "GDP",           "UK", "🇬🇧", "growth",    "quarterly"),
    # Japão
    ("JPNCPIALLMINMEI",      "CPI",           "JP", "🇯🇵", "inflation", "monthly"),
    ("JPNPROINDQISMEI",      "Prod. Ind.",    "JP", "🇯🇵", "growth",    "monthly"),
    # China
    ("CHNCPIALLMINMEI",      "CPI",           "CN", "🇨🇳", "inflation", "monthly"),
    # Coreia
    ("KORCPIALLMINMEI",      "CPI",           "KR", "🇰🇷", "inflation", "monthly"),
    ("KORPROINDQISMEI",      "Prod. Ind.",    "KR", "🇰🇷", "growth",    "monthly"),
    ("NGDPRSAXDCKRQ",        "GDP",           "KR", "🇰🇷", "growth",    "quarterly"),
    # Canadá
    ("CANCPIALLMINMEI",      "CPI",           "CA", "🇨🇦", "inflation", "monthly"),
    ("CANPROINDQISMEI",      "Prod. Ind.",    "CA", "🇨🇦", "growth",    "monthly"),
    ("NGDPRSAXDCCAQ",        "GDP",           "CA", "🇨🇦", "growth",    "quarterly"),
    # Austrália
    ("AUSCPIALLQINMEI",      "CPI",           "AU", "🇦🇺", "inflation", "quarterly"),
    # Espanha
    ("ESPNHICP",             "HICP",          "ES", "🇪🇸", "inflation", "monthly"),
    # Itália
    ("ITACPIALLMINMEI",      "CPI",           "IT", "🇮🇹", "inflation", "monthly"),
]

FRED_SERIES_META_URL = "https://api.stlouisfed.org/fred/series"

def _fred_last_updated(series_id):
    """
    Retorna (last_updated_date, obs_date_latest) via metadados FRED.
    last_updated = data em que FRED publicou dados novos (data de release real)
    Usa fred/series endpoint que devolve last_updated: "2026-05-13 07:48:05-05"
    """
    try:
        r = requests.get(FRED_SERIES_META_URL, params={
            "series_id": series_id,
            "api_key":   FRED_API_KEY,
            "file_type": "json",
        }, timeout=10)
        if r.status_code != 200:
            return None
        seriess = r.json().get("seriess", [])
        if not seriess:
            return None
        lu = seriess[0].get("last_updated", "")
        if not lu:
            return None
        # Format: "2026-05-13 07:48:05-05"
        from datetime import date as _d
        return _d.fromisoformat(lu[:10])
    except Exception:
        return None


def check_recent_macro_releases(days_back=14):
    """
    Verifica que dados FRED foram publicados nos últimos N dias.

    NOTA IMPORTANTE: usa `last_updated` dos metadados FRED (data de publicação real)
    e NÃO a `observation_date` (que é a data do período — ex: 2026-04-01 para CPI Abril).
    Assim, CPI de Abril publicado a 13 de Maio aparece como 'há 14 dias' não 'há 56 dias'.

    Retorna lista ordenada por recência (mais recente primeiro).
    """
    from datetime import date as _date
    today   = _date.today()
    cutoff  = today - timedelta(days=days_back)
    results = []

    for series_id, name, country, flag, ind_type, freq in _RELEASE_WATCHLIST:
        try:
            # ── 1. Verifica data de publicação real (last_updated) ─
            last_updated = _fred_last_updated(series_id)
            if last_updated is None or last_updated < cutoff:
                continue   # não publicado recentemente

            days_ago = (today - last_updated).days

            # ── 2. Busca observações para calcular YoY ────────────
            lim = 16 if freq == "monthly" else (8 if freq == "quarterly" else 30)
            df  = fred_get(series_id, limit=lim)
            if df is None or len(df) < 2:
                continue

            v          = df["value"].values.astype(float)
            latest_val = float(v[-1])
            prev_val   = float(v[-2])
            obs_date   = str(df["date"].iloc[-1].date())   # período (ex: "2026-04-01")

            # ── 3. YoY e Aceleração ───────────────────────────────
            yoy = yoy_prev = accel = None

            if freq == "monthly" and len(v) >= 14:
                yoy      = (v[-1]-v[-13])/abs(v[-13])*100 if v[-13] != 0 else 0.0
                yoy_prev = (v[-2]-v[-14])/abs(v[-14])*100 if v[-14] != 0 else 0.0
                accel    = round(yoy - yoy_prev, 3)
                yoy      = round(yoy, 2)
                yoy_prev = round(yoy_prev, 2)

            elif freq == "quarterly" and len(v) >= 6:
                yoy      = (v[-1]-v[-5])/abs(v[-5])*100 if v[-5] != 0 else 0.0
                yoy_prev = (v[-2]-v[-6])/abs(v[-6])*100 if v[-6] != 0 else 0.0
                accel    = round(yoy - yoy_prev, 3)
                yoy      = round(yoy, 2)
                yoy_prev = round(yoy_prev, 2)

            else:   # daily / dados insuficientes → variação absoluta
                yoy      = round((latest_val - prev_val) / abs(prev_val) * 100, 2) \
                            if prev_val != 0 else 0.0
                yoy_prev = None
                accel    = round(latest_val - prev_val, 3)

            if accel is None:
                accel = 0.0

            # ── 4. Classificação de impacto no Quad ───────────────
            if ind_type == "inflation":
                if accel > 0.05:
                    quad_signal  = "inflation ↑ → pressão Q2/Q3"
                    signal_color = "#f97316"
                    signal_icon  = "\U0001f53a"   # 🔺
                elif accel < -0.05:
                    quad_signal  = "inflation ↓ → favorece Q1/Q4"
                    signal_color = "#4ade80"
                    signal_icon  = "\U0001f53b"   # 🔻
                else:
                    quad_signal  = "inflation → estável"
                    signal_color = "#94a3b8"
                    signal_icon  = "→"
            else:   # growth
                if accel > 0.05:
                    quad_signal  = "growth ↑ → favorece Q1/Q2"
                    signal_color = "#4ade80"
                    signal_icon  = "\U0001f53a"   # 🔺
                elif accel < -0.05:
                    quad_signal  = "growth ↓ → pressão Q3/Q4"
                    signal_color = "#ef4444"
                    signal_icon  = "\U0001f53b"   # 🔻
                else:
                    quad_signal  = "growth → estável"
                    signal_color = "#94a3b8"
                    signal_icon  = "→"

            results.append({
                "series":        series_id,
                "name":          name,
                "country":       country,
                "flag":          flag,
                "type":          ind_type,
                "freq":          freq,
                "release_date":  str(last_updated),   # data de publicação real
                "obs_date":      obs_date,             # período de referência
                "days_ago":      days_ago,
                "latest_val":    latest_val,
                "prev_val":      prev_val,
                "yoy":           yoy,
                "yoy_prev":      yoy_prev,
                "accel":         accel,
                "quad_signal":   quad_signal,
                "signal_color":  signal_color,
                "signal_icon":   signal_icon,
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["days_ago"])
    return results


# ── RUN ───────────────────────────────────────────────────────
def analyse_macro_indicators():
    print(f"\n{'='*60}")
    print(f"  GLOBAL MACRO v4 — {RUN_DATE}")
    print(f"  Aceleração agregada · {len(ECONOMIES)} economias")
    print(f"  Growth: GDP+PCE+IP+Payroll · Inflation: PPI+CPI+CoreCPI")
    print("="*60)

    def sf(v, fmt='+.3f'): return format(v, fmt) if v is not None else '—'
    eco_results = []
    for eco in ECONOMIES:
        try:
            print(f"  {eco['flag']} {eco['name']:20}", end="", flush=True)
            r = analyse_economy(eco)
            eco_results.append(r)
            gs = r["g_score"]; is_ = r["i_score"]
            ql = r["quad_m_label"]
            gs_str = f"{gs:+.3f}" if gs is not None else "—"
            is_str = f"{is_:+.3f}" if is_ is not None else "—"
            print(f"  G:{gs_str}  I:{is_str}  → {ql}  [{r['data_quality']}]")
        except Exception as e:
            print(f"  ⚠️  {e}")
            eco_results.append({
                "code":eco["code"],"name":eco["name"],"flag":eco["flag"],
                "region":eco["region"],"markets":eco.get("markets",[]),
                "g_score":None,"i_score":None,"g_score_q":None,"i_score_q":None,
                "quad_m":0,"quad_m_label":"ERRO","quad_m_color":"#475569",
                "quad_q":0,"quad_q_label":"ERRO","quad_q_color":"#475569",
                "quad_phase":"ERRO","quad_phase_color":"#475569",
                "g_details":[],"i_details":[],"cpi_yoy":None,"rate":None,
                "data_quality":"ERRO",
            })

    us = next((r for r in eco_results if r["code"]=="US"), {})
    print(f"\n  🇺🇸 US  Quad M: {us.get('quad_m_label','—')}  "
          f"G:{sf(us.get('g_score'))}  I:{sf(us.get('i_score'))}")
    print(f"  🇺🇸 US  Quad Q: {us.get('quad_q_label','—')}  "
          f"G:{sf(us.get('g_score_q'))}  I:{sf(us.get('i_score_q'))}")

    quad_m_int = us.get("quad_m", 0)
    pb_us      = QUAD_PLAYBOOK.get(quad_m_int, QUAD_PLAYBOOK[0])
    return {
        "economies":   eco_results,
        "quad_label":  us.get("quad_m_label","—"),
        "quad_color":  us.get("quad_m_color","#94a3b8"),
        "quad_us":     quad_m_int,
        "quad_action": pb_us["action"],
        "quad_best":   pb_us.get("highlights", []),
        "quad_worst":  pb_us.get("avoid_highlights", []),
    }

# ── GENERATE HTML ─────────────────────────────────────────────
def generate_macro_html(macro):
    if not macro or not macro.get("economies"):
        return """<div class="section"><div class="section-title">MACRO</div>
                  <div style="color:#475569;padding:30px;text-align:center">
                  Sem dados — verifica FRED_API_KEY em config.py</div></div>"""

    economies = macro["economies"]

    # ── Mapa global por Quad ──────────────────────────────────
    by_quad = {1:[], 2:[], 3:[], 4:[], 0:[]}
    for e in economies:
        by_quad[e.get("quad_m",0)].append(e)

    def score_bar(score, score_roc=None, max_v=0.5):
        """
        Barra visual do score composto.
        score     = aceleração composta actual (determina Quad)
        score_roc = ROC do score (2ª derivada) — indica fase
        """
        if score is None: return "<span style='color:#334155'>—</span>"
        c    = "#15803d" if score > 0.1 else "#4ade80" if score > 0 else                "#ef4444" if score < -0.1 else "#f97316"
        pct  = min(100, abs(score)/max_v*100)
        icon = "▲" if score > 0 else "▼"
        # ROC do score: seta de tendência
        roc_html = ""
        if score_roc is not None:
            rc  = "#4ade80" if score_roc > 0.005 else "#ef4444" if score_roc < -0.005 else "#94a3b8"
            ri  = "↗" if score_roc > 0.01 else "↘" if score_roc < -0.01 else "→"
            roc_html = f"<span style='color:{rc};font-size:9px;margin-left:2px' title='ROC do score: {score_roc:+.4f}'>{ri}</span>"
        return (f"<div style='display:flex;align-items:center;gap:4px'>"
                f"<span style='color:{c};font-weight:700;font-size:10px;width:58px;text-align:right'>"
                f"{icon} {score:+.3f}</span>"
                f"<div style='width:40px;height:8px;background:#1e293b;border-radius:3px;overflow:hidden'>"
                f"<div style='width:{pct:.0f}%;height:100%;background:{c};border-radius:3px'></div>"
                f"</div>{roc_html}</div>")

    def indicator_mini(details):
        """Mini display dos indicadores individuais"""
        html = ""
        for d in details[:4]:
            try:
                a = d.get("accel") if isinstance(d, dict) else None
                n = d.get("name","?") if isinstance(d, dict) else "?"
                if a is None: continue
                c = "#15803d" if a > 0.1 else "#4ade80" if a > 0 else                     "#ef4444" if a < -0.1 else "#f97316"
                icon = "▲" if a > 0 else "▼"
                html += (f"<div style='font-size:8px;color:{c};white-space:nowrap'>"
                         f"{icon} {n[:12]}: {a:+.4f}</div>")
            except Exception:
                continue
        return html or "<div style='font-size:8px;color:#334155'>sem dados</div>"

    def quad_map_card(qnum, eco_list):
        pb    = QUAD_PLAYBOOK[qnum]
        c     = pb["color"]
        flags = " ".join(e["flag"] for e in eco_list)
        codes = ", ".join(e["code"] for e in eco_list)
        n     = len(eco_list)
        late  = sum(1 for e in eco_list if "LATE" in (e.get("quad_phase") or "") or "INFLEXÃO" in (e.get("quad_phase") or ""))
        late_b= f"<span style='background:#f97316;color:#fff;font-size:8px;padding:1px 5px;border-radius:3px;margin-left:6px'>{late} ⚠️ LATE</span>" if late else ""
        return f"""
        <div style="background:{c}15;border:2px solid {c}66;border-radius:10px;padding:14px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
            <div>
              <span style="color:{c};font-size:16px;font-weight:900">{pb['label']}</span>
              <span style="color:#475569;font-size:9px;margin-left:8px">{pb['desc']} · {pb['text']}</span>
              {late_b}
            </div>
            <div style="background:{c};color:#0a0a0a;font-size:22px;font-weight:900;
                        padding:2px 12px;border-radius:6px;min-width:36px;text-align:center">{n}</div>
          </div>
          <div style="font-size:22px;margin-bottom:4px;letter-spacing:3px">{flags or '—'}</div>
          <div style="font-size:9px;color:#64748b;margin-bottom:6px">{codes or 'nenhum'}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:6px">
            <div>{''.join(f"<div style='font-size:8px;color:#4ade80'>▲ {nm} {rt}</div>" for nm,rt in pb.get('highlights',[])[:3])}</div>
            <div>{''.join(f"<div style='font-size:8px;color:#f87171'>▼ {nm} {rt}</div>" for nm,rt in pb.get('avoid_highlights',[])[:2])}</div>
          </div>
          <div style="font-size:8px;color:{c};background:{c}11;padding:5px 8px;border-radius:4px;line-height:1.4">
              {pb['action'].split('·')[0].strip()}</div>
        </div>"""

    quad_grid = f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px">
      {quad_map_card(1,by_quad[1])}{quad_map_card(2,by_quad[2])}
      {quad_map_card(3,by_quad[3])}{quad_map_card(4,by_quad[4])}
    </div>"""

    # ── US destaque ───────────────────────────────────────────
    us  = next((e for e in economies if e["code"]=="US"), None)
    us_html = ""
    if us:
        qm  = us.get("quad_m",0); qq = us.get("quad_q",0)
        pqm = QUAD_PLAYBOOK[qm];  pqq = QUAD_PLAYBOOK[qq]
        us_html = f"""
        <div style="background:#0a1628;border:2px solid #1e3a5f;border-radius:10px;
                    padding:14px;margin-bottom:14px">
          <div style="font-size:9px;color:#475569;margin-bottom:10px;font-weight:700">
              🇺🇸 UNITED STATES — DETALHE</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px">
            <div style="text-align:center">
              <div style="font-size:9px;color:#475569">QUAD MENSAL</div>
              <div style="font-size:20px;font-weight:900;color:{pqm['color']}">{pqm['label']}</div>
              <div style="font-size:9px;color:{pqm['color']}">{pqm['desc']}</div>
              <div style="font-size:9px;color:#64748b;margin-top:4px">{us.get('quad_phase','—')}</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:9px;color:#475569">QUAD TRIMESTRAL</div>
              <div style="font-size:20px;font-weight:900;color:{pqq['color']}">{pqq['label']}</div>
              <div style="font-size:9px;color:{pqq['color']}">{pqq['desc']}</div>
            </div>
            <div>
              <div style="font-size:9px;color:#475569;margin-bottom:6px">
                  GROWTH INDICATORS
                  <span style="color:#64748b;font-size:8px;margin-left:6px">
                  G Score ROC²: {f'{us.get("g_score_roc"):+.4f}' if us.get('g_score_roc') is not None else '—'}</span>
              </div>
              {indicator_mini(us.get('g_details',[]))}
              <div style="margin-top:4px">{score_bar(us.get('g_score'), us.get('g_score_roc'))}</div>
            </div>
            <div>
              <div style="font-size:9px;color:#475569;margin-bottom:6px">
                  INFLATION INDICATORS
                  <span style="color:#64748b;font-size:8px;margin-left:6px">
                  I Score ROC²: {f'{us.get("i_score_roc"):+.4f}' if us.get('i_score_roc') is not None else '—'}</span>
              </div>
              {indicator_mini(us.get('i_details',[]))}
              <div style="margin-top:4px">{score_bar(us.get('i_score'), us.get('i_score_roc'))}</div>
            </div>
          </div>
        </div>"""

    # ── Tabela por região ─────────────────────────────────────
    regions = ["Americas","Eurozone","Europe","Asia-Pacific"]
    region_tables = ""
    for region in regions:
        eco_r = [e for e in economies if e.get("region")==region]
        if not eco_r: continue
        rows = ""
        for e in eco_r:
            qmc = e.get("quad_m_color","#94a3b8")
            qqc = e.get("quad_q_color","#94a3b8")
            qml = e.get("quad_m_label","—")
            qql = e.get("quad_q_label","—")
            phase  = e.get("quad_phase","—")
            phasec = e.get("quad_phase_color","#94a3b8")
            cpi    = e.get("cpi_yoy")
            cpi_s  = f"{cpi:+.1f}%" if cpi is not None else "—"
            cpi_c  = "#ef4444" if (cpi or 0)>4 else "#f97316" if (cpi or 0)>2.5 else "#4ade80"
            rate   = e.get("rate")
            dq     = e.get("data_quality","—")
            dqc    = "#15803d" if dq=="FRED" else "#fbbf24" if "PROXY" in dq else "#475569"

            rows += f"""<tr>
              <td style="font-size:14px">{e['flag']}</td>
              <td><strong style="font-size:10px">{e['code']}</strong></td>
              <td style="color:#64748b;font-size:10px">{e['name']}</td>
              <td><span style="background:{qmc}22;color:{qmc};padding:2px 8px;
                  border-radius:4px;font-size:10px;font-weight:900">{qml}</span></td>
              <td><span style="background:{qqc}22;color:{qqc};padding:2px 8px;
                  border-radius:4px;font-size:10px;font-weight:700">{qql}</span></td>
              <td style="font-size:9px;color:{phasec}">{phase}</td>
              <td>{score_bar(e.get('g_score'), e.get('g_score_roc')) if e.get('g_score') is not None else '<span style="color:#334155">sem dados</span>'}</td>
              <td>{score_bar(e.get('i_score'), e.get('i_score_roc')) if e.get('i_score') is not None else '<span style="color:#334155">sem dados</span>'}</td>
              <td style="font-size:9px">{indicator_mini(e.get('g_details',[]))}</td>
              <td style="font-size:9px">{indicator_mini(e.get('i_details',[]))}</td>
              <td style="color:{cpi_c}">{cpi_s}</td>
              <td style="color:#94a3b8">{f'{rate:.2f}%' if rate else '—'}</td>
              <td style="font-size:8px;color:{dqc}">{dq}</td>
            </tr>"""

        region_tables += f"""
        <div style="margin-bottom:14px">
          <div style="font-size:10px;font-weight:700;color:#64748b;
                      margin-bottom:6px;letter-spacing:1px">{region.upper()}</div>
          <div class="table-wrap">
            <table>
              <tr><th></th><th>Cód</th><th>País</th>
                  <th onclick="sortTable(this)">Quad M</th>
                  <th onclick="sortTable(this)">Quad Q</th>
                  <th onclick="sortTable(this)">Fase</th>
                  <th title="G Score composto + ROC² (↗ consolida, ↘ late)">G Score ↗↘</th>
                  <th title="I Score composto + ROC² (↗ consolida, ↘ late)">I Score ↗↘</th>
                  <th title="Acelerações individuais dos indicadores de crescimento">Growth Detalhes</th>
                  <th title="Acelerações individuais dos indicadores de inflação">Inflation Detalhes</th>
                  <th onclick="sortTable(this)">CPI YoY</th>
                  <th>Taxa</th><th>Fonte</th></tr>
              {rows}
            </table>
          </div>
        </div>"""

    # ── Legenda / Playbook Summary ────────────────────────────
    legend = """<div style='margin-top:14px'>
      <div style='font-size:10px;font-weight:700;color:#64748b;margin-bottom:8px;letter-spacing:1px'>
        PLAYBOOK POR QUAD — dados reais 5 anos (SPY+TIP/IEF proxy)</div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px'>"""
    for q in [1,2,3,4]:
        pb = QUAD_PLAYBOOK[q]; c = pb["color"]
        # Highlights com percentagens reais
        hl = pb.get("highlights", [])
        ah = pb.get("avoid_highlights", [])
        hl_html = "".join(
            f"<div style='font-size:8px;color:#4ade80;white-space:nowrap'>"
            f"▲ <strong>{name}</strong> <span style='color:#86efac'>{ret}</span></div>"
            for name, ret in hl[:4]
        )
        ah_html = "".join(
            f"<div style='font-size:8px;color:#f87171;white-space:nowrap'>"
            f"▼ <strong>{name}</strong> <span style='color:#fca5a5'>{ret}</span></div>"
            for name, ret in ah[:3]
        )
        action_short = pb['action'].split('·')[0].strip()
        legend += f"""
        <div style="background:{c}12;border:2px solid {c}44;border-radius:8px;padding:10px">
          <div style="color:{c};font-weight:900;font-size:11px;margin-bottom:2px">
            {pb['label']} — {pb['text']}</div>
          <div style="color:{c}99;font-size:8px;margin-bottom:6px">{pb['desc']}</div>
          <div style="margin-bottom:4px">{hl_html}</div>
          <div style="border-top:1px solid {c}22;padding-top:4px;margin-top:2px">{ah_html}</div>
          <div style="font-size:8px;color:{c}bb;margin-top:6px;border-top:1px solid {c}22;
                      padding-top:4px;line-height:1.4">{action_short}</div>
        </div>"""
    legend += "</div></div>"

    # ── Metodologia ───────────────────────────────────────────
    method = """
    <div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:8px;
                padding:12px;margin-top:10px;font-size:9px">
      <div style="color:#38bdf8;font-weight:700;margin-bottom:6px">METODOLOGIA:</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;color:#64748b;line-height:1.6">
        <div><strong style="color:#94a3b8">1. ROC</strong> de cada indicador (YoY% mensal, QoQ% trimestral)<br>
             <strong style="color:#94a3b8">2. Aceleração</strong> = variação do ROC vs período anterior<br>
             <strong style="color:#94a3b8">3. Score composto</strong> = média ponderada das acelerações</div>
        <div><strong style="color:#94a3b8">Growth leading</strong>: GDP(w:3) + IP(w:3) + Payrolls(w:3) + PCE(w:2,lag1m) + Retail+Sentiment(w:2)<br>
             <strong style="color:#94a3b8">Inflation leading</strong>: PPI Final(w:4) + PPI All(w:3) + CPI(w:3) + Core CPI(w:3) + BE10Y(w:2)<br>
             <strong style="color:#94a3b8">Nota</strong>: PCE tem lag de 1 mês vs IP/Payrolls — peso reduzido para não distorcer ·
             <strong style="color:#f97316">↘ ROC²-</strong> = LATE stage</div>
      </div>
    </div>"""

    return f"""
    <div class="section">
      <div class="section-title">GLOBAL MACRO — HEDGEYE QUAD v4 · ACELERAÇÃO AGREGADA</div>
      <div style="color:#475569;font-size:9px;margin-bottom:12px">
        {len(economies)} economias · Quad = sinal do score composto de acelerações
        · G Score > 0 = crescimento a acelerar · I Score > 0 = inflação a acelerar
      </div>
      {us_html}
      <div style="font-size:10px;font-weight:700;color:#64748b;margin-bottom:8px">
          MAPA GLOBAL (QUAD MENSAL)</div>
      {quad_grid}
      {region_tables}
      {legend}
      {method}
    </div>"""