def create_telegram_summary(ai_reasoned_stocks):
    if not ai_reasoned_stocks:
        return "📊 GÜNLÜK HİSSE ÖZETİ\n\nBugün öne çıkan hisse bulunamadı."

    emoji_map = {
        "enerji": "⚡",
        "petrol": "🛢️",
        "doğal gaz": "🔥",
        "shipping": "🚢",
        "tanker": "🚢",
        "savunma": "🛡️",
        "siber": "🔐",
        "nükleer": "☢️",
        "uranyum": "☢️",
        "elektrik": "🔌",
        "şebeke": "🔌",
        "çip": "🧠",
        "yarı iletken": "🧠",
        "altın": "🥇",
        "gümüş": "🥇",
        "sigorta": "🏦",
        "lojistik": "🚚",
    }

    def pick_emoji(theme):
        lower_theme = theme.lower()
        for key, emoji in emoji_map.items():
            if key in lower_theme:
                return emoji
        return "📌"

    blocks = ["📊 GÜNLÜK HİSSE ÖZETİ"]

    for item in ai_reasoned_stocks:
        ticker = item.get("ticker", "")
        theme = item.get("theme", "Makro fırsat")
        confidence = item.get("confidence", "Orta")
        reason = item.get("reason", "Bugünkü makro temaya göre destekleyici bir hikâye var.")
        expectation = item.get("expectation", "Kısa vadede pozitif fiyatlama görülebilir.")
        move_range = item.get("move_range", "%2 - %5")
        emoji = pick_emoji(theme)

        block = (
            f"📌 HİSSE: {ticker}\n"
            f"{emoji} Tema: {theme}\n"
            f"🎯 Güven: {confidence}\n"
            f"🧠 Sebep: {reason}\n"
            f"📈 Beklenti: {expectation}\n"
            f"📊 Tahmini hareket: {move_range}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)