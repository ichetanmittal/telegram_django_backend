# Telegram Chat API

A Django REST API for Telegram chat functionality with authentication, message management, and chat history.

## Features

- 📱 Telegram phone verification and authentication
- 💬 Send and receive messages
- 📋 Get chat lists and chat history
- 👤 User information management
- 🔄 Real-time message monitoring (receiver.py)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your Telegram API credentials
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start development server:
```bash
python manage.py runserver
```

## API Endpoints

- `POST /api/send_code/` - Send verification code
- `POST /api/verify_code/` - Verify phone number
- `POST /api/get_user_info/` - Get user information
- `POST /api/get_chats/` - Get user's chat list
- `POST /api/send_message/` - Send message
- `POST /api/get_chat_history/` - Get chat history

## Deployment on Render

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - Other variables will be auto-generated

3. Deploy using the included `render.yaml` configuration

## Environment Variables

See `.env.example` for all required environment variables.

## Background Message Receiver

Run `python receiver.py` to start monitoring incoming messages in real-time.