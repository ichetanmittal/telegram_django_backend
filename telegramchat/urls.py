from django.urls import path
from . import views  # ✅ safer than 'from telegramchat import views'

urlpatterns = [
    path('send_code/', views.send_code),
    path('verify_code/', views.verify_code),
    path('get_chats/', views.get_chats),
    path('send_message/', views.send_message),
    path('get_chat_history/', views.get_chat_history),
    path('get_user_info/', views.get_user_info),
]
