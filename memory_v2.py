import json
import os


def append_memory(filename, item):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(item)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_recent_memory(filename, limit=5):
    if not os.path.exists(filename):
        return []

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data[-limit:]


def build_memory_context(memory_items):
    if not memory_items:
        return "No recent memory available."

    lines = []

    for i, item in enumerate(memory_items, start=1):
        lines.append(f"MEMORY ITEM {i}")

        date_value = item.get("date", "unknown date")
        lines.append(f"Date: {date_value}")

        news = item.get("news", [])
        if news:
            lines.append("Past news headlines:")
            for headline in news[:5]:
                lines.append(f"- {headline}")

        top_stocks = item.get("top_stocks", [])
        if top_stocks:
            lines.append("Past top stocks:")
            for stock in top_stocks[:3]:
                ticker = stock.get("ticker", "unknown")
                score = stock.get("score", "unknown")
                lines.append(f"- {ticker} (score: {score})")

        analysis_summary = item.get("analysis_summary", "")
        if analysis_summary:
            lines.append("Past short analysis summary:")
            lines.append(analysis_summary)

        lines.append("-" * 40)

    return "\n".join(lines)