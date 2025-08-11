import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

class TelegramService:
    def __init__(self):
        self.api_id = 20984384
        self.api_hash = "166edd64b602cad7c2cefd5d03f4d760"
        self.client = None
        self.loop = None

    def _ensure_loop(self):
        if not self.loop or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def send_code(self, phone):
        self._ensure_loop()
        try:
            self.client = TelegramClient(
                StringSession(),
                self.api_id,
                self.api_hash,
                loop=self.loop
            )
            
            # Connect synchronously
            self.client.connect()
            
            if not self.loop.run_until_complete(self.client.is_user_authorized()):
                result = self.loop.run_until_complete(
                    self.client.send_code_request(phone)
                )
                return {
                    "status": "success",
                    "phone_code_hash": result.phone_code_hash
                }
            return {"status": "already_authorized"}
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            if self.client:
                self.client.disconnect()
            if self.loop:
                self.loop.close()