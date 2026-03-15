def score_stock(snapshot, extracted_idea=None, event_tickers=None):
    score = 0
    reasons = []

    price_change = snapshot.get("price_change_pct", 0)
    volume_ratio = snapshot.get("volume_ratio", 0)
    ticker = snapshot.get("ticker", "")

    extract_score = 0
    extract_reasons = []
    event_supported = False

    if extracted_idea:
        extract_score = extracted_idea.get("extract_score", 0)
        extract_reasons = extracted_idea.get("extract_reasons", [])

    if event_tickers and ticker in event_tickers:
        event_supported = True

    # 1) AI extraction gücü
    if extract_score >= 8:
        score += 4
        reasons.append("AI analizinde çok güçlü çıktı")
    elif extract_score >= 5:
        score += 3
        reasons.append("AI analizinde güçlü çıktı")
    elif extract_score >= 3:
        score += 2
        reasons.append("AI analizinde orta güçte çıktı")
    elif extract_score > 0:
        score += 1
        reasons.append("AI analizinde geçti")

    # 2) Event desteği varsa bonus
    if event_supported:
        score += 2
        reasons.append("Event zinciri tarafından destekleniyor")

    # 3) Günlük fiyat hareketi
    if price_change >= 2:
        score += 3
        reasons.append("Fiyat güçlü pozitif")
    elif price_change > 0:
        score += 2
        reasons.append("Fiyat pozitif")
    elif price_change > -1:
        score += 1
        reasons.append("Fiyat çok zayıf değil")
    else:
        reasons.append("Fiyat zayıf")

    # 4) Hacim oranı
    if volume_ratio >= 1.5:
        score += 3
        reasons.append("Hacim güçlü şekilde ortalamanın üstünde")
    elif volume_ratio >= 1.2:
        score += 2
        reasons.append("Hacim ortalamanın üstünde")
    elif volume_ratio >= 1.0:
        score += 1
        reasons.append("Hacim normalin biraz üstünde")
    else:
        reasons.append("Hacim zayıf")

    return {
        "ticker": ticker,
        "score": score,
        "reasons": reasons,
        "last_close": snapshot.get("last_close"),
        "price_change_pct": price_change,
        "volume_ratio": volume_ratio,
        "extract_score": extract_score,
        "extract_reasons": extract_reasons,
        "event_supported": event_supported
    }


def score_many_stocks(market_snapshots, extracted_ideas, event_tickers=None):
    scored = []

    idea_map = {}
    for idea in extracted_ideas:
        idea_map[idea["ticker"]] = idea

    for snapshot in market_snapshots:
        ticker = snapshot.get("ticker", "")
        extracted_idea = idea_map.get(ticker)
        scored.append(score_stock(snapshot, extracted_idea, event_tickers))

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored