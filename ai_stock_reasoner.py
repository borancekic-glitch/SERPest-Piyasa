import os
import json
import re
import anthropic

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "").strip()


def _extract_json_array(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI çıktısında JSON array bulunamadı.")

    return text[start:end + 1]


def build_fallback_reasons(scored_stocks, max_stocks=5):
    top_stocks = scored_stocks[:max_stocks]
    results = []

    for item in top_stocks:
        ticker = item.get("ticker", "")
        event_supported = item.get("event_supported", False)
        extract_score = item.get("extract_score", 0)
        price_change = item.get("price_change_pct", 0)
        volume_ratio = item.get("volume_ratio", 0)

        confidence = "Orta"
        if extract_score >= 8 or (event_supported and volume_ratio >= 1.0):
            confidence = "Yüksek"
        elif extract_score <= 2 and volume_ratio < 1.0:
            confidence = "Düşük"

        reason_parts = []

        if event_supported:
            reason_parts.append("makro olay zinciri tarafından destekleniyor")
        if extract_score >= 8:
            reason_parts.append("AI analizinde güçlü öne çıktı")
        elif extract_score >= 4:
            reason_parts.append("AI analizinde destek buldu")

        if price_change >= 2:
            reason_parts.append("fiyat momentumu güçlü")
        elif price_change > 0:
            reason_parts.append("fiyat pozitif")

        if volume_ratio >= 1.5:
            reason_parts.append("hacim güçlü")
        elif volume_ratio >= 1.0:
            reason_parts.append("hacim destekli")

        if not reason_parts:
            reason_parts.append("günün makro temasına uyumlu bulundu")

        reason = ", ".join(reason_parts)
        expectation = "Makro tema korunursa hissede kısa vadeli pozitif fiyatlama görülebilir."

        move_range = "%2 - %5"
        if confidence == "Yüksek":
            move_range = "%3 - %7"
        elif confidence == "Düşük":
            move_range = "%1 - %3"

        results.append({
            "ticker": ticker,
            "theme": "Makro fırsat",
            "confidence": confidence,
            "reason": reason,
            "expectation": expectation,
            "move_range": move_range,
        })

    return results


def generate_ai_stock_reasons(news, analysis, scored_stocks, event_candidates=None, max_stocks=5):
    top_stocks = scored_stocks[:max_stocks]

    if not top_stocks:
        return []

    stock_payload = []
    for item in top_stocks:
        stock_payload.append({
            "ticker": item.get("ticker"),
            "score": item.get("score"),
            "extract_score": item.get("extract_score"),
            "event_supported": item.get("event_supported"),
            "price_change_pct": item.get("price_change_pct"),
            "volume_ratio": item.get("volume_ratio"),
            "reasons": item.get("reasons", []),
            "extract_reasons": item.get("extract_reasons", []),
        })

    event_info = event_candidates if event_candidates else {"events": [], "sectors": [], "tickers": []}

    prompt = f"""
Bugünkü haberleri, makro analizi ve seçilmiş hisseleri kullanarak her hisse için BİRBİRİNDEN FARKLI, hisseye özel, olaya bağlı kısa açıklamalar üret.

Kurallar:
- Türkçe yaz.
- Her hisse için özel sebep yaz. Kopyala-yapıştır gibi aynı sebebi tekrar etme.
- Sebep kısmı "jeopolitik risk var" gibi çok genel olmasın.
- Her hissede olay -> şirket/tema -> neden fayda görebilir zincirini kur.
- Eğer hisse enerjiyse petrol arzı / navlun / LNG / rafineri / upstream gibi özel mekanizmayı belirt.
- Eğer savunmaysa füze, hava savunma, askeri sipariş, donanma, savaş uzaması gibi özel mekanizmayı belirt.
- Eğer shipping ise rota uzaması, sigorta maliyeti, ton-mil artışı, tanker/navlun gibi özel mekanizmayı belirt.
- Eğer siber güvenlik ise saldırı riski, kritik altyapı, kamu/şirket bütçesi gibi özel mekanizmayı belirt.
- Eğer nükleer/elektrik ise enerji güvenliği, baz yük, şebeke yatırımı gibi özel mekanizmayı belirt.
- Tahmini hareket kısa vadeli yaklaşık aralık olsun.
- Güven sadece: Düşük, Orta, Yüksek
- Her hisse için şu alanları döndür:
  - ticker
  - theme
  - confidence
  - reason
  - expectation
  - move_range
- Sadece GEÇERLİ JSON ARRAY döndür.
- Açıklama, yorum, markdown, kod bloğu ekleme.

Bugünkü haberler:
{news}

Event tespiti:
{json.dumps(event_info, ensure_ascii=False)}

Makro analiz:
{analysis}

Seçilmiş hisseler:
{json.dumps(stock_payload, ensure_ascii=False)}
"""

    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1400,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw_text = response.content[0].text
        print("AI RAW RESPONSE:")
        print(raw_text)

        json_text = _extract_json_array(raw_text)
        parsed = json.loads(json_text)

        cleaned = []
        for item in parsed:
            cleaned.append({
                "ticker": str(item.get("ticker", "")).upper().strip(),
                "theme": str(item.get("theme", "")).strip(),
                "confidence": str(item.get("confidence", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
                "expectation": str(item.get("expectation", "")).strip(),
                "move_range": str(item.get("move_range", "")).strip(),
            })

        if not cleaned:
            print("AI reason çıktısı boş geldi, fallback kullanılacak.")
            return build_fallback_reasons(scored_stocks, max_stocks=max_stocks)

        return cleaned

    except Exception as e:
        print("AI hisse gerekçesi üretiminde hata oluştu:")
        print(str(e))
        return build_fallback_reasons(scored_stocks, max_stocks=max_stocks)
