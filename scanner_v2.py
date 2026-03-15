def get_sector_stock_map():
    return {
        "container shipping": ["ZIM", "MATX", "DAC"],
        "oil tanker": ["FRO", "TNK", "DHT", "INSW"],
        "defense": ["LMT", "RTX", "NOC", "LDOS", "LHX", "GD", "HII"],
        "insurance": ["ALL", "TRV", "CB", "PGR", "AIG"],
        "cybersecurity": ["CRWD", "PANW", "FTNT", "ZS", "S", "OKTA"],
        "semiconductors": ["NVDA", "AMD", "AVGO", "MU", "QCOM", "MRVL", "ARM", "TSM", "ASML", "AMAT", "LRCX", "KLAC"],
        "energy": ["XOM", "CVX", "COP", "SLB", "HAL", "EOG", "OXY"],
        "gold": ["NEM", "AEM", "GOLD", "AU"],
        "silver": ["PAAS", "WPM", "HL", "AG", "SILV", "MAG"],
        "airlines": ["DAL", "UAL", "AAL", "LUV"],
        "railroads": ["UNP", "CSX", "NSC"],
        "logistics": ["FDX", "UPS", "EXPD", "CHRW", "HUBG"],
        "freight": ["ODFL", "SAIA", "XPO", "ARCB"],
        "industrial": ["CAT", "DE", "ETN", "PH", "EMR", "TT", "JCI"],
        "natural gas": ["EQT", "AR", "RRC", "LNG", "CTRA"],
        "uranium and nuclear": ["CCJ", "LEU", "BWXT", "UEC", "UUUU", "SMR", "OKLO", "VST", "CEG", "GEV"],
        "steel": ["NUE", "STLD", "X", "CLF"],
        "commodities": ["ADM", "BG", "MOS", "NTR"],
        "utilities": ["NEE", "DUK", "SO", "CEG", "AEP", "EXC", "PEG"],
        "defense tech": ["PLTR", "KTOS", "AVAV", "RCAT"],
        "ship leasing": ["DAC"],
        "ports and marine": ["MATX", "KEX"],
        "data centers and power": ["VRT", "ETN", "CEG", "VST", "GEV", "DLR", "EQIX"],
        "copper and electrification": ["FCX", "SCCO", "TECK", "BHP"],
        "ai servers and infrastructure": ["DELL", "SMCI", "ANET", "VRT"],
        "clean energy and grid": ["NRG", "TLN", "CEG", "VST", "NEE", "GEV"],
        "quantum computing": ["IONQ", "RGTI", "QBTS", "QUBT"],
        "advanced chips and chip tools": ["NVDA", "AMD", "AVGO", "ARM", "TSM", "ASML", "AMAT", "LRCX", "KLAC", "MU"]
    }


def get_event_sector_map():
    return {
        "middle east escalation": ["energy", "oil tanker", "defense"],
        "oil supply disruption": ["energy", "oil tanker", "natural gas"],
        "war escalation": ["defense", "energy", "oil tanker"],
        "cyber attack": ["cybersecurity", "defense tech"],
        "power grid stress": ["uranium and nuclear", "utilities", "data centers and power", "clean energy and grid"],
        "ai semiconductor demand": ["advanced chips and chip tools", "semiconductors", "ai servers and infrastructure", "data centers and power"],
        "freight disruption": ["container shipping", "logistics", "freight", "ports and marine"],
        "industrial rebuild": ["industrial", "steel", "copper and electrification"],
        "higher insurance losses": ["insurance"],
        "safe haven metals": ["gold", "silver"],
    }


def get_stock_universe_text():
    universe = get_sector_stock_map()

    lines = []
    for sector, stocks in universe.items():
        lines.append(f"{sector}: {', '.join(stocks)}")

    return "\n".join(lines)


def detect_event_types_from_news(news_list):
    text = " ".join(news_list).lower()
    detected = []

    keyword_map = {
        "middle east escalation": ["iran", "israel", "middle east", "hezbollah", "red sea", "hormuz"],
        "oil supply disruption": ["oil", "crude", "supply disruption", "pipeline", "opec"],
        "war escalation": ["attack", "missile", "war", "drone strike", "air strike", "troops"],
        "cyber attack": ["cyber", "hack", "ransomware", "data breach"],
        "power grid stress": ["blackout", "grid", "electricity shortage", "power shortage"],
        "ai semiconductor demand": ["ai chip", "semiconductor", "gpu", "data center"],
        "freight disruption": ["shipping", "freight", "container", "port", "logistics"],
        "industrial rebuild": ["rebuild", "construction", "infrastructure", "factory"],
        "higher insurance losses": ["insured losses", "catastrophe losses", "hurricane losses"],
        "safe haven metals": ["gold", "bullion", "silver", "safe haven"],
    }

    for event_name, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in text:
                detected.append(event_name)
                break

    return list(dict.fromkeys(detected))


def get_candidate_stocks_from_events(news_list):
    event_sector_map = get_event_sector_map()
    sector_stock_map = get_sector_stock_map()

    detected_events = detect_event_types_from_news(news_list)

    candidate_stocks = []
    matched_sectors = []

    for event in detected_events:
        sectors = event_sector_map.get(event, [])
        for sector in sectors:
            if sector not in matched_sectors:
                matched_sectors.append(sector)

            for ticker in sector_stock_map.get(sector, []):
                if ticker not in candidate_stocks:
                    candidate_stocks.append(ticker)

    return {
        "events": detected_events,
        "sectors": matched_sectors,
        "tickers": candidate_stocks
    }