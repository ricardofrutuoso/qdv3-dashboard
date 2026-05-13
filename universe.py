# ============================================================
# UNIVERSE.PY — Universo completo DeGiro (~800 tickers)
# 24 bolsas | Stocks + ETFs + FX + Commodities + Vol
# ============================================================

# ── STOCKS POR BOLSA ─────────────────────────────────────────

STOCKS_US = [
    ("AAPL",  "Apple",        "NASDAQ"), ("MSFT", "Microsoft",   "NASDAQ"),
    ("NVDA",  "Nvidia",       "NASDAQ"), ("AMD",  "AMD",         "NASDAQ"),
    ("META",  "Meta",         "NASDAQ"), ("AMZN", "Amazon",      "NASDAQ"),
    ("GOOGL", "Alphabet",     "NASDAQ"), ("TSLA", "Tesla",       "NASDAQ"),
    ("INTC",  "Intel",        "NASDAQ"), ("QCOM", "Qualcomm",    "NASDAQ"),
    ("ADBE",  "Adobe",        "NASDAQ"), ("NFLX", "Netflix",     "NASDAQ"),
    ("PYPL",  "PayPal",       "NASDAQ"), ("CSCO", "Cisco",       "NASDAQ"),
    ("TXN",   "Texas Instr",  "NASDAQ"), ("AVGO", "Broadcom",    "NASDAQ"),
    ("BABA",  "Alibaba",      "NYSE"),   ("PDD",  "PDD",         "NASDAQ"),
    ("NIO",   "NIO",          "NYSE"),   ("XOM",  "Exxon",       "NYSE"),
    ("CVX",   "Chevron",      "NYSE"),   ("JPM",  "JPMorgan",    "NYSE"),
    ("BAC",   "BofA",         "NYSE"),   ("GS",   "Goldman",     "NYSE"),
    ("MS",    "Morgan Stanley","NYSE"),  ("WMT",  "Walmart",     "NYSE"),
    ("JNJ",   "J&J",          "NYSE"),   ("PFE",  "Pfizer",      "NYSE"),
    ("UNH",   "UnitedHealth", "NYSE"),   ("V",    "Visa",        "NYSE"),
    ("MA",    "Mastercard",   "NYSE"),   ("BRK-B","Berkshire",   "NYSE"),
    ("COIN",  "Coinbase",     "NASDAQ"), ("MSTR", "MicroStrategy","NASDAQ"),
    ("UBER",  "Uber",         "NYSE"),   ("ABNB", "Airbnb",      "NASDAQ"),
    ("SHOP",  "Shopify",      "NYSE"),   ("SQ",   "Block",       "NYSE"),
    ("PLTR",  "Palantir",     "NYSE"),   ("ARM",  "ARM Holdings","NASDAQ"),
]

STOCKS_DE = [
    ("SAP.DE",  "SAP",        "XETRA"), ("SIE.DE",  "Siemens",   "XETRA"),
    ("ALV.DE",  "Allianz",    "XETRA"), ("BAS.DE",  "BASF",      "XETRA"),
    ("IFX.DE",  "Infineon",   "XETRA"), ("MBG.DE",  "Mercedes",  "XETRA"),
    ("BMW.DE",  "BMW",        "XETRA"), ("VOW3.DE", "Volkswagen","XETRA"),
    ("ADS.DE",  "Adidas",     "XETRA"), ("MRK.DE",  "Merck DE",  "XETRA"),
    ("DBK.DE",  "Deutsche Bk","XETRA"), ("DTE.DE",  "Deutsche T","XETRA"),
    ("BEI.DE",  "Beiersdorf", "XETRA"), ("HNR1.DE", "Hannover Re","XETRA"),
    ("MUV2.DE", "Munich Re",  "XETRA"), ("RWE.DE",  "RWE",       "XETRA"),
    ("BAYN.DE", "Bayer",      "XETRA"), ("FRE.DE",  "Fresenius", "XETRA"),
    ("HEI.DE",  "HeidelMat",  "XETRA"), ("ENR.DE",  "Siemens En","XETRA"),
    ("CON.DE",  "Continental","XETRA"), ("QIA.DE",  "Qiagen",    "XETRA"),
    ("VNA.DE",  "Vonovia",    "XETRA"), ("DHL.DE",  "DHL Group", "XETRA"),
    ("AIR.DE",  "Airbus DE",  "XETRA"), ("LHA.DE",  "Lufthansa", "XETRA"),
]

STOCKS_FR = [
    ("AIR.PA",  "Airbus",      "XPAR"), ("MC.PA",   "LVMH",       "XPAR"),
    ("TTE.PA",  "TotalEnergies","XPAR"),("SAF.PA",  "Safran",      "XPAR"),
    ("OR.PA",   "L'Oreal",     "XPAR"), ("SAN.PA",  "Sanofi",      "XPAR"),
    ("BNP.PA",  "BNP Paribas", "XPAR"), ("ACA.PA",  "Credit Agri", "XPAR"),
    ("GLE.PA",  "Soc Generale","XPAR"), ("RMS.PA",  "Hermes",      "XPAR"),
    ("KER.PA",  "Kering",      "XPAR"), ("CAP.PA",  "Capgemini",   "XPAR"),
    ("DSY.PA",  "Dassault Sys","XPAR"), ("EDF.PA",  "EDF",         "XPAR"),
    ("ALO.PA",  "Alstom",      "XPAR"), ("VIE.PA",  "Veolia",      "XPAR"),
    ("PUB.PA",  "Publicis",    "XPAR"), ("STM.PA",  "STMicro",     "XPAR"),
    ("ATO.PA",  "Atos",        "XPAR"), ("VIV.PA",  "Vivendi",     "XPAR"),
]

STOCKS_NL = [
    ("ASML.AS", "ASML",        "XAMS"), ("PHIA.AS", "Philips",     "XAMS"),
    ("HEIA.AS", "Heineken",    "XAMS"), ("WKL.AS",  "Wolters Kluw","XAMS"),
    ("NN.AS",   "NN Group",    "XAMS"), ("RAND.AS", "Randstad",    "XAMS"),
    ("AGN.AS",  "Aegon",       "XAMS"), ("URW.AS",  "Unibail",     "XAMS"),
    ("AD.AS",   "Ahold",       "XAMS"), ("AKZA.AS", "Akzo Nobel",  "XAMS"),
    ("DSM.AS",  "DSM",         "XAMS"), ("MT.AS",   "ArcelorMittal","XAMS"),
    ("ABN.AS",  "ABN AMRO",    "XAMS"), ("BESI.AS", "BESI",        "XAMS"),
]

STOCKS_IT = [
    ("ENEL.MI", "Enel",        "XMIL"), ("ISP.MI",  "Intesa",      "XMIL"),
    ("ENI.MI",  "ENI",         "XMIL"), ("UCG.MI",  "UniCredit",   "XMIL"),
    ("STM.MI",  "STMicro IT",  "XMIL"), ("RACE.MI", "Ferrari",     "XMIL"),
    ("TIT.MI",  "Telecom IT",  "XMIL"), ("LDO.MI",  "Leonardo",    "XMIL"),
    ("PRY.MI",  "Prysmian",    "XMIL"), ("MB.MI",   "Mediobanca",  "XMIL"),
    ("MONC.MI", "Moncler",     "XMIL"), ("G.MI",    "Generali",    "XMIL"),
]

STOCKS_ES = [
    ("SAN.MC",  "Santander",   "XMAD"), ("BBVA.MC", "BBVA",        "XMAD"),
    ("ITX.MC",  "Inditex",     "XMAD"), ("IBE.MC",  "Iberdrola",   "XMAD"),
    ("REP.MC",  "Repsol",      "XMAD"), ("TEF.MC",  "Telefonica",  "XMAD"),
    ("CABK.MC", "CaixaBank",   "XMAD"), ("AMS.MC",  "Amadeus",     "XMAD"),
    ("FER.MC",  "Ferrovial",   "XMAD"), ("ELE.MC",  "Endesa",      "XMAD"),
    ("MAP.MC",  "Mapfre",      "XMAD"), ("MTS.MC",  "ArcelorMit ES","XMAD"),
]

STOCKS_UK = [
    ("SHEL.L",  "Shell",       "LSE"),  ("BP.L",    "BP",          "LSE"),
    ("HSBA.L",  "HSBC",        "LSE"),  ("AZN.L",   "AstraZeneca", "LSE"),
    ("ULVR.L",  "Unilever",    "LSE"),  ("DGE.L",   "Diageo",      "LSE"),
    ("RIO.L",   "Rio Tinto",   "LSE"),  ("GLEN.L",  "Glencore",    "LSE"),
    ("BT-A.L",  "BT Group",    "LSE"),  ("LLOY.L",  "Lloyds",      "LSE"),
    ("BARC.L",  "Barclays",    "LSE"),  ("VOD.L",   "Vodafone",    "LSE"),
    ("GSK.L",   "GSK",         "LSE"),  ("IMB.L",   "Imperial Br", "LSE"),
    ("BAE.L",   "BAE Systems", "LSE"),  ("RR.L",    "Rolls Royce", "LSE"),
    ("ARM.L",   "ARM UK",      "LSE"),  ("EXPN.L",  "Experian",    "LSE"),
]

STOCKS_CH = [
    ("NESN.SW", "Nestle",      "SWX"),  ("NOVN.SW", "Novartis",    "SWX"),
    ("ROG.SW",  "Roche",       "SWX"),  ("ABBN.SW", "ABB",         "SWX"),
    ("ZURN.SW", "Zurich Ins",  "SWX"),  ("UBSG.SW", "UBS",         "SWX"),
    ("CSGN.SW", "Credit Suisse","SWX"), ("LONN.SW", "Lonza",       "SWX"),
    ("SREN.SW", "Swiss Re",    "SWX"),  ("SLHN.SW", "Swiss Life",  "SWX"),
    ("ALC.SW",  "Alcon",       "SWX"),  ("GIVN.SW", "Givaudan",    "SWX"),
]

STOCKS_JP = [
    ("7203.T",  "Toyota",      "TSE"),  ("6758.T",  "Sony",        "TSE"),
    ("9984.T",  "SoftBank",    "TSE"),  ("6861.T",  "Keyence",     "TSE"),
    ("8306.T",  "Mitsubishi UFJ","TSE"),("7974.T",  "Nintendo",    "TSE"),
    ("9432.T",  "NTT",         "TSE"),  ("6954.T",  "Fanuc",       "TSE"),
    ("4519.T",  "Chugai Pharma","TSE"), ("8058.T",  "Mitsubishi",  "TSE"),
    ("6367.T",  "Daikin",      "TSE"),  ("9983.T",  "Fast Retailing","TSE"),
]

STOCKS_HK = [
    ("0700.HK", "Tencent",     "HKEX"), ("9988.HK", "Alibaba HK",  "HKEX"),
    ("0941.HK", "China Mobile","HKEX"), ("1299.HK", "AIA",         "HKEX"),
    ("0005.HK", "HSBC HK",     "HKEX"), ("2318.HK", "Ping An",     "HKEX"),
    ("3690.HK", "Meituan",     "HKEX"), ("0388.HK", "HK Exchanges","HKEX"),
    ("1810.HK", "Xiaomi",      "HKEX"), ("9999.HK", "NetEase",     "HKEX"),
]

STOCKS_AU = [
    ("BHP.AX",  "BHP",         "ASX"),  ("CBA.AX",  "CommonwlthBk","ASX"),
    ("CSL.AX",  "CSL",         "ASX"),  ("NAB.AX",  "NAB",         "ASX"),
    ("WBC.AX",  "Westpac",     "ASX"),  ("ANZ.AX",  "ANZ",         "ASX"),
    ("WES.AX",  "Wesfarmers",  "ASX"),  ("MQG.AX",  "Macquarie",   "ASX"),
    ("RIO.AX",  "Rio Tinto AU","ASX"),  ("WOW.AX",  "Woolworths",  "ASX"),
    ("FMG.AX",  "Fortescue",   "ASX"),  ("TLS.AX",  "Telstra",     "ASX"),
]

STOCKS_CA = [
    ("SHOP.TO", "Shopify CA",  "TSX"),  ("RY.TO",   "Royal Bank",  "TSX"),
    ("TD.TO",   "TD Bank",     "TSX"),  ("CNR.TO",  "CN Rail",     "TSX"),
    ("ENB.TO",  "Enbridge",    "TSX"),  ("BNS.TO",  "Scotiabank",  "TSX"),
    ("BMO.TO",  "BMO",         "TSX"),  ("SU.TO",   "Suncor",      "TSX"),
    ("ABX.TO",  "Barrick Gold","TSX"),  ("MFC.TO",  "Manulife",    "TSX"),
]

STOCKS_SE = [
    ("ERIC-B.ST","Ericsson",   "XSTO"), ("VOLV-B.ST","Volvo",      "XSTO"),
    ("ATCO-A.ST","Atlas Copco","XSTO"), ("SAND.ST",  "Sandvik",    "XSTO"),
    ("SEB-A.ST", "SEB Bank",   "XSTO"), ("SWED-A.ST","Swedbank",   "XSTO"),
    ("INVE-B.ST","Investor",   "XSTO"), ("HM-B.ST",  "H&M",        "XSTO"),
    ("ALFA.ST",  "Alfa Laval", "XSTO"), ("SKF-B.ST", "SKF",        "XSTO"),
]

STOCKS_DK = [
    ("NOVO-B.CO","Novo Nordisk","XCSE"), ("MAERSK-B.CO","Maersk","XCSE"),
    ("DSV.CO",   "DSV",        "XCSE"), ("ORSTED.CO", "Orsted",    "XCSE"),
    ("CARL-B.CO","Carlsberg",  "XCSE"), ("COLO-B.CO", "Coloplast", "XCSE"),
    ("GN.CO",    "GN Store",   "XCSE"), ("DEMANT.CO", "Demant",    "XCSE"),
]

STOCKS_NO = [
    ("EQNR.OL", "Equinor",    "XOSL"),  ("DNB.OL",  "DNB Bank",   "XOSL"),
    ("TEL.OL",  "Telenor",    "XOSL"),  ("ORK.OL",  "Orkla",      "XOSL"),
    ("AKERBP.OL","Aker BP",   "XOSL"),  ("MOWI.OL", "Mowi",       "XOSL"),
    ("YAR.OL",  "Yara",       "XOSL"),  ("NHY.OL",  "Norsk Hydro","XOSL"),
]

STOCKS_FI = [
    ("NOKIA.HE","Nokia",       "XHEL"),  ("FORTUM.HE","Fortum",   "XHEL"),
    ("NESTE.HE","Neste",       "XHEL"),  ("SAMPO.HE", "Sampo",    "XHEL"),
    ("STERV.HE","Stora Enso",  "XHEL"),  ("WRT1V.HE", "Wartsila", "XHEL"),
]

STOCKS_PT = [
    ("BCP.LS",  "BCP",         "XLIS"),  ("EDP.LS",  "EDP",        "XLIS"),
    ("GALP.LS", "Galp",        "XLIS"),  ("NOS.LS",  "NOS",        "XLIS"),
    ("JMT.LS",  "Jeronimo M",  "XLIS"),  ("SON.LS",  "Sonae",      "XLIS"),
    ("EGL.LS",  "EGL",         "XLIS"),  ("EDPR.LS", "EDP Renew",  "XLIS"),
]

STOCKS_GR = [
    ("OPAP.AT", "OPAP",        "XATH"),  ("ETE.AT",  "NBG",        "XATH"),
    ("EUROB.AT","Eurobank",    "XATH"),  ("ALPHA.AT","Alpha Bank",  "XATH"),
    ("HTO.AT",  "OTE",         "XATH"),  ("PPC.AT",  "PPC",        "XATH"),
]

STOCKS_AT = [
    ("VOE.VI",  "Voestalpine", "XWBO"),  ("OMV.VI",  "OMV",        "XWBO"),
    ("EBS.VI",  "Erste Bank",  "XWBO"),  ("VER.VI",  "Verbund",    "XWBO"),
    ("RBI.VI",  "Raiffeisen",  "XWBO"),  ("ATX.VI",  "Vienna ATX", "XWBO"),
]

STOCKS_BE = [
    ("ABI.BR",  "AB InBev",    "XBRU"),  ("UCB.BR",  "UCB",        "XBRU"),
    ("SOLB.BR", "Solvay",      "XBRU"),  ("ACKB.BR", "Ackermans",  "XBRU"),
    ("COLR.BR", "Colruyt",     "XBRU"),  ("AGS.BR",  "Ageas",      "XBRU"),
]

STOCKS_IE = [
    ("CRH.IR",  "CRH",         "XDUB"),  ("RYANAIR.IR","Ryanair",  "XDUB"),
    ("AIB.IR",  "AIB",         "XDUB"),  ("BOI.IR",  "Bank Ireland","XDUB"),
    ("EXPERIAN.IR","Experian IR","XDUB"),
]

STOCKS_PL = [
    ("PKN.WA",  "PKN Orlen",   "XWAR"),  ("PKO.WA",  "PKO Bank",   "XWAR"),
    ("PZU.WA",  "PZU",         "XWAR"),  ("KGH.WA",  "KGHM",       "XWAR"),
    ("LPP.WA",  "LPP",         "XWAR"),  ("ALE.WA",  "Allegro",    "XWAR"),
]

STOCKS_CZ = [
    ("CEZ.PR",  "CEZ",         "XPRA"),  ("KOMB.PR", "Komercni Bk","XPRA"),
    ("MONET.PR","Moneta",      "XPRA"),
]

STOCKS_SG = [
    ("D05.SI",  "DBS Bank",    "SGX"),   ("O39.SI",  "OCBC",       "SGX"),
    ("U11.SI",  "UOB",         "SGX"),   ("Z74.SI",  "SingTel",    "SGX"),
    ("C6L.SI",  "Singapore Air","SGX"),  ("BN4.SI",  "Keppel",     "SGX"),
]

# ── AGREGA TODOS OS STOCKS ───────────────────────────────────
STOCKS = (STOCKS_US + STOCKS_DE + STOCKS_FR + STOCKS_NL +
          STOCKS_IT + STOCKS_ES + STOCKS_UK + STOCKS_CH +
          STOCKS_JP + STOCKS_HK + STOCKS_AU + STOCKS_CA +
          STOCKS_SE + STOCKS_DK + STOCKS_NO + STOCKS_FI +
          STOCKS_PT + STOCKS_GR + STOCKS_AT + STOCKS_BE +
          STOCKS_IE + STOCKS_PL + STOCKS_CZ + STOCKS_SG)

# ── ETFs ─────────────────────────────────────────────────────
ETFS = [
    ("QQQ",     "Nasdaq ETF",      "NASDAQ"),
    ("SPY",     "S&P500 ETF",      "NYSE"),
    ("IWM",     "Russell 2000",    "NYSE"),
    ("MCHI",    "China ETF",       "NYSE"),
    ("INDA",    "India ETF",       "NYSE"),
    ("EEM",     "EM ETF",          "NYSE"),
    ("EWJ",     "Japan ETF",       "NYSE"),
    ("EWZ",     "Brazil ETF",      "NYSE"),
    ("GLD",     "Gold ETF",        "NYSE"),
    ("TLT",     "20Y Bond ETF",    "NYSE"),
    ("IEF",     "7-10Y Bond ETF",  "NYSE"),
    ("HYG",     "High Yield ETF",  "NYSE"),
    ("XLE",     "Energy ETF",      "NYSE"),
    ("XLF",     "Financials ETF",  "NYSE"),
    ("XLK",     "Tech ETF",        "NYSE"),
    ("XBI",     "Biotech ETF",     "NYSE"),
    ("ARK",     "ARK Innovation",  "NYSE"),
    ("QDV5.DE", "MSCI India DE",   "XETRA"),
    ("EXS1.DE", "EuroStoxx50",     "XETRA"),
    ("DBXD.DE", "DAX ETF",         "XETRA"),
    ("EXXT.DE", "Nasdaq DE",       "XETRA"),
    ("IWDA.AS", "MSCI World",      "XAMS"),
    ("VUSA.AS", "S&P500 EUR",      "XAMS"),
    ("CSPX.AS", "S&P500 EUR Acc",  "XAMS"),
    ("IBCK.DE", "Bond Corp EUR",   "XETRA"),
]

# ── FX ───────────────────────────────────────────────────────
FX = [
    ("EURUSD=X", "EUR/USD",      "FX"),
    ("GBPUSD=X", "GBP/USD",      "FX"),
    ("USDJPY=X", "USD/JPY",      "FX"),
    ("AUDUSD=X", "AUD/USD",      "FX"),
    ("USDCAD=X", "USD/CAD",      "FX"),
    ("USDCHF=X", "USD/CHF",      "FX"),
    ("NZDUSD=X", "NZD/USD",      "FX"),
    ("EURGBP=X", "EUR/GBP",      "FX"),
    ("EURJPY=X", "EUR/JPY",      "FX"),
    ("USDCNH=X", "USD/CNH",      "FX"),
    ("USDSEK=X", "USD/SEK",      "FX"),
    ("USDNOK=X", "USD/NOK",      "FX"),
    ("USDDKK=X", "USD/DKK",      "FX"),
    ("USDSGD=X", "USD/SGD",      "FX"),
    ("USDHKD=X", "USD/HKD",      "FX"),
    ("DX-Y.NYB", "Dollar Index", "MACRO"),
    ("UUP",      "Dollar ETF",   "MACRO"),
    ("FXE",      "Euro ETF",     "MACRO"),
    ("FXY",      "Yen ETF",      "MACRO"),
]

# ── COMMODITIES ──────────────────────────────────────────────
COMMODITIES = [
    ("CL=F",  "WTI Crude",    "COMMODITY"),
    ("BZ=F",  "Brent Crude",  "COMMODITY"),
    ("NG=F",  "Natural Gas",  "COMMODITY"),
    ("RB=F",  "RBOB Gasoline","COMMODITY"),
    ("GC=F",  "Gold",         "COMMODITY"),
    ("SI=F",  "Silver",       "COMMODITY"),
    ("HG=F",  "Copper",       "COMMODITY"),
    ("PL=F",  "Platinum",     "COMMODITY"),
    ("PA=F",  "Palladium",    "COMMODITY"),
    ("ZC=F",  "Corn",         "COMMODITY"),
    ("ZW=F",  "Wheat",        "COMMODITY"),
    ("ZS=F",  "Soybeans",     "COMMODITY"),
    ("KC=F",  "Coffee",       "COMMODITY"),
    ("SB=F",  "Sugar",        "COMMODITY"),
    ("CC=F",  "Cocoa",        "COMMODITY"),
    ("DBA",   "Agri ETF",     "COMMODITY"),
    ("SLV",   "Silver ETF",   "COMMODITY"),
    ("CPER",  "Copper ETF",   "COMMODITY"),
    ("UNG",   "NatGas ETF",   "COMMODITY"),
]

# ── VOLATILITY ───────────────────────────────────────────────
VOLATILITY = [
    ("^VIX",   "VIX S&P500",     "VOL"),
    ("^VXN",   "VXN Nasdaq",     "VOL"),
    ("^RVX",   "RVX Russell",    "VOL"),
    ("^VXD",   "VXD Dow",        "VOL"),
    ("^OVX",   "OVX Oil",        "VOL"),
    ("^GVZ",   "GVZ Gold",       "VOL"),
    ("^EVZ",   "EVZ Euro",       "VOL"),
    ("^VVIX",  "VVIX Vol of VIX","VOL"),
    ("^SKEW",  "SKEW Tail Risk", "VOL"),
    ("VXX",    "VIX ETF",        "VOL"),
]

# ── OPTIONS ──────────────────────────────────────────────────
OPTIONS_UNIVERSE = [
    # CBOE
    ("^DJX",    "Dow Jones Mini",   "CBOE"),
    ("^RUT",    "Russell 2000",     "CBOE"),
    ("SPY",     "XSP proxy",        "CBOE"),
    ("QQQ",     "Nasdaq",           "CBOE"),
    ("NVDA",    "Nvidia",           "CBOE"),
    ("AAPL",    "Apple",            "CBOE"),
    ("MSFT",    "Microsoft",        "CBOE"),
    ("TSLA",    "Tesla",            "CBOE"),
    ("AMD",     "AMD",              "CBOE"),
    # EUREX
    ("EXS1.DE", "EuroStoxx50",      "EUREX"),
    ("DBXD.DE", "DAX ETF",          "EUREX"),
    ("IWDA.AS", "MSCI World",       "EUREX"),
    ("EUN2.DE", "MSCI World EUR",   "EUREX"),
    # EURONEXT AMSTERDAM
    ("IWDA.AS", "MSCI World AMS",   "EURONEXT"),
    ("VUSA.AS", "S&P500 EUR",       "EURONEXT"),
    ("ASML.AS", "ASML",             "EURONEXT"),
    # EURONEXT BRUSSELS
    ("ABI.BR",  "AB InBev",         "EURONEXT"),
    ("UCB.BR",  "UCB",              "EURONEXT"),
    # EURONEXT LISBON — PSX apenas
    ("BCP.LS",  "BCP PSX",          "EURONEXT"),
    ("EDP.LS",  "EDP PSX",          "EURONEXT"),
    # EURONEXT MILAN
    ("ENEL.MI", "Enel",             "EURONEXT"),
    ("ISP.MI",  "Intesa",           "EURONEXT"),
    ("RACE.MI", "Ferrari",          "EURONEXT"),
    # EURONEXT PARIS
    ("AIR.PA",  "Airbus",           "EURONEXT"),
    ("MC.PA",   "LVMH",             "EURONEXT"),
    ("TTE.PA",  "TotalEnergies",    "EURONEXT"),
    ("OR.PA",   "L'Oreal",          "EURONEXT"),
    # MEFF
    ("SAN.MC",  "Santander",        "MEFF"),
    ("BBVA.MC", "BBVA",             "MEFF"),
    ("ITX.MC",  "Inditex",          "MEFF"),
    ("IBE.MC",  "Iberdrola",        "MEFF"),
    # OMX
    ("ERIC-B.ST","Ericsson",        "OMX"),
    ("NOVO-B.CO","Novo Nordisk",    "OMX"),
    ("VOLV-B.ST","Volvo",           "OMX"),
]

# ── DEGIRO EXCHANGE MAPPING ──────────────────────────────────
DEGIRO_SUFFIX = {
    "NASDAQ": "",    "NYSE":  "",    "XETRA": ".DE",
    "XPAR":   ".PA", "XAMS":  ".AS", "XMIL":  ".MI",
    "XLIS":   ".LS", "XMAD":  ".MC", "XBRU":  ".BR",
    "LSE":    ".L",  "SWX":   ".SW", "TSE":   ".T",
    "HKEX":   ".HK", "ASX":   ".AX", "TSX":   ".TO",
    "XSTO":   ".ST", "XCSE":  ".CO", "XOSL":  ".OL",
    "XHEL":   ".HE", "XATH":  ".AT", "XWBO":  ".VI",
    "XDUB":   ".IR", "XWAR":  ".WA", "XPRA":  ".PR",
    "SGX":    ".SI", "FX":    "",    "MACRO": "",
    "COMMODITY":"",  "VOL":   "",    "CBOE":  "",
    "EUREX":  ".DE", "RATES": "",
}

# Universo completo
ALL = STOCKS + ETFS + FX + COMMODITIES + VOLATILITY