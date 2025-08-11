import os
import sys
import django
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from django.utils import timezone
from asgiref.sync import sync_to_async

# 🔧 Adjust project paths and settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "telegramweb.settings")  # Change if needed

# 🔧 Setup Django
django.setup()

# ✅ Import after setup
from telegramchat.models import TelegramUser, ChatMessage
from django.conf import settings

# 🔄 Fetch all users safely in async context
@sync_to_async
def get_all_users():
    return list(TelegramUser.objects.all())

# 🧠 Save message safely in async context
@sync_to_async
def save_message(user, sender, message):
    ChatMessage.objects.create(
        user=user,
        sender=sender,
        message=message,
        timestamp=timezone.now()
    )

async def run_clients():
    users = await get_all_users()

    if not users:
        print("❗ No Telegram users found in the database.")
        return

    clients = []

    for user in users:
        client = TelegramClient(StringSession(user.session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)

        @client.on(events.NewMessage(incoming=True))
        async def handler(event, user=user):
            sender = await event.get_sender()
            sender_name = sender.username or sender.first_name or str(sender.id)
            message_text = event.message.message

            await save_message(user, sender_name, message_text)

            print(f"[{user.phone}] Message from {sender_name}: {message_text}")

        await client.start()
        print(f"[{user.phone}] ✅ Client started and listening...")
        clients.append(client)

    # Keep all clients running
    await asyncio.gather(*[client.run_until_disconnected() for client in clients])

if __name__ == "__main__":
    try:
        asyncio.run(run_clients())
    except KeyboardInterrupt:
        print("🔴 Receiver stopped manually.")
