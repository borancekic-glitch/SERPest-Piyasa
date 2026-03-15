import os
import anthropic

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "").strip()


def translate_to_turkish(text):

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    prompt = f"""
Aşağıdaki finansal raporu Türkçeye çevir.

Kurallar:
- Akıcı ve düzgün Türkçe kullan
- Finans terimlerini doğru çevir
- Hisse sembollerini değiştirme
- Formatı koru

Metin:

{text}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text