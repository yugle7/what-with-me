import os

import requests
import re

import dotenv

dotenv.load_dotenv()

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
API_GATEWAY_DOMAIN = os.getenv("API_GATEWAY_DOMAIN")
URL = "https://api.telegram.org"
APP = "https://yugle7.github.io/whatwithme/"


def set_webhook():
    url = f"{URL}/bot{TG_BOT_TOKEN}/setWebhook"
    res = requests.post(url, json={"url": f"{API_GATEWAY_DOMAIN}/fshtb-function"})
    print(res.json())


def delete_webhook():
    url = f"{URL}/bot{TG_BOT_TOKEN}/deleteWebhook"
    requests.post(url)


def escape(text):
    return re.sub(r"([:_~*\[\]()>#+-={}|.!])", r"\\\1", text)


def send_message(chat_id, text):
    url = f"{URL}/bot{TG_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": escape(text), "parse_mode": "MarkdownV2"}

    res = requests.post(url, json=data)
    if not res.ok:
        return None

    res = res.json().get("result")
    return res and res.get("message_id")


def edit_message(chat_id, message_id, text):
    url = f"{URL}/bot{TG_BOT_TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "text": escape(text),
        "message_id": message_id,
        "parse_mode": "MarkdownV2",
    }
    return requests.post(url, data=data).ok


def delete_message(chat_id, message_id):
    url = f"{URL}/bot{TG_BOT_TOKEN}/deleteMessage"
    data = {"chat_id": chat_id, "message_id": message_id}
    return requests.post(url, data=data).ok


def get_user_id(body):
    for k in ["callback_query", "message", "edited_message"]:
        if k in body:
            return body[k]["from"]["id"]
    return None


if __name__ == "__main__":
    set_webhook()
