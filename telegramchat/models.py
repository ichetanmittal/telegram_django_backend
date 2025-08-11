from django.db import models

class TelegramUser(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    session_string = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone


class ChatMessage(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender} at {self.timestamp}"
