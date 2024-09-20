import requests
from django.conf import settings
from requests.exceptions import RequestException


def send_telegram_message(message):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()  # Raises an exception for 4xx/5xx responses
    except RequestException as e:
        """Logging of exception for further analysis"""
        print(f"Failed to send Telegram message: {e}")
        return None

    return response.json()
