import requests
from datetime import datetime
import os
from claude_analyzer import analyze_news
from scanner_v2 import get_stock_universe_text, get_candidate_stocks_from_events
from memory_v2 import append_memory, load_recent_memory, build_memory_context
from idea_extractor import extract_ranked_tickers
from market_data import get_many_stock_snapshots
from scorer import score_many_stocks
from ai_stock_reasoner import generate_ai_stock_reasons
from report_generator import generate_report, save_report
from telegram_formatter import create_telegram_summary

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip()


def get_news():
    url = "https://newsapi.org/v2/top-headlines"

    params = {
        "country": "us",
        "apiKey": NEWS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    headlines = []

    if "articles" not in data:
        print("News API hatası:")
        print(data)
        return []

    for article in data["articles"]:
        title = article.get("title")
        if title:
            headlines.append(title)

    return headlines


def run_daily_analysis(send_telegram=False, telegram_sender_func=None):
    feedback_text = ""

    news = get_news()

    event_candidates = get_candidate_stocks_from_events(news)
    recent_memory = load_recent_memory("event_memory.json", limit=5)
    recent_memory_text = build_memory_context(recent_memory)
    stock_universe = get_stock_universe_text()

    analysis = analyze_news(news, stock_universe, recent_memory_text, feedback_text)

    extracted_ideas = extract_ranked_tickers(analysis, "us_stock_universe.json")
    ai_tickers = [item["ticker"] for item in extracted_ideas]
    event_tickers = event_candidates["tickers"]

    tickers = ai_tickers

    market_snapshots = get_many_stock_snapshots(tickers)
    scored_stocks = score_many_stocks(market_snapshots, extracted_ideas, event_tickers)

    ai_reasoned_stocks = generate_ai_stock_reasons(
        news=news,
        analysis=analysis,
        scored_stocks=scored_stocks,
        event_candidates=event_candidates,
        max_stocks=5
    )

    report_text = generate_report(news, analysis, scored_stocks, ai_reasoned_stocks)
    report_filename = save_report(report_text)

    telegram_summary = create_telegram_summary(ai_reasoned_stocks)

    telegram_result = None
    if send_telegram and telegram_sender_func:
        telegram_result = telegram_sender_func(telegram_summary)

    top_stocks_for_memory = scored_stocks[:3] if scored_stocks else []
    analysis_summary = analysis[:1200]

    append_memory("event_memory.json", {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "news": news[:10],
        "analysis_summary": analysis_summary,
        "tickers": tickers,
        "top_stocks": top_stocks_for_memory,
        "ai_reasoned_stocks": ai_reasoned_stocks,
        "report_file": report_filename
    })

    result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "news": news,
        "event_candidates": event_candidates,
        "analysis": analysis,
        "extracted_ideas": extracted_ideas,
        "tickers": tickers,
        "market_snapshots": market_snapshots,
        "scored_stocks": scored_stocks,
        "ai_reasoned_stocks": ai_reasoned_stocks,
        "telegram_summary": telegram_summary,
        "report_text": report_text,
        "report_filename": report_filename,
        "telegram_result": telegram_result
    }

    return result