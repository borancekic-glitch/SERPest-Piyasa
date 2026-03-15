import json
import os
from datetime import datetime, timedelta

import anthropic
import requests
import yfinance as yf

CACHE_FILE = os.path.join("data", "stock_ai_cache.json")
CACHE_HOURS = 6
NEWS_API_URL = "https://newsapi.org/v2/everything"


def load_json_file(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(filename, data):
    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_cache():
    return load_json_file(CACHE_FILE, {})


def save_cache(data):
    save_json_file(CACHE_FILE, data)


def get_cached_analysis(ticker):
    cache = load_cache()
    item = cache.get(ticker.upper())

    if not item:
        return None

    created_at = item.get("created_at")
    if not created_at:
        return None

    try:
        created_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    if datetime.utcnow() - created_dt > timedelta(hours=CACHE_HOURS):
        return None

    return item.get("analysis")


def set_cached_analysis(ticker, analysis_data):
    cache = load_cache()
    cache[ticker.upper()] = {
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis": analysis_data
    }
    save_cache(cache)


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def pct_change(current_value, base_value):
    if current_value is None or base_value in (None, 0):
        return None
    try:
        return round(((current_value - base_value) / base_value) * 100, 2)
    except Exception:
        return None


def get_price_context(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty:
            return {
                "last_close": None,
                "change_1m_pct": None,
                "change_2m_pct": None,
                "change_3m_pct": None,
                "change_6m_pct": None,
                "high_1y": None,
                "low_1y": None
            }

        last_close = float(hist["Close"].iloc[-1])

        def get_close_days_ago(days):
            if len(hist) <= days:
                return float(hist["Close"].iloc[0])
            return float(hist["Close"].iloc[-days - 1])

        close_1m = get_close_days_ago(21)
        close_2m = get_close_days_ago(42)
        close_3m = get_close_days_ago(63)
        close_6m = get_close_days_ago(126)

        return {
            "last_close": round(last_close, 2),
            "change_1m_pct": pct_change(last_close, close_1m),
            "change_2m_pct": pct_change(last_close, close_2m),
            "change_3m_pct": pct_change(last_close, close_3m),
            "change_6m_pct": pct_change(last_close, close_6m),
            "high_1y": round(float(hist["High"].max()), 2),
            "low_1y": round(float(hist["Low"].min()), 2)
        }
    except Exception:
        return {
            "last_close": None,
            "change_1m_pct": None,
            "change_2m_pct": None,
            "change_3m_pct": None,
            "change_6m_pct": None,
            "high_1y": None,
            "low_1y": None
        }


def get_fundamental_context(ticker):
    data = {
        "market_cap": None,
        "trailing_pe": None,
        "forward_pe": None,
        "price_to_book": None,
        "profit_margins": None,
        "operating_margins": None,
        "revenue_growth": None,
        "earnings_growth": None,
        "return_on_equity": None,
        "debt_to_equity": None,
        "current_ratio": None,
        "quick_ratio": None,
        "free_cashflow": None,
        "total_cash": None,
        "total_debt": None,
        "recommendation_key": None,
        "target_mean_price": None,
        "current_price": None,
        "fifty_two_week_high": None,
        "fifty_two_week_low": None,
        "beta": None,
        "sector": None,
        "industry": None
    }

    try:
        stock = yf.Ticker(ticker)
        info = getattr(stock, "info", {}) or {}

        data["market_cap"] = safe_float(info.get("marketCap"))
        data["trailing_pe"] = safe_float(info.get("trailingPE"))
        data["forward_pe"] = safe_float(info.get("forwardPE"))
        data["price_to_book"] = safe_float(info.get("priceToBook"))
        data["profit_margins"] = safe_float(info.get("profitMargins"))
        data["operating_margins"] = safe_float(info.get("operatingMargins"))
        data["revenue_growth"] = safe_float(info.get("revenueGrowth"))
        data["earnings_growth"] = safe_float(info.get("earningsGrowth"))
        data["return_on_equity"] = safe_float(info.get("returnOnEquity"))
        data["debt_to_equity"] = safe_float(info.get("debtToEquity"))
        data["current_ratio"] = safe_float(info.get("currentRatio"))
        data["quick_ratio"] = safe_float(info.get("quickRatio"))
        data["free_cashflow"] = safe_float(info.get("freeCashflow"))
        data["total_cash"] = safe_float(info.get("totalCash"))
        data["total_debt"] = safe_float(info.get("totalDebt"))
        data["recommendation_key"] = info.get("recommendationKey")
        data["target_mean_price"] = safe_float(info.get("targetMeanPrice"))
        data["current_price"] = safe_float(info.get("currentPrice"))
        data["fifty_two_week_high"] = safe_float(info.get("fiftyTwoWeekHigh"))
        data["fifty_two_week_low"] = safe_float(info.get("fiftyTwoWeekLow"))
        data["beta"] = safe_float(info.get("beta"))
        data["sector"] = info.get("sector")
        data["industry"] = info.get("industry")
    except Exception:
        pass

    return data


def build_sector_keywords(stock):
    sector = str(stock.get("sector", "")).lower()
    theme = str(stock.get("theme", "")).lower()
    symbol = str(stock.get("symbol", "")).upper()

    keywords = []

    if "energy" in sector or "lng" in theme or symbol == "LNG":
        keywords += [
            "LNG exports", "natural gas prices", "LNG terminal", "shipping rates",
            "energy demand", "Europe gas demand", "Asia LNG demand"
        ]

    if "defense" in sector:
        keywords += [
            "defense spending", "missile demand", "military contracts", "geopolitical tension"
        ]

    if "cyber" in sector:
        keywords += [
            "cybersecurity spending", "data breach", "zero trust", "enterprise security demand"
        ]

    if "logistics" in sector or "shipping" in theme or symbol in {"FRO", "TNK", "DHT", "INSW"}:
        keywords += [
            "tanker rates", "shipping disruption", "oil routes", "freight demand",
            "maritime security", "port congestion", "Middle East shipping"
        ]

    if "semiconductors" in sector or "chip" in theme:
        keywords += [
            "AI chip demand", "data center spending", "semiconductor pricing", "foundry supply"
        ]

    return keywords[:6]


def get_yfinance_news_lines(ticker, max_items=4):
    lines = []

    try:
        stock = yf.Ticker(ticker)
        news_items = getattr(stock, "news", []) or []

        for item in news_items[:max_items]:
            title = item.get("title") or item.get("content", {}).get("title")
            publisher = item.get("publisher") or item.get("content", {}).get("provider", {}).get("displayName")
            if not title:
                continue

            line = f"- {title}"
            if publisher:
                line += f" ({publisher})"
            lines.append(line)
    except Exception:
        pass

    return lines


def build_news_queries(stock):
    symbol = str(stock.get("symbol", "")).upper().strip()
    name = str(stock.get("name", symbol)).strip()
    sector = str(stock.get("sector", "")).strip()
    theme = str(stock.get("theme", "")).strip()

    queries = [
        f'"{name}" OR {symbol}',
        f'("{name}" OR {symbol}) AND (earnings OR revenue OR guidance OR outlook OR margin OR demand)',
        f'("{name}" OR {symbol}) AND (contract OR expansion OR regulation OR management OR strategy)'
    ]

    if sector:
        queries.append(f'"{sector}" AND (outlook OR demand OR pricing OR regulation OR supply chain)')

    if theme:
        queries.append(f'"{theme}" AND (demand OR pricing OR regulation OR adoption OR spending)')

    for keyword in build_sector_keywords(stock):
        queries.append(keyword)

    unique_queries = []
    seen = set()

    for query in queries:
        if query not in seen:
            seen.add(query)
            unique_queries.append(query)

    return unique_queries[:7]


def search_newsapi_articles(stock, max_articles=16):
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    if not api_key:
        return []

    queries = build_news_queries(stock)
    all_articles = []
    seen_urls = set()
    from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    for query in queries[:5]:
        try:
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 6,
                "from": from_date,
                "apiKey": api_key
            }

            response = requests.get(NEWS_API_URL, params=params, timeout=20)
            data = response.json()

            for article in data.get("articles", []):
                url = article.get("url")
                title = article.get("title")
                source_name = (article.get("source") or {}).get("name")
                published_at = article.get("publishedAt")

                if not title or not url or url in seen_urls:
                    continue

                seen_urls.add(url)
                all_articles.append({
                    "title": title,
                    "source": source_name,
                    "published_at": published_at,
                    "url": url,
                    "description": article.get("description", "")
                })

                if len(all_articles) >= max_articles:
                    return all_articles
        except Exception:
            continue

    return all_articles[:max_articles]


def article_relevance_score(article, stock):
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()

    score = 0
    symbol = str(stock.get("symbol", "")).lower()
    name = str(stock.get("name", "")).lower()
    sector = str(stock.get("sector", "")).lower()
    theme = str(stock.get("theme", "")).lower()

    if symbol and symbol in text:
        score += 4
    if name and name in text:
        score += 5
    if sector and sector in text:
        score += 2
    if theme and theme in text:
        score += 2

    for keyword in build_sector_keywords(stock):
        if keyword.lower() in text:
            score += 2

    important_terms = [
        "earnings", "guidance", "demand", "margin", "growth", "outlook",
        "pricing", "regulation", "contract", "expansion", "rates",
        "shipping", "oil", "lng", "war", "sanctions", "freight", "supply chain"
    ]
    for term in important_terms:
        if term in text:
            score += 1

    return score


def collect_relevant_news(stock, max_lines=10):
    newsapi_articles = search_newsapi_articles(stock, max_articles=16)

    scored_articles = sorted(
        newsapi_articles,
        key=lambda item: article_relevance_score(item, stock),
        reverse=True
    )

    lines = []
    used_titles = set()

    for article in scored_articles:
        title = article.get("title", "").strip()
        if not title or title in used_titles:
            continue

        used_titles.add(title)

        line = f"- {title}"
        if article.get("source"):
            line += f" ({article['source']})"
        if article.get("published_at"):
            line += f" | {article['published_at']}"

        lines.append(line)

        if len(lines) >= max_lines:
            break

    for line in get_yfinance_news_lines(stock.get("symbol", ""), max_items=4):
        if len(lines) >= max_lines:
            break
        if line not in lines:
            lines.append(line)

    return lines[:max_lines]


def decide_direction(latest_signal, market_data, price_context, fundamentals):
    positive = 0
    negative = 0

    score = latest_signal.get("score") if latest_signal else None
    if score is not None and score >= 8:
        positive += 2
    elif score is not None and score <= 3:
        negative += 1

    if price_context.get("change_2m_pct") is not None and price_context["change_2m_pct"] > 0:
        positive += 1
    elif price_context.get("change_2m_pct") is not None and price_context["change_2m_pct"] < -8:
        negative += 1

    if market_data.get("volume_ratio") is not None and market_data["volume_ratio"] >= 1.15:
        positive += 1
    elif market_data.get("volume_ratio") is not None and market_data["volume_ratio"] < 0.9:
        negative += 1

    revenue_growth = fundamentals.get("revenue_growth")
    earnings_growth = fundamentals.get("earnings_growth")
    debt_to_equity = fundamentals.get("debt_to_equity")

    if revenue_growth is not None and revenue_growth > 0:
        positive += 1
    elif revenue_growth is not None and revenue_growth < 0:
        negative += 1

    if earnings_growth is not None and earnings_growth > 0:
        positive += 1
    elif earnings_growth is not None and earnings_growth < 0:
        negative += 1

    if debt_to_equity is not None and debt_to_equity > 200:
        negative += 1

    if positive >= negative + 2:
        return "Yükseliş"
    if negative >= positive + 2:
        return "Düşüş"
    if abs(positive - negative) <= 1:
        return "Sabit"
    return "Değişken"


def build_fallback_analysis(stock, market_data, latest_signal, price_context, fundamentals, news_lines):
    direction = decide_direction(latest_signal, market_data, price_context, fundamentals)

    macro_sector_reasons = []
    company_reasons = []
    financial_reasons = []

    if stock.get("theme"):
        macro_sector_reasons.append(
            f"{stock['theme']} temasıyla ilgili gelişmeler önümüzdeki 1-2 ayda hisseyi etkileyebilir."
        )

    if stock.get("sector"):
        macro_sector_reasons.append(
            f"{stock['sector']} sektöründeki haber akışı ve fiyatlama şirket algısını değiştirebilir."
        )

    if news_lines:
        macro_sector_reasons.append(
            "Toplanan haberlerde şirketi veya sektörünü etkileyebilecek güncel başlıklar bulunuyor."
        )

    if latest_signal and latest_signal.get("event_supported"):
        company_reasons.append("Son sinyalde hisse, olay zinciri tarafından desteklenen adaylardan biri olarak görünüyor.")

    if market_data.get("volume_ratio") is not None:
        vr = market_data["volume_ratio"]
        if vr >= 1.15:
            company_reasons.append("Hacim ortalamanın üzerinde, piyasada ilgi artışı olabilir.")
        elif vr < 0.9:
            company_reasons.append("Hacim zayıf, bu da hareketin gücünü sınırlayabilir.")

    if price_context.get("change_2m_pct") is not None:
        ch = price_context["change_2m_pct"]
        if ch > 0:
            company_reasons.append("Son 2 aylık fiyat eğilimi pozitif tarafta.")
        elif ch < 0:
            company_reasons.append("Son 2 aylık fiyat eğilimi zayıf tarafta.")

    if fundamentals.get("revenue_growth") is not None:
        if fundamentals["revenue_growth"] > 0:
            financial_reasons.append("Gelir büyümesi pozitif görünüyor.")
        else:
            financial_reasons.append("Gelir büyümesi zayıf veya negatif.")

    if fundamentals.get("earnings_growth") is not None:
        if fundamentals["earnings_growth"] > 0:
            financial_reasons.append("Kârlılık büyümesi destekleyici olabilir.")
        else:
            financial_reasons.append("Kârlılık tarafında baskı olabilir.")

    if fundamentals.get("debt_to_equity") is not None:
        if fundamentals["debt_to_equity"] > 200:
            financial_reasons.append("Borçluluk seviyesi risk oluşturabilir.")
        else:
            financial_reasons.append("Borçluluk yapısı aşırı sorunlu görünmüyor.")

    if not financial_reasons:
        financial_reasons.append("Finansal veriler sınırlı olsa da şirketin temel yapısı tek başına aşırı negatif görünmüyor.")

    direction_note_map = {
        "Yükseliş": "Mevcut veriler, önümüzdeki 1-2 ayda yukarı yönlü eğilimin daha olası olduğunu gösteriyor.",
        "Düşüş": "Mevcut veriler, önümüzdeki 1-2 ayda aşağı yönlü baskının daha olası olduğunu gösteriyor.",
        "Sabit": "Mevcut veriler, önümüzdeki 1-2 ayda belirgin bir yön yerine daha dengeli bir görünüm gösteriyor.",
        "Değişken": "Mevcut veriler, önümüzdeki 1-2 ayda yönün haber akışına bağlı olarak sert şekilde değişebileceğini gösteriyor."
    }

    return {
        "ticker": stock.get("symbol", ""),
        "company_name": stock.get("name", stock.get("symbol", "")),
        "time_horizon": "1-2 ay",
        "predicted_direction": direction,
        "direction_summary": direction_note_map[direction],
        "macro_sector_reasons": macro_sector_reasons[:4],
        "company_reasons": company_reasons[:4],
        "financial_reasons": financial_reasons[:4],
        "news_used": news_lines[:8],
        "fundamental_snapshot": fundamentals,
        "premium_note": "Bu analiz 1-2 aylık görünüm içindir ve bilgilendirme amaçlıdır."
    }


def parse_ai_response(text, ticker, stock, fundamentals, news_lines):
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(cleaned)
    except Exception:
        return {
            "ticker": ticker,
            "company_name": stock.get("name", ticker),
            "time_horizon": "1-2 ay",
            "predicted_direction": "Değişken",
            "direction_summary": cleaned[:1000],
            "macro_sector_reasons": [],
            "company_reasons": [],
            "financial_reasons": [],
            "news_used": news_lines[:8],
            "fundamental_snapshot": fundamentals,
            "premium_note": "Bu analiz AI çıktısından dönüştürüldü."
        }

    return {
        "ticker": ticker,
        "company_name": data.get("company_name", stock.get("name", ticker)),
        "time_horizon": data.get("time_horizon", "1-2 ay"),
        "predicted_direction": data.get("predicted_direction", "Değişken"),
        "direction_summary": data.get("direction_summary", ""),
        "macro_sector_reasons": data.get("macro_sector_reasons", []),
        "company_reasons": data.get("company_reasons", []),
        "financial_reasons": data.get("financial_reasons", []),
        "news_used": news_lines[:8],
        "fundamental_snapshot": fundamentals,
        "premium_note": data.get("premium_note", "Bu analiz bilgilendirme amaçlıdır.")
    }


def generate_stock_ai_analysis(stock, market_data, latest_signal=None, force_refresh=False):
    ticker = str(stock.get("symbol", "")).upper().strip()

    if not ticker:
        return {
            "status": "error",
            "message": "Geçersiz ticker."
        }

    if not force_refresh:
        cached = get_cached_analysis(ticker)
        if cached:
            return {
                "status": "ok",
                "source": "cache",
                "analysis": cached
            }

    price_context = get_price_context(ticker)
    fundamentals = get_fundamental_context(ticker)
    news_lines = collect_relevant_news(stock, max_lines=10)

    api_key = os.getenv("CLAUDE_API_KEY", "").strip()

    if not api_key:
        fallback = build_fallback_analysis(
            stock=stock,
            market_data=market_data,
            latest_signal=latest_signal or {},
            price_context=price_context,
            fundamentals=fundamentals,
            news_lines=news_lines
        )
        set_cached_analysis(ticker, fallback)
        return {
            "status": "ok",
            "source": "fallback",
            "analysis": fallback
        }

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""
Sen elit seviyede makro + sektör + şirket + finansal yapı analizi yapan bir hisse araştırma analistisin.

Görev:
Seçilen Amerikan hissesini önümüzdeki 1-2 ay için değerlendir.

Zorunlu analiz yöntemi:
1. Şirketi doğrudan etkileyen haberleri değerlendir.
2. Şirketin sektörünü veya temasını dolaylı etkileyen haberleri değerlendir.
3. Şirketin aldığı kararlar, sözleşmeler, genişleme planları, yönetim kararları gibi şirket özel unsurları ayır.
4. Şirketin finansal yapısını ayrı değerlendir.
5. Sonuç tek cümlelik genel yorum değil, aşağıdaki formatta net sınıflandırılmış olsun.

Kurallar:
- Çıktı sadece JSON olsun.
- Tahmin ufku net biçimde 1-2 ay olsun.
- predicted_direction alanı sadece şu 4 değerden biri olsun:
  "Yükseliş", "Düşüş", "Sabit", "Değişken"
- macro_sector_reasons sadece sektör / tema / makro haber etkilerini anlatsın.
- company_reasons sadece şirket özel gelişmeleri veya hisseye özgü nedenleri anlatsın.
- financial_reasons sadece şirketin genel finansal durumuna dayalı nedenleri anlatsın.

Hisse Bilgileri:
Ticker: {ticker}
Şirket adı: {stock.get("name", ticker)}
Sektör: {stock.get("sector", "Unknown")}
Tema: {stock.get("theme", "")}
Açıklama: {stock.get("description", "")}

Güncel Piyasa Snapshot:
{json.dumps(market_data, ensure_ascii=False)}

Fiyat Bağlamı:
{json.dumps(price_context, ensure_ascii=False)}

Temel Finansal Görünüm:
{json.dumps(fundamentals, ensure_ascii=False)}

Son sinyal verisi:
{json.dumps(latest_signal or {}, ensure_ascii=False)}

Toplanan ilgili haberler:
{chr(10).join(news_lines) if news_lines else "- İlgili haber bulunamadı"}

Sadece şu formatta JSON üret:
{{
  "company_name": "...",
  "time_horizon": "1-2 ay",
  "predicted_direction": "Yükseliş / Düşüş / Sabit / Değişken",
  "direction_summary": "Önümüzdeki 1-2 ay için yönün neden böyle göründüğünü açıklayan 2-4 cümle",
  "macro_sector_reasons": [
    "sektörü veya temayı etkileyen haber bazlı neden 1",
    "sektörü veya temayı etkileyen haber bazlı neden 2",
    "sektörü veya temayı etkileyen haber bazlı neden 3"
  ],
  "company_reasons": [
    "şirket özel gelişmesi veya şirket bazlı neden 1",
    "şirket özel gelişmesi veya şirket bazlı neden 2",
    "şirket özel gelişmesi veya şirket bazlı neden 3"
  ],
  "financial_reasons": [
    "finansal yapıdan gelen neden 1",
    "finansal yapıdan gelen neden 2",
    "finansal yapıdan gelen neden 3"
  ],
  "premium_note": "Kısa not"
}}
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1200,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        text = response.content[0].text
        analysis_data = parse_ai_response(
            text=text,
            ticker=ticker,
            stock=stock,
            fundamentals=fundamentals,
            news_lines=news_lines
        )

        set_cached_analysis(ticker, analysis_data)

        return {
            "status": "ok",
            "source": "ai",
            "analysis": analysis_data
        }

    except Exception:
        fallback = build_fallback_analysis(
            stock=stock,
            market_data=market_data,
            latest_signal=latest_signal or {},
            price_context=price_context,
            fundamentals=fundamentals,
            news_lines=news_lines
        )
        set_cached_analysis(ticker, fallback)

        return {
            "status": "ok",
            "source": "fallback",
            "analysis": fallback
        }