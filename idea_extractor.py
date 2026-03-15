import json
import re
from collections import defaultdict


TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")


def load_stock_universe(universe_file):
    with open(universe_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    universe = {}
    for item in data:
        symbol = item.get("symbol", "").strip().upper()
        if symbol:
            universe[symbol] = item

    return universe


def build_sector_map():
    return {
        "oil and energy": ["XOM", "CVX", "COP", "SLB", "HAL", "EOG", "OXY", "CTRA", "AR", "EQT", "LNG"],
        "oil tankers": ["FRO", "TNK", "DHT", "INSW"],
        "defense and aerospace": ["LMT", "RTX", "NOC", "GD", "LHX", "LDOS", "HII"],
        "insurance": ["ALL", "TRV", "CB", "AIG", "PGR"],
        "cybersecurity": ["CRWD", "PANW", "FTNT", "ZS", "S"],
        "uranium and nuclear": ["CCJ", "LEU", "BWXT", "UEC", "UUUU", "SMR", "OKLO", "VST", "CEG", "GEV"],
        "advanced chips and chip tools": ["NVDA", "AMD", "AVGO", "QCOM", "MRVL", "AMAT", "LRCX", "KLAC", "MU"],
        "shipping and container lines": ["ZIM", "MATX", "DAC"],
        "industrial machinery": ["CAT", "ETN", "EMR", "PH", "DE"],
        "logistics and freight": ["FDX", "UPS", "CHRW", "ODFL", "SAIA"],
        "steel": ["NUE", "STLD", "X", "CLF"],
        "defense tech": ["PLTR", "KTOS", "AVAV", "RCAT"],
    }


def normalize_text(text):
    return text.replace("**", "").replace("—", "-").replace("–", "-")


def split_sections(text):
    text = normalize_text(text)

    headers = [
        "SUMMARY OF MAIN EVENT:",
        "DIRECTLY AFFECTED INDUSTRIES:",
        "SECOND-ORDER OPPORTUNITIES:",
        "THIRD-ORDER OPPORTUNITIES:",
        "RECURRING THEMES VS RECENT MEMORY:",
        "LESSONS FROM PAST STOCK IDEA PERFORMANCE:",
        "RISKS / WHY THE IDEA COULD FAIL:",
        "BEST 3 IDEAS TODAY:"
    ]

    sections = {}

    for i, header in enumerate(headers):
        start = text.find(header)
        if start == -1:
            continue

        end = len(text)

        for next_header in headers[i + 1:]:
            next_pos = text.find(next_header, start + len(header))
            if next_pos != -1:
                end = next_pos
                break

        sections[header] = text[start:end].strip()

    return sections


def extract_tickers_from_line(line, valid_tickers):
    candidates = TICKER_RE.findall(line.upper())
    return [c for c in candidates if c in valid_tickers]


def detect_sector_context(block, sector_map):
    block_lower = block.lower()
    matched = set()

    for sector_name, tickers in sector_map.items():
        if sector_name in block_lower:
            matched.update(tickers)

    return matched


def extract_ranked_tickers(analysis_text, universe_file):
    universe = load_stock_universe(universe_file)
    valid_tickers = set(universe.keys())
    sector_map = build_sector_map()
    sections = split_sections(analysis_text)

    scores = defaultdict(int)
    reasons = defaultdict(list)

    best_ideas = sections.get("BEST 3 IDEAS TODAY:", "")
    for line in best_ideas.splitlines():
        found = extract_tickers_from_line(line, valid_tickers)
        for ticker in found:
            scores[ticker] += 5
            reasons[ticker].append("BEST 3 IDEAS bölümünde geçti")

    for section_name in [
        "DIRECTLY AFFECTED INDUSTRIES:",
        "SECOND-ORDER OPPORTUNITIES:",
        "THIRD-ORDER OPPORTUNITIES:"
    ]:
        block = sections.get(section_name, "")
        if not block:
            continue

        current_sector_support = detect_sector_context(block, sector_map)

        for line in block.splitlines():
            if "Possible U.S. stocks" in line:
                found = extract_tickers_from_line(line, valid_tickers)
                for ticker in found:
                    scores[ticker] += 4
                    reasons[ticker].append(f"{section_name} içinde Possible U.S. stocks satırında geçti")

                    if ticker in current_sector_support:
                        scores[ticker] += 1
                        reasons[ticker].append("Sektör bağlamı ile desteklendi")

    whole_text_found = extract_tickers_from_line(analysis_text, valid_tickers)
    for ticker in whole_text_found:
        scores[ticker] += 1
        reasons[ticker].append("Serbest metinde geçti")

    ambiguous_tickers = {"A", "I", "IT", "ON"}
    for bad in ambiguous_tickers:
        if bad in scores:
            del scores[bad]
            del reasons[bad]

    results = []
    for ticker, score in scores.items():
        unique_reasons = list(dict.fromkeys(reasons[ticker]))
        results.append({
            "ticker": ticker,
            "extract_score": score,
            "extract_reasons": unique_reasons,
            "description": universe[ticker].get("description", "")
        })

    results.sort(key=lambda x: (-x["extract_score"], x["ticker"]))
    return results