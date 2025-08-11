from django.contrib import admin
from .models import TelegramUser, ChatMessage
admin.site.register(TelegramUser)
admin.site.register(ChatMessage)