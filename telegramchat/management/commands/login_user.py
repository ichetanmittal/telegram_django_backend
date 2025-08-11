from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# 🔐 Replace with your app credentials
API_ID = 20984384
API_HASH = "166edd64b602cad7c2cefd5d03f4d760"

def generate_session():
    print("📱 Telegram Login")

    # ✅ Let Telethon handle all prompts automatically
    with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        client.start()  # ← No phone passed
        session_string = client.session.save()

        print("\n✅ Login successful!")
        print(f"\n🔑 Your session string (save this in DB!):\n\n{session_string}\n")

if __name__ == "__main__":
    generate_session()
