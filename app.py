from flask import Flask, jsonify, render_template, request
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("CLAUDE loaded:", bool(os.getenv("CLAUDE_API_KEY")))
print("NEWS loaded:", bool(os.getenv("NEWS_API_KEY")))
print("ENV exists:", env_path.exists())

from engine import run_daily_analysis
from market_data import get_stock_snapshot, get_stock_chart_data
from stock_ai_analysis import generate_stock_ai_analysis
from telegram_sender import send_long_telegram_message
from signal_forge import (
    run_signal_forge_latest,
    load_backtest_results,
    summarize_signal_forge_results
)

app = Flask(__name__, template_folder="templates", static_folder="static")

REPORTS_DB_FILE = "reports_db.json"
STOCK_UNIVERSE_FILE = "us_stock_universe.json"
TRACKED_STOCKS_FILE = os.path.join("data", "tracked_stocks.json")
WEEKLY_PICKS_FILE = os.path.join("data", "weekly_picks.json")


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


def load_reports_db():
    return load_json_file(REPORTS_DB_FILE, [])


def save_reports_db(data):
    save_json_file(REPORTS_DB_FILE, data)


def load_stock_universe():
    raw = load_json_file(STOCK_UNIVERSE_FILE, [])
    result = {}

    for item in raw:
        symbol = str(item.get("symbol", "")).strip().upper()
        if symbol:
            result[symbol] = {
                "symbol": symbol,
                "description": item.get("description", ""),
                "type": item.get("type", "Common Stock")
            }

    return result


def load_tracked_stocks():
    raw = load_json_file(TRACKED_STOCKS_FILE, [])
    result = []

    for item in raw:
        symbol = str(item.get("symbol", "")).strip().upper()
        if not symbol:
            continue

        result.append({
            "symbol": symbol,
            "name": item.get("name", symbol),
            "sector": item.get("sector", "Unknown"),
            "theme": item.get("theme", ""),
            "description": item.get("description", "")
        })

    return result


def load_weekly_picks():
    return load_json_file(WEEKLY_PICKS_FILE, {})


def save_run_result(result):
    reports = load_reports_db()

    db_item = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "date": result.get("date"),
        "news": result.get("news", []),
        "event_candidates": result.get("event_candidates", {}),
        "analysis": result.get("analysis", ""),
        "scored_stocks": result.get("scored_stocks", []),
        "ai_reasoned_stocks": result.get("ai_reasoned_stocks", []),
        "telegram_summary": result.get("telegram_summary", ""),
        "report_text": result.get("report_text", ""),
        "report_filename": result.get("report_filename", "")
    }

    reports.insert(0, db_item)
    save_reports_db(reports[:100])
    return db_item


def build_signal_forge_summary_from_latest():
    results_db = load_backtest_results()
    if not results_db:
        return None

    all_rows = []
    for report_res in results_db:
        if isinstance(report_res, dict) and "results" in report_res:
            all_rows.extend(report_res.get("results", []))
        elif isinstance(report_res, list):
            all_rows.extend(report_res)

    if not all_rows:
        return None

    return summarize_signal_forge_results(all_rows)


def get_latest_report():
    reports = load_reports_db()
    return reports[0] if reports else None


def build_weekly_picks_fallback():
    latest = get_latest_report()
    if not latest:
        return {
            "status": "empty",
            "title": "Haftanın Tavsiyeleri",
            "week_label": "-",
            "summary": "Henüz haftalık öneri oluşturulmadı.",
            "picks": []
        }

    ai_reasoned = latest.get("ai_reasoned_stocks", [])
    scored = latest.get("scored_stocks", [])

    picks = []

    if ai_reasoned:
        for item in ai_reasoned[:5]:
            ticker = str(item.get("ticker", "")).upper()
            if not ticker:
                continue

            match_score = next(
                (s for s in scored if str(s.get("ticker", "")).upper() == ticker),
                {}
            )

            picks.append({
                "ticker": ticker,
                "theme": item.get("theme", "Makro fırsat"),
                "confidence": item.get("confidence", "Orta"),
                "reason": item.get("reason", ""),
                "expectation": item.get("expectation", ""),
                "move_range": item.get("move_range", ""),
                "score": match_score.get("score")
            })
    else:
        for item in scored[:5]:
            picks.append({
                "ticker": item.get("ticker", ""),
                "theme": "Makro fırsat",
                "confidence": "Orta",
                "reason": ", ".join(item.get("reasons", [])),
                "expectation": "Kısa vadede izlenebilir.",
                "move_range": "%2 - %5",
                "score": item.get("score")
            })

    return {
        "status": "ok",
        "title": "Haftanın Tavsiyeleri",
        "week_label": latest.get("date", "-"),
        "summary": "Bu bölüm şimdilik son üretilen rapordan besleniyor. Sonraki adımda haftalık otomatik üretime çevireceğiz.",
        "picks": picks
    }


def get_weekly_picks_payload():
    weekly = load_weekly_picks()

    if weekly and weekly.get("picks"):
        return {
            "status": "ok",
            "title": weekly.get("title", "Haftanın Tavsiyeleri"),
            "week_label": weekly.get("week_label", "-"),
            "summary": weekly.get("summary", ""),
            "picks": weekly.get("picks", [])
        }

    return build_weekly_picks_fallback()


def find_tracked_stock(ticker):
    ticker = str(ticker).upper().strip()
    tracked = load_tracked_stocks()

    for item in tracked:
        if item["symbol"] == ticker:
            return item

    universe = load_stock_universe()
    uni_item = universe.get(ticker)

    if uni_item:
        return {
            "symbol": ticker,
            "name": uni_item.get("description", ticker),
            "sector": "Unknown",
            "theme": "",
            "description": uni_item.get("description", "")
        }

    return None


def serialize_stock_list():
    tracked = load_tracked_stocks()
    universe = load_stock_universe()

    items = []
    for item in tracked:
        symbol = item["symbol"]
        uni = universe.get(symbol, {})
        items.append({
            "symbol": symbol,
            "name": item.get("name") or uni.get("description", symbol),
            "sector": item.get("sector", "Unknown"),
            "theme": item.get("theme", ""),
            "description": item.get("description") or uni.get("description", "")
        })

    return items


def get_latest_signal_for_ticker(ticker):
    latest = get_latest_report()
    if not latest:
        return None

    ticker = str(ticker).upper().strip()

    for item in latest.get("scored_stocks", []):
        if str(item.get("ticker", "")).upper() == ticker:
            return item

    return None


@app.route("/")
def home_page():
    return render_template("home.html")


@app.route("/stocks")
def stocks_page():
    return render_template("stocks.html")


@app.route("/stocks/<ticker>")
def stock_detail_page(ticker):
    stock = find_tracked_stock(ticker)
    if not stock:
        return render_template("stock_detail.html", ticker=str(ticker).upper(), not_found=True)

    return render_template("stock_detail.html", ticker=stock["symbol"], not_found=False)


@app.route("/api/run-analysis")
def api_run_analysis():
    result = run_daily_analysis(send_telegram=False)
    db_item = save_run_result(result)
    return jsonify({"status": "ok", "report": db_item})


@app.route("/api/run-analysis-and-send")
def api_run_analysis_and_send():
    result = run_daily_analysis(
        send_telegram=True,
        telegram_sender_func=send_long_telegram_message
    )
    db_item = save_run_result(result)
    return jsonify({"status": "ok", "report": db_item})


@app.route("/api/latest-report")
def api_latest_report():
    latest = get_latest_report()
    if not latest:
        return jsonify({"status": "empty"})
    return jsonify({"status": "ok", "report": latest})


@app.route("/api/reports")
def api_reports():
    reports = load_reports_db()
    brief = []

    for item in reports[:20]:
        brief.append({
            "id": item.get("id"),
            "date": item.get("date"),
            "top_tickers": [s.get("ticker") for s in item.get("scored_stocks", [])[:5]]
        })

    return jsonify({"status": "ok", "reports": brief})


@app.route("/api/report/<report_id>")
def api_report_detail(report_id):
    reports = load_reports_db()
    for item in reports:
        if str(item.get("id")) == str(report_id):
            return jsonify({"status": "ok", "report": item})
    return jsonify({"status": "error", "message": "Rapor bulunamadı."}), 404


@app.route("/api/run-signal-forge-latest")
def api_run_signal_forge_latest():
    result = run_signal_forge_latest(top_n=5)
    return jsonify(result)


@app.route("/api/signal-forge-results")
def api_signal_forge_results():
    results = load_backtest_results()
    return jsonify({"status": "ok", "count": len(results), "results": results})


@app.route("/api/signal-forge-summary")
def api_signal_forge_summary():
    summary = build_signal_forge_summary_from_latest()
    return jsonify({"status": "ok", "summary": summary or {}})


@app.route("/api/health")
def api_health():
    latest = get_latest_report()
    return jsonify({
        "status": "ok",
        "service": "AI Macro Stock Engine",
        "mode": "website",
        "last_run": latest.get("date") if latest else "-"
    })


@app.route("/api/weekly-picks/latest")
def api_weekly_picks_latest():
    return jsonify(get_weekly_picks_payload())


@app.route("/api/stocks")
def api_stocks():
    items = serialize_stock_list()
    return jsonify({
        "status": "ok",
        "count": len(items),
        "stocks": items
    })


@app.route("/api/stocks/<ticker>")
def api_stock_profile(ticker):
    stock = find_tracked_stock(ticker)
    if not stock:
        return jsonify({"status": "error", "message": "Hisse bulunamadı."}), 404

    latest_match = get_latest_signal_for_ticker(stock["symbol"])

    return jsonify({
        "status": "ok",
        "stock": stock,
        "latest_signal": latest_match
    })


@app.route("/api/stocks/<ticker>/market-data")
def api_stock_market_data(ticker):
    stock = find_tracked_stock(ticker)
    if not stock:
        return jsonify({"status": "error", "message": "Hisse bulunamadı."}), 404

    snapshot = get_stock_snapshot(stock["symbol"])
    if not snapshot:
        return jsonify({
            "status": "error",
            "message": "Piyasa verisi alınamadı."
        }), 404

    return jsonify({
        "status": "ok",
        "stock": stock,
        "market_data": snapshot
    })


@app.route("/api/stocks/<ticker>/chart")
def api_stock_chart(ticker):
    stock = find_tracked_stock(ticker)
    if not stock:
        return jsonify({"status": "error", "message": "Hisse bulunamadı."}), 404

    chart_range = request.args.get("range", "3mo")
    chart_data = get_stock_chart_data(stock["symbol"], chart_range=chart_range)

    if not chart_data:
        return jsonify({"status": "error", "message": "Grafik verisi alınamadı."}), 404

    return jsonify({
        "status": "ok",
        "stock": stock,
        "chart": chart_data
    })


@app.route("/api/stocks/<ticker>/ai-analysis")
def api_stock_ai_analysis(ticker):
    stock = find_tracked_stock(ticker)
    if not stock:
        return jsonify({"status": "error", "message": "Hisse bulunamadı."}), 404

    market_data = get_stock_snapshot(stock["symbol"])
    if not market_data:
        return jsonify({"status": "error", "message": "Piyasa verisi alınamadı."}), 404

    latest_signal = get_latest_signal_for_ticker(stock["symbol"])
    force_refresh = request.args.get("refresh", "0") == "1"

    result = generate_stock_ai_analysis(
        stock=stock,
        market_data=market_data,
        latest_signal=latest_signal,
        force_refresh=force_refresh
    )

    if result.get("status") != "ok":
        return jsonify(result), 500

    return jsonify(result)


@app.route("/api/dashboard-summary")
def api_dashboard_summary():
    latest = get_latest_report()

    return jsonify({
        "status": "ok",
        "health": {
            "service": "AI Macro Stock Engine",
            "status": "online",
            "last_run": latest.get("date") if latest else "-"
        },
        "weekly_picks": get_weekly_picks_payload(),
        "signal_forge": build_signal_forge_summary_from_latest() or {}
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)