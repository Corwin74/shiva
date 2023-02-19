import requests
from environs import Env

env = Env()
env.read_env()
tlgm_bot_token = env('TLGM_BOT_TOKEN')


def send_notification(chat_id, text):
    payload = {'chat_id': chat_id, 'text': text}
    response = requests.get(f'https://api.telegram.org/bot{tlgm_bot_token}/sendMessage', params=payload)
    response.raise_for_status()
