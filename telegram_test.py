import requests

import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()
    print(data)


if __name__ == "__main__":
    get_updates()