import requests
import time 
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram_message(message_text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message_text
    }

    response = requests.post(url, data=payload)
    return response.json()


def split_by_stock_blocks(text, max_length=3500):
    text = text.strip()

    if len(text) <= max_length:
        return [text]

    lines = text.splitlines()

    header_lines = []
    stock_blocks = []
    current_block = []

    started_blocks = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("HİSSE:") or stripped.startswith("HISSE:"):
            started_blocks = True

            if current_block:
                stock_blocks.append("\n".join(current_block).strip())
                current_block = []

            current_block.append(line)
        else:
            if not started_blocks:
                header_lines.append(line)
            else:
                current_block.append(line)

    if current_block:
        stock_blocks.append("\n".join(current_block).strip())

    header_text = "\n".join(header_lines).strip()

    parts = []
    current_part = header_text if header_text else ""

    for block in stock_blocks:
        block_to_add = ("\n\n" + block) if current_part else block

        if len(current_part) + len(block_to_add) <= max_length:
            current_part += block_to_add
        else:
            if current_part.strip():
                parts.append(current_part.strip())
            current_part = block

    if current_part.strip():
        parts.append(current_part.strip())

    return parts


def send_long_telegram_message(message_text):
    parts = split_by_stock_blocks(message_text, max_length=3500)
    results = []

    for i, part in enumerate(parts, start=1):
        if len(parts) > 1:
            final_text = f"Parça {i}/{len(parts)}\n\n{part}"
        else:
            final_text = part

        result = send_telegram_message(final_text)
        results.append(result)
        time.sleep(1)

    return results


if __name__ == "__main__":
    test_message = """📊 GÜNLÜK HİSSE ÖZETİ

HİSSE: LMT
Sebep: Savunma harcamaları artıyor.
Beklenti: Kısa vadede güçlü kalabilir.

HİSSE: FRO
Sebep: Tanker navlunları destekleniyor.
Beklenti: Jeopolitik riskle ivme sürebilir.

HİSSE: CEG
Sebep: Veri merkezi güç talebi artıyor.
Beklenti: Elektrik üreticileri destek bulabilir.
"""

    result = send_long_telegram_message(test_message)
    print(result)