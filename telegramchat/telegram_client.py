from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# 🔐 Your Telegram API credentials
api_id = 20984384
api_hash = '166edd64b602cad7c2cefd5d03f4d760'

# This function will be used to create a client using a user's session string
def get_telegram_client(session_string):
    return TelegramClient(StringSession(session_string), api_id, api_hash)
