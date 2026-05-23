# ============================================================
# UNIVERSE.PY — Universo completo DeGiro (~1000+ tickers)
# Stocks + ETFs + FX + Commodities + Vol + Crypto
# ============================================================

# ── STOCKS US ────────────────────────────────────────────────
STOCKS_US = [
    ("AAPL",  "Apple",          "NASDAQ"), ("MSFT", "Microsoft",    "NASDAQ"),
    ("NVDA",  "Nvidia",         "NASDAQ"), ("AMD",  "AMD",          "NASDAQ"),
    ("META",  "Meta",           "NASDAQ"), ("AMZN", "Amazon",       "NASDAQ"),
    ("GOOGL", "Alphabet",       "NASDAQ"), ("TSLA", "Tesla",        "NASDAQ"),
    ("INTC",  "Intel",          "NASDAQ"), ("QCOM", "Qualcomm",     "NASDAQ"),
    ("ADBE",  "Adobe",          "NASDAQ"), ("NFLX", "Netflix",      "NASDAQ"),
    ("PYPL",  "PayPal",         "NASDAQ"), ("CSCO", "Cisco",        "NASDAQ"),
    ("TXN",   "Texas Instr",    "NASDAQ"), ("AVGO", "Broadcom",     "NASDAQ"),
    ("CRM",   "Salesforce",     "NYSE"),   ("NOW",  "ServiceNow",   "NYSE"),
    ("UBER",  "Uber",           "NYSE"),   ("ABNB", "Airbnb",       "NASDAQ"),
    ("SHOP",  "Shopify",        "NYSE"),   ("SNOW", "Snowflake",    "NYSE"),
    ("PLTR",  "Palantir",       "NYSE"),   ("ARM",  "ARM Holdings", "NASDAQ"),
    ("BABA",  "Alibaba",        "NYSE"),   ("PDD",  "PDD",          "NASDAQ"),
    ("NIO",   "NIO",            "NYSE"),   ("BIDU", "Baidu",        "NASDAQ"),
    ("JD",    "JD.com",         "NASDAQ"), ("TMUS", "T-Mobile",     "NASDAQ"),
    ("XOM",   "Exxon",          "NYSE"),   ("CVX",  "Chevron",      "NYSE"),
    ("COP",   "ConocoPhillips", "NYSE"),   ("SLB",  "Schlumberger", "NYSE"),
    ("JPM",   "JPMorgan",       "NYSE"),   ("BAC",  "BofA",         "NYSE"),
    ("GS",    "Goldman",        "NYSE"),   ("MS",   "Morgan Stanley","NYSE"),
    ("WFC",   "Wells Fargo",    "NYSE"),   ("C",    "Citigroup",    "NYSE"),
    ("BLK",   "BlackRock",      "NYSE"),   ("AXP",  "Amex",         "NYSE"),
    ("WMT",   "Walmart",        "NYSE"),   ("COST", "Costco",       "NASDAQ"),
    ("TGT",   "Target",         "NYSE"),   ("AMGN", "Amgen",        "NASDAQ"),
    ("LLY",   "Eli Lilly",      "NYSE"),   ("JNJ",  "J&J",          "NYSE"),
    ("PFE",   "Pfizer",         "NYSE"),   ("MRK",  "Merck",        "NYSE"),
    ("UNH",   "UnitedHealth",   "NYSE"),   ("ABBV", "AbbVie",       "NYSE"),
    ("BMY",   "Bristol Myers",  "NYSE"),   ("GILD", "Gilead",       "NASDAQ"),
    ("V",     "Visa",           "NYSE"),   ("MA",   "Mastercard",   "NYSE"),
    ("BRK-B", "Berkshire",      "NYSE"),   ("COIN", "Coinbase",     "NASDAQ"),
    ("MSTR",  "MicroStrategy",  "NASDAQ"), ("SQ",   "Block",        "NYSE"),
    ("HOOD",  "Robinhood",      "NASDAQ"), ("AFRM", "Affirm",       "NASDAQ"),
    ("BA",    "Boeing",         "NYSE"),   ("CAT",  "Caterpillar",  "NYSE"),
    ("DE",    "Deere",          "NYSE"),   ("RTX",  "Raytheon",     "NYSE"),
    ("LMT",   "Lockheed",       "NYSE"),   ("GE",   "GE",           "NYSE"),
    ("NEE",   "NextEra",        "NYSE"),   ("DUK",  "Duke Energy",  "NYSE"),
    ("SO",    "Southern Co",    "NYSE"),   ("MELI", "MercadoLibre", "NASDAQ"),
    ("SPOT",  "Spotify",        "NYSE"),   ("DDOG", "Datadog",      "NASDAQ"),
    ("NET",   "Cloudflare",     "NYSE"),   ("CRWD", "Crowdstrike",  "NASDAQ"),
    ("MDB",   "MongoDB",        "NASDAQ"), ("ZS",   "Zscaler",      "NASDAQ"),
    ("OKTA",  "Okta",           "NASDAQ"), ("HUBS", "HubSpot",      "NYSE"),
    ("TEAM",  "Atlassian",      "NASDAQ"), ("WDAY", "Workday",      "NASDAQ"),
    ("ZM",    "Zoom",           "NASDAQ"), ("DOCU", "DocuSign",     "NASDAQ"),
    ("IONQ",  "IonQ",           "NYSE"),   ("RGTI", "Rigetti",      "NASDAQ"),
    ("SE",    "Sea Limited",    "NYSE"),   ("GRAB", "Grab",         "NASDAQ"),
    ("SOFI",  "SoFi",           "NASDAQ"), ("NU",   "Nubank",       "NYSE"),
    ("MRNA",  "Moderna",        "NASDAQ"), ("BNTX", "BioNTech",     "NASDAQ"),
    ("REGN",  "Regeneron",      "NASDAQ"), ("VRTX", "Vertex",       "NASDAQ"),
    ("ENPH",  "Enphase",        "NASDAQ"), ("FSLR", "First Solar",  "NASDAQ"),
    ("PLUG",  "Plug Power",     "NASDAQ"), ("BE",   "Bloom Energy", "NYSE"),
    ("LULU",  "Lululemon",      "NASDAQ"), ("NKE",  "Nike",         "NYSE"),
    ("SBUX",  "Starbucks",      "NASDAQ"), ("MCD",  "McDonalds",    "NYSE"),
    ("CMG",   "Chipotle",       "NYSE"),   ("MARA", "Marathon Dig", "NASDAQ"),
    ("RIOT",  "Riot Platforms", "NASDAQ"), ("CLSK", "CleanSpark",   "NASDAQ"),
    ("HUT",   "Hut 8 Mining",   "NASDAQ"),
]

# ── STOCKS DE ────────────────────────────────────────────────
STOCKS_DE = [
    ("SAP.DE",  "SAP",           "XETRA"), ("SIE.DE",  "Siemens",     "XETRA"),
    ("ALV.DE",  "Allianz",       "XETRA"), ("BAS.DE",  "BASF",        "XETRA"),
    ("IFX.DE",  "Infineon",      "XETRA"), ("MBG.DE",  "Mercedes",    "XETRA"),
    ("BMW.DE",  "BMW",           "XETRA"), ("VOW3.DE", "Volkswagen",  "XETRA"),
    ("ADS.DE",  "Adidas",        "XETRA"), ("MRK.DE",  "Merck DE",    "XETRA"),
    ("DBK.DE",  "Deutsche Bk",   "XETRA"), ("DTE.DE",  "Deutsche T",  "XETRA"),
    ("BEI.DE",  "Beiersdorf",    "XETRA"), ("MUV2.DE", "Munich Re",   "XETRA"),
    ("RWE.DE",  "RWE",           "XETRA"), ("BAYN.DE", "Bayer",       "XETRA"),
    ("FRE.DE",  "Fresenius",     "XETRA"), ("HEI.DE",  "HeidelMat",   "XETRA"),
    ("ENR.DE",  "Siemens En",    "XETRA"), ("CON.DE",  "Continental", "XETRA"),
    ("QIA.DE",  "Qiagen",        "XETRA"), ("VNA.DE",  "Vonovia",     "XETRA"),
    ("DHL.DE",  "DHL Group",     "XETRA"), ("AIR.DE",  "Airbus DE",   "XETRA"),
    ("LHA.DE",  "Lufthansa",     "XETRA"), ("MTX.DE",  "MTU Aero",    "XETRA"),
    ("ZAL.DE",  "Zalando",       "XETRA"),
]

# ── STOCKS FR ────────────────────────────────────────────────
STOCKS_FR = [
    ("AIR.PA", "Airbus",         "XPAR"), ("MC.PA",   "LVMH",         "XPAR"),
    ("TTE.PA", "TotalEnergies",  "XPAR"), ("SAF.PA",  "Safran",       "XPAR"),
    ("OR.PA",  "L'Oreal",        "XPAR"), ("SAN.PA",  "Sanofi",       "XPAR"),
    ("BNP.PA", "BNP Paribas",    "XPAR"), ("ACA.PA",  "Credit Agri",  "XPAR"),
    ("GLE.PA", "Soc Generale",   "XPAR"), ("RMS.PA",  "Hermes",       "XPAR"),
    ("KER.PA", "Kering",         "XPAR"), ("CAP.PA",  "Capgemini",    "XPAR"),
    ("DSY.PA", "Dassault Sys",   "XPAR"), ("STM.PA",  "STMicro",      "XPAR"),
    ("AI.PA",  "Air Liquide",    "XPAR"), ("DG.PA",   "Vinci",        "XPAR"),
    ("ML.PA",  "Michelin",       "XPAR"),
]

# ── STOCKS NL ────────────────────────────────────────────────
STOCKS_NL = [
    ("ASML.AS", "ASML",          "XAMS"), ("PHIA.AS", "Philips",      "XAMS"),
    ("HEIA.AS", "Heineken",      "XAMS"), ("WKL.AS",  "Wolters Kluw", "XAMS"),
    ("NN.AS",   "NN Group",      "XAMS"), ("AGN.AS",  "Aegon",        "XAMS"),
    ("AD.AS",   "Ahold",         "XAMS"), ("AKZA.AS", "Akzo Nobel",   "XAMS"),
    ("MT.AS",   "ArcelorMittal", "XAMS"), ("ABN.AS",  "ABN AMRO",     "XAMS"),
    ("BESI.AS", "BESI",          "XAMS"),
]

# ── STOCKS IT ────────────────────────────────────────────────
STOCKS_IT = [
    ("ENEL.MI", "Enel",          "XMIL"), ("ISP.MI",  "Intesa",       "XMIL"),
    ("ENI.MI",  "ENI",           "XMIL"), ("UCG.MI",  "UniCredit",    "XMIL"),
    ("RACE.MI", "Ferrari",       "XMIL"), ("LDO.MI",  "Leonardo",     "XMIL"),
    ("PRY.MI",  "Prysmian",      "XMIL"), ("MB.MI",   "Mediobanca",   "XMIL"),
    ("MONC.MI", "Moncler",       "XMIL"), ("G.MI",    "Generali",     "XMIL"),
]

# ── STOCKS ES ────────────────────────────────────────────────
STOCKS_ES = [
    ("SAN.MC",  "Santander",     "XMAD"), ("BBVA.MC", "BBVA",         "XMAD"),
    ("ITX.MC",  "Inditex",       "XMAD"), ("IBE.MC",  "Iberdrola",    "XMAD"),
    ("REP.MC",  "Repsol",        "XMAD"), ("TEF.MC",  "Telefonica",   "XMAD"),
    ("CABK.MC", "CaixaBank",     "XMAD"), ("AMS.MC",  "Amadeus",      "XMAD"),
    ("FER.MC",  "Ferrovial",     "XMAD"), ("IAG.MC",  "IAG",          "XMAD"),
]

# ── STOCKS UK ────────────────────────────────────────────────
STOCKS_UK = [
    ("SHEL.L", "Shell",          "LSE"),  ("BP.L",    "BP",           "LSE"),
    ("HSBA.L", "HSBC",           "LSE"),  ("AZN.L",   "AstraZeneca",  "LSE"),
    ("ULVR.L", "Unilever",       "LSE"),  ("RIO.L",   "Rio Tinto",    "LSE"),
    ("GLEN.L", "Glencore",       "LSE"),  ("LLOY.L",  "Lloyds",       "LSE"),
    ("BARC.L", "Barclays",       "LSE"),  ("GSK.L",   "GSK",          "LSE"),
    ("BAE.L",  "BAE Systems",    "LSE"),  ("RR.L",    "Rolls Royce",  "LSE"),
    ("NWG.L",  "NatWest",        "LSE"),
]

# ── STOCKS CH ────────────────────────────────────────────────
STOCKS_CH = [
    ("NESN.SW", "Nestle",        "SWX"),  ("NOVN.SW", "Novartis",     "SWX"),
    ("ROG.SW",  "Roche",         "SWX"),  ("ABBN.SW", "ABB",          "SWX"),
    ("ZURN.SW", "Zurich Ins",    "SWX"),  ("UBSG.SW", "UBS",          "SWX"),
    ("LONN.SW", "Lonza",         "SWX"),  ("SREN.SW", "Swiss Re",     "SWX"),
]

# ── STOCKS JP ────────────────────────────────────────────────
STOCKS_JP = [
    ("7203.T",  "Toyota",        "TSE"),  ("6758.T",  "Sony",         "TSE"),
    ("9984.T",  "SoftBank",      "TSE"),  ("6861.T",  "Keyence",      "TSE"),
    ("8306.T",  "Mitsubishi UFJ","TSE"),  ("7974.T",  "Nintendo",     "TSE"),
    ("8035.T",  "Tokyo Electron","TSE"),  ("6098.T",  "Recruit",      "TSE"),
]

# ── STOCKS HK ────────────────────────────────────────────────
STOCKS_HK = [
    ("0700.HK", "Tencent",       "HKEX"), ("9988.HK", "Alibaba HK",   "HKEX"),
    ("0941.HK", "China Mobile",  "HKEX"), ("1299.HK", "AIA",          "HKEX"),
    ("3690.HK", "Meituan",       "HKEX"), ("1810.HK", "Xiaomi",       "HKEX"),
]

# ── STOCKS AU ────────────────────────────────────────────────
STOCKS_AU = [
    ("BHP.AX",  "BHP",           "ASX"),  ("CBA.AX",  "CommonwlthBk", "ASX"),
    ("CSL.AX",  "CSL",           "ASX"),  ("NAB.AX",  "NAB",          "ASX"),
    ("WBC.AX",  "Westpac",       "ASX"),  ("ANZ.AX",  "ANZ",          "ASX"),
    ("WES.AX",  "Wesfarmers",    "ASX"),  ("MQG.AX",  "Macquarie",    "ASX"),
    ("RIO.AX",  "Rio Tinto AU",  "ASX"),  ("FMG.AX",  "Fortescue",    "ASX"),
]

# ── STOCKS CA ────────────────────────────────────────────────
STOCKS_CA = [
    ("SHOP.TO", "Shopify CA",    "TSX"),  ("RY.TO",   "Royal Bank",   "TSX"),
    ("TD.TO",   "TD Bank",       "TSX"),  ("CNR.TO",  "CN Rail",      "TSX"),
    ("ENB.TO",  "Enbridge",      "TSX"),  ("BNS.TO",  "Scotiabank",   "TSX"),
    ("BMO.TO",  "BMO",           "TSX"),  ("SU.TO",   "Suncor",       "TSX"),
    ("ABX.TO",  "Barrick Gold",  "TSX"),
]

# ── STOCKS SE ────────────────────────────────────────────────
STOCKS_SE = [
    ("ERIC-B.ST","Ericsson",     "XSTO"), ("VOLV-B.ST","Volvo",       "XSTO"),
    ("ATCO-A.ST","Atlas Copco",  "XSTO"), ("SAND.ST",  "Sandvik",     "XSTO"),
    ("INVE-B.ST","Investor",     "XSTO"), ("HM-B.ST",  "H&M",         "XSTO"),
]

# ── STOCKS DK ────────────────────────────────────────────────
STOCKS_DK = [
    ("NOVO-B.CO","Novo Nordisk", "XCSE"), ("DSV.CO",   "DSV",         "XCSE"),
    ("ORSTED.CO","Orsted",       "XCSE"), ("CARL-B.CO","Carlsberg",    "XCSE"),
    ("COLO-B.CO","Coloplast",    "XCSE"),
]

# ── STOCKS NO ────────────────────────────────────────────────
STOCKS_NO = [
    ("EQNR.OL", "Equinor",       "XOSL"), ("DNB.OL",  "DNB Bank",    "XOSL"),
    ("TEL.OL",  "Telenor",       "XOSL"), ("AKERBP.OL","Aker BP",     "XOSL"),
    ("YAR.OL",  "Yara",          "XOSL"), ("NHY.OL",  "Norsk Hydro", "XOSL"),
]

# ── STOCKS FI ────────────────────────────────────────────────
STOCKS_FI = [
    ("NOKIA.HE","Nokia",         "XHEL"), ("FORTUM.HE","Fortum",      "XHEL"),
    ("NESTE.HE","Neste",         "XHEL"), ("SAMPO.HE", "Sampo",       "XHEL"),
    ("KNEBV.HE","Kone",          "XHEL"),
]

# ── STOCKS PT ────────────────────────────────────────────────
STOCKS_PT = [
    ("BCP.LS",  "BCP",           "XLIS"), ("EDP.LS",  "EDP",          "XLIS"),
    ("GALP.LS", "Galp",          "XLIS"), ("NOS.LS",  "NOS",          "XLIS"),
    ("JMT.LS",  "Jeronimo M",    "XLIS"), ("SON.LS",  "Sonae",        "XLIS"),
    ("EDPR.LS", "EDP Renew",     "XLIS"), ("CTT.LS",  "CTT Correios", "XLIS"),
]

# ── STOCKS GR ────────────────────────────────────────────────
STOCKS_GR = [
    ("OPAP.AT", "OPAP",          "XATH"), ("ETE.AT",  "NBG",          "XATH"),
    ("EUROB.AT","Eurobank",      "XATH"), ("ALPHA.AT","Alpha Bank",   "XATH"),
    ("PPC.AT",  "PPC",           "XATH"),
]

# ── STOCKS AT ────────────────────────────────────────────────
STOCKS_AT = [
    ("VOE.VI",  "Voestalpine",   "XWBO"), ("OMV.VI",  "OMV",          "XWBO"),
    ("EBS.VI",  "Erste Bank",    "XWBO"), ("VER.VI",  "Verbund",      "XWBO"),
    ("RBI.VI",  "Raiffeisen",    "XWBO"),
]

# ── STOCKS BE ────────────────────────────────────────────────
STOCKS_BE = [
    ("ABI.BR",  "AB InBev",      "XBRU"), ("UCB.BR",  "UCB",          "XBRU"),
    ("SOLB.BR", "Solvay",        "XBRU"), ("ACKB.BR", "Ackermans",    "XBRU"),
    ("COLR.BR", "Colruyt",       "XBRU"), ("AGS.BR",  "Ageas",        "XBRU"),
]

# ── STOCKS IE ────────────────────────────────────────────────
STOCKS_IE = [
    ("CRH.IR",  "CRH",           "XDUB"), ("RYANAIR.IR","Ryanair",    "XDUB"),
    ("AIB.IR",  "AIB",           "XDUB"), ("BOI.IR",  "Bank Ireland", "XDUB"),
]

# ── STOCKS PL ────────────────────────────────────────────────
STOCKS_PL = [
    ("PKN.WA",  "PKN Orlen",     "XWAR"), ("PKO.WA",  "PKO Bank",     "XWAR"),
    ("PZU.WA",  "PZU",           "XWAR"), ("KGH.WA",  "KGHM",         "XWAR"),
    ("CDR.WA",  "CD Projekt",    "XWAR"), ("DNP.WA",  "Dino Polska",  "XWAR"),
]

# ── STOCKS SG ────────────────────────────────────────────────
STOCKS_SG = [
    ("D05.SI",  "DBS Bank",      "SGX"),  ("O39.SI",  "OCBC",         "SGX"),
    ("U11.SI",  "UOB",           "SGX"),  ("Z74.SI",  "SingTel",      "SGX"),
    ("C6L.SI",  "Singapore Air", "SGX"),
]

# ── AGREGA STOCKS ────────────────────────────────────────────
STOCKS = (STOCKS_US + STOCKS_DE + STOCKS_FR + STOCKS_NL +
          STOCKS_IT + STOCKS_ES + STOCKS_UK + STOCKS_CH +
          STOCKS_JP + STOCKS_HK + STOCKS_AU + STOCKS_CA +
          STOCKS_SE + STOCKS_DK + STOCKS_NO + STOCKS_FI +
          STOCKS_PT + STOCKS_GR + STOCKS_AT + STOCKS_BE +
          STOCKS_IE + STOCKS_PL + STOCKS_SG)

# ── ETFs ─────────────────────────────────────────────────────
ETFS = [
    ("QQQ",     "Nasdaq ETF",        "NASDAQ"),
    ("SPY",     "S&P500 ETF",        "NYSE"),
    ("IWM",     "Russell 2000",      "NYSE"),
    ("DIA",     "Dow Jones ETF",     "NYSE"),
    ("VTI",     "Total Mkt ETF",     "NYSE"),
    ("XLE",     "Energy ETF",        "NYSE"),
    ("XLF",     "Financials ETF",    "NYSE"),
    ("XLK",     "Tech ETF",          "NYSE"),
    ("XLV",     "Healthcare ETF",    "NYSE"),
    ("XLI",     "Industrials ETF",   "NYSE"),
    ("XLY",     "Consumer Disc ETF", "NYSE"),
    ("XLP",     "Consumer Stap ETF", "NYSE"),
    ("XLU",     "Utilities ETF",     "NYSE"),
    ("XLB",     "Materials ETF",     "NYSE"),
    ("XLRE",    "Real Estate ETF",   "NYSE"),
    ("XBI",     "Biotech ETF",       "NYSE"),
    ("GDX",     "Gold Miners ETF",   "NYSE"),
    ("GDXJ",    "Jr Gold Miners",    "NYSE"),
    ("ARKK",    "ARK Innovation",    "NYSE"),
    ("MCHI",    "China ETF",         "NYSE"),
    ("INDA",    "India ETF",         "NYSE"),
    ("EEM",     "EM ETF",            "NYSE"),
    ("VWO",     "EM Vanguard ETF",   "NYSE"),
    ("EWJ",     "Japan ETF",         "NYSE"),
    ("EWZ",     "Brazil ETF",        "NYSE"),
    ("EWY",     "Korea ETF",         "NYSE"),
    ("EWG",     "Germany ETF",       "NYSE"),
    ("EWU",     "UK ETF",            "NYSE"),
    ("EFA",     "Dev Mkt ETF",       "NYSE"),
    ("FXI",     "China Large Cap",   "NYSE"),
    ("TLT",     "20Y Bond ETF",      "NYSE"),
    ("IEF",     "7-10Y Bond ETF",    "NYSE"),
    ("SHY",     "1-3Y Bond ETF",     "NYSE"),
    ("HYG",     "High Yield ETF",    "NYSE"),
    ("LQD",     "Corp Bond ETF",     "NYSE"),
    ("TIP",     "TIPS ETF",          "NYSE"),
    ("EMB",     "EM Bond ETF",       "NYSE"),
    ("GLD",     "Gold ETF",          "NYSE"),
    ("SLV",     "Silver ETF",        "NYSE"),
    ("USO",     "Oil ETF",           "NYSE"),
    ("UNG",     "NatGas ETF",        "NYSE"),
    ("DBA",     "Agri ETF",          "NYSE"),
    ("CPER",    "Copper ETF",        "NYSE"),
    ("QDV5.DE", "MSCI India DE",     "XETRA"),
    ("EXS1.DE", "EuroStoxx50",       "XETRA"),
    ("DBXD.DE", "DAX ETF",           "XETRA"),
    ("EXXT.DE", "Nasdaq DE",         "XETRA"),
    ("EXW1.DE", "MSCI World DE",     "XETRA"),
    ("IBCK.DE", "Bond Corp EUR",     "XETRA"),
    ("IWDA.AS", "MSCI World",        "XAMS"),
    ("VUSA.AS", "S&P500 EUR",        "XAMS"),
    ("CSPX.AS", "S&P500 EUR Acc",    "XAMS"),
    ("EQQQ.DE", "Nasdaq EUR",        "XETRA"),
    ("XDWD.DE", "MSCI World EUR",    "XETRA"),
]

# ── FX ───────────────────────────────────────────────────────
FX = [
    ("EURUSD=X", "EUR/USD",        "FX"),
    ("GBPUSD=X", "GBP/USD",        "FX"),
    ("USDJPY=X", "USD/JPY",        "FX"),
    ("AUDUSD=X", "AUD/USD",        "FX"),
    ("USDCAD=X", "USD/CAD",        "FX"),
    ("USDCHF=X", "USD/CHF",        "FX"),
    ("NZDUSD=X", "NZD/USD",        "FX"),
    ("EURGBP=X", "EUR/GBP",        "FX"),
    ("EURJPY=X", "EUR/JPY",        "FX"),
    ("EURCHF=X", "EUR/CHF",        "FX"),
    ("EURAUD=X", "EUR/AUD",        "FX"),
    ("EURCAD=X", "EUR/CAD",        "FX"),
    ("EURNZD=X", "EUR/NZD",        "FX"),
    ("EURSEK=X", "EUR/SEK",        "FX"),
    ("EURNOK=X", "EUR/NOK",        "FX"),
    ("USDCNH=X", "USD/CNH",        "FX"),
    ("USDINR=X", "USD/INR",        "FX"),
    ("USDBRL=X", "USD/BRL",        "FX"),
    ("USDMXN=X", "USD/MXN",        "FX"),
    ("USDTRY=X", "USD/TRY",        "FX"),
    ("USDZAR=X", "USD/ZAR",        "FX"),
    ("GBPJPY=X", "GBP/JPY",        "FX"),
    ("GBPAUD=X", "GBP/AUD",        "FX"),
    ("AUDJPY=X", "AUD/JPY",        "FX"),
    ("CADJPY=X", "CAD/JPY",        "FX"),
    ("CHFJPY=X", "CHF/JPY",        "FX"),
    ("NZDJPY=X", "NZD/JPY",        "FX"),
    ("DX-Y.NYB", "Dollar Index",   "MACRO"),
    ("UUP",      "Dollar ETF",     "MACRO"),
    ("FXE",      "Euro ETF",       "MACRO"),
    ("FXY",      "Yen ETF",        "MACRO"),
    ("FXB",      "GBP ETF",        "MACRO"),
    ("FXA",      "AUD ETF",        "MACRO"),
    ("FXF",      "CHF ETF",        "MACRO"),
    ("FXC",      "CAD ETF",        "MACRO"),
]

# ── COMMODITIES ──────────────────────────────────────────────
COMMODITIES = [
    ("CL=F",  "WTI Crude",        "COMMODITY"),
    ("BZ=F",  "Brent Crude",      "COMMODITY"),
    ("NG=F",  "Natural Gas",      "COMMODITY"),
    ("RB=F",  "RBOB Gasoline",    "COMMODITY"),
    ("HO=F",  "Heating Oil",      "COMMODITY"),
    ("GC=F",  "Gold",             "COMMODITY"),
    ("SI=F",  "Silver",           "COMMODITY"),
    ("HG=F",  "Copper",           "COMMODITY"),
    ("PL=F",  "Platinum",         "COMMODITY"),
    ("PA=F",  "Palladium",        "COMMODITY"),
    ("ZC=F",  "Corn",             "COMMODITY"),
    ("ZW=F",  "Wheat",            "COMMODITY"),
    ("ZS=F",  "Soybeans",         "COMMODITY"),
    ("KC=F",  "Coffee",           "COMMODITY"),
    ("SB=F",  "Sugar",            "COMMODITY"),
    ("CC=F",  "Cocoa",            "COMMODITY"),
    ("CT=F",  "Cotton",           "COMMODITY"),
    ("OJ=F",  "Orange Juice",     "COMMODITY"),
    ("LBS=F", "Lumber",           "COMMODITY"),
    ("DBA",   "Agri ETF",         "COMMODITY"),
    ("SLV",   "Silver ETF",       "COMMODITY"),
    ("CPER",  "Copper ETF",       "COMMODITY"),
    ("UNG",   "NatGas ETF",       "COMMODITY"),
    ("GDX",   "Gold Miners ETF",  "COMMODITY"),
]

# ── VOLATILITY ───────────────────────────────────────────────
VOLATILITY = [
    ("^VIX",   "VIX S&P500",      "VOL"),
    ("^VXN",   "VXN Nasdaq",      "VOL"),
    ("^RVX",   "RVX Russell",     "VOL"),
    ("^VXD",   "VXD Dow",         "VOL"),
    ("^OVX",   "OVX Oil",         "VOL"),
    ("^GVZ",   "GVZ Gold",        "VOL"),
    ("^EVZ",   "EVZ Euro",        "VOL"),
    ("^VVIX",  "VVIX Vol of VIX", "VOL"),
    ("^SKEW",  "SKEW Tail Risk",  "VOL"),
    ("VXX",    "VIX ETF",         "VOL"),
]

# ── CRYPTO ───────────────────────────────────────────────────
CRYPTO = [
    ("BTC-USD",  "Bitcoin",        "CRYPTO"),
    ("ETH-USD",  "Ethereum",       "CRYPTO"),
    ("BNB-USD",  "BNB",            "CRYPTO"),
    ("SOL-USD",  "Solana",         "CRYPTO"),
    ("XRP-USD",  "XRP",            "CRYPTO"),
    ("ADA-USD",  "Cardano",        "CRYPTO"),
    ("AVAX-USD", "Avalanche",      "CRYPTO"),
    ("DOGE-USD", "Dogecoin",       "CRYPTO"),
    ("LINK-USD", "Chainlink",      "CRYPTO"),
    ("MATIC-USD","Polygon",        "CRYPTO"),
    ("UNI-USD",  "Uniswap",        "CRYPTO"),
    ("LTC-USD",  "Litecoin",       "CRYPTO"),
    ("NEAR-USD", "NEAR Protocol",  "CRYPTO"),
    ("ARB-USD",  "Arbitrum",       "CRYPTO"),
    ("SUI-USD",  "Sui",            "CRYPTO"),
]

# ── OPTIONS ──────────────────────────────────────────────────
OPTIONS_UNIVERSE = [
    ("SPY",      "S&P500",         "CBOE"),
    ("QQQ",      "Nasdaq",         "CBOE"),
    ("IWM",      "Russell 2000",   "CBOE"),
    ("NVDA",     "Nvidia",         "CBOE"),
    ("AAPL",     "Apple",          "CBOE"),
    ("MSFT",     "Microsoft",      "CBOE"),
    ("TSLA",     "Tesla",          "CBOE"),
    ("AMD",      "AMD",            "CBOE"),
    ("META",     "Meta",           "CBOE"),
    ("AMZN",     "Amazon",         "CBOE"),
    ("GLD",      "Gold ETF",       "CBOE"),
    ("TLT",      "20Y Bond",       "CBOE"),
    ("EEM",      "EM ETF",         "CBOE"),
    ("EXS1.DE",  "EuroStoxx",      "EUREX"),
    ("DBXD.DE",  "DAX ETF",        "EUREX"),
    ("IWDA.AS",  "MSCI World",     "EURONEXT"),
    ("VUSA.AS",  "S&P500 EUR",     "EURONEXT"),
    ("ASML.AS",  "ASML",           "EURONEXT"),
    ("ABI.BR",   "AB InBev",       "EURONEXT"),
    ("BCP.LS",   "BCP PSX",        "EURONEXT"),
    ("EDP.LS",   "EDP PSX",        "EURONEXT"),
    ("ENEL.MI",  "Enel",           "EURONEXT"),
    ("RACE.MI",  "Ferrari",        "EURONEXT"),
    ("AIR.PA",   "Airbus",         "EURONEXT"),
    ("MC.PA",    "LVMH",           "EURONEXT"),
    ("TTE.PA",   "TotalEnergies",  "EURONEXT"),
    ("SAN.MC",   "Santander",      "MEFF"),
    ("BBVA.MC",  "BBVA",           "MEFF"),
    ("ITX.MC",   "Inditex",        "MEFF"),
    ("NOVO-B.CO","Novo Nordisk",   "OMX"),
]

# ── COT CODES (CFTC) ─────────────────────────────────────────
# Código CFTC para cada ticker — usado em scanner_cot.py
COT_CODES = {
    "GC=F":    "088691",   # Gold
    "SI=F":    "084691",   # Silver
    "HG=F":    "085692",   # Copper
    "CL=F":    "067651",   # WTI Crude
    "NG=F":    "023651",   # Natural Gas
    "ZC=F":    "002602",   # Corn
    "ZW=F":    "001602",   # Wheat
    "ZS=F":    "005602",   # Soybeans
    "KC=F":    "083731",   # Coffee
    "SB=F":    "080732",   # Sugar
    "EURUSD=X":"099741",   # EUR/USD
    "GBPUSD=X":"096742",   # GBP/USD
    "USDJPY=X":"097741",   # JPY/USD
    "AUDUSD=X":"232741",   # AUD/USD
    "USDCAD=X":"090741",   # CAD/USD
    "USDCHF=X":"092741",   # CHF/USD
    "NZDUSD=X":"112741",   # NZD/USD
    "BTC-USD": "133741",   # Bitcoin
}

# ── UNIVERSO COMPLETO ────────────────────────────────────────
ALL = STOCKS + ETFS + FX + COMMODITIES + VOLATILITY + CRYPTO + OPTIONS_UNIVERSE