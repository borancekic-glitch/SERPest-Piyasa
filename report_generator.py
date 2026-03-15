from datetime import datetime


def generate_report(news, analysis, scored_stocks, ai_reasoned_stocks):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    reason_map = {}
    for item in ai_reasoned_stocks:
        ticker = item.get("ticker", "").upper()
        if ticker:
            reason_map[ticker] = item

    report_lines = []
    report_lines.append("GÜNLÜK MACRO STOCK RAPORU")
    report_lines.append(f"Tarih: {today}")
    report_lines.append("=" * 60)

    report_lines.append("\n1) GÜNÜN HABER BAŞLIKLARI")
    for item in news[:10]:
        report_lines.append(f"- {item}")

    report_lines.append("\n2) AI MAKRO ANALİZİ")
    report_lines.append(analysis)

    report_lines.append("\n3) SEÇİLEN HİSSELER İÇİN AI DESTEKLİ ÖZEL GEREKÇELER")

    if ai_reasoned_stocks:
        for i, stock in enumerate(ai_reasoned_stocks, start=1):
            report_lines.append(f"{i}. HİSSE: {stock['ticker']}")
            report_lines.append(f"   Tema: {stock['theme']}")
            report_lines.append(f"   Güven: {stock['confidence']}")
            report_lines.append(f"   Sebep: {stock['reason']}")
            report_lines.append(f"   Beklenti: {stock['expectation']}")
            report_lines.append(f"   Tahmini hareket: {stock['move_range']}")
            report_lines.append("-" * 50)
    else:
        report_lines.append("AI özel hisse gerekçesi üretilemedi.")

    report_lines.append("\n4) EN YÜKSEK SKORLU HİSSELER")

    if scored_stocks:
        top_ideas = scored_stocks[:5]

        for i, stock in enumerate(top_ideas, start=1):
            ticker = stock["ticker"]
            ai_detail = reason_map.get(ticker, {})

            report_lines.append(
                f"{i}. {ticker} | "
                f"Skor: {stock['score']} | "
                f"Fiyat: {stock['last_close']} | "
                f"Günlük %: {stock['price_change_pct']} | "
                f"Hacim oranı: {stock['volume_ratio']} | "
                f"Event destek: {stock.get('event_supported')}"
            )
            report_lines.append(f"   Skor nedenleri: {', '.join(stock['reasons'])}")

            if stock.get("extract_reasons"):
                report_lines.append(f"   Extractor nedenleri: {', '.join(stock['extract_reasons'])}")

            if ai_detail:
                report_lines.append(f"   AI tema: {ai_detail.get('theme', '')}")
                report_lines.append(f"   AI sebep: {ai_detail.get('reason', '')}")
                report_lines.append(f"   AI beklenti: {ai_detail.get('expectation', '')}")
                report_lines.append(f"   AI hareket: {ai_detail.get('move_range', '')}")

            report_lines.append("-" * 50)
    else:
        report_lines.append("Skorlanmış hisse bulunamadı.")

    return "\n".join(report_lines)


def save_report(report_text):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"daily_report_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    return filename