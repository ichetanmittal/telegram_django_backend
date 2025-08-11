import json
import logging
from django.conf import settings
from .models import TelegramUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    FloodWaitError
)

logger = logging.getLogger(__name__)

# Temporary in-memory storage
session_store = {}
phone_code_hash_store = {}

# Authenticate a client using session_string
def get_authenticated_client(session_string):
    client = TelegramClient(StringSession(session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    async_to_sync(client.connect)()
    return client

# ------------------- SEND CODE -------------------

@csrf_exempt
def send_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            phone = data.get('phone')
            if not phone:
                return JsonResponse({'status': 'error', 'message': 'Phone number is required'}, status=400)

            response = async_to_sync(send_telegram_code)(phone, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
            return JsonResponse(response)

        except Exception as e:
            logger.exception("[SEND CODE] Server error")
            return JsonResponse({'status': 'error', 'message': 'Server error while sending code'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

async def send_telegram_code(phone, api_id, api_hash):
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    try:
        result = await client.send_code_request(phone)
        session_store[phone] = client.session.save()
        phone_code_hash_store[phone] = result.phone_code_hash

        logger.info(f"[SEND CODE] phone_code_hash: {result.phone_code_hash}")
        return {
            'status': 'success',
            'phone_code_hash': result.phone_code_hash,
            'timeout': result.timeout,
            'message': 'Verification code sent successfully'
        }

    except FloodWaitError as e:
        return {
            'status': 'error',
            'message': f'Too many attempts. Wait {e.seconds} seconds.',
            'retry_after': e.seconds
        }

    except Exception as e:
        logger.exception("[SEND CODE] Unexpected error")
        return {'status': 'error', 'message': 'Failed to send verification code'}

    finally:
        await client.disconnect()

# ------------------- VERIFY CODE -------------------

@csrf_exempt
def verify_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            phone = data.get('phone')
            code = str(data.get('code')) if data.get('code') else None
            phone_code_hash = data.get('phone_code_hash')

            if not all([phone, code, phone_code_hash]):
                return JsonResponse({'status': 'error', 'message': 'Missing phone, code or phone_code_hash'}, status=400)

            response = async_to_sync(verify_telegram_code)(phone, code, phone_code_hash, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
            return JsonResponse(response)

        except Exception as e:
            logger.exception("[VERIFY CODE] Server error")
            return JsonResponse({'status': 'error', 'message': 'Server error while verifying code'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

from asgiref.sync import sync_to_async
async def verify_telegram_code(phone, code, phone_code_hash, api_id, api_hash):
    session_str = session_store.get(phone)
    stored_hash = phone_code_hash_store.get(phone)

    if not session_str or not stored_hash:
        return {'status': 'error', 'message': 'Session or phone_code_hash not found. Please resend code.'}

    if stored_hash != phone_code_hash:
        return {'status': 'error', 'message': 'Invalid or outdated phone_code_hash.'}

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)

        # Save the session string after successful login
        session_string = client.session.save()

        # ✅ Save to database using sync_to_async
        await sync_to_async(TelegramUser.objects.update_or_create)(
            phone=phone,
            defaults={'session_string': session_string}
        )

        return {
            'status': 'success',
            'session_string': session_string,
            'message': 'Login successful!'
        }

    except PhoneCodeInvalidError:
        return {'status': 'error', 'message': 'Invalid verification code'}
    except PhoneCodeExpiredError:
        return {'status': 'error', 'message': 'Code expired. Request a new one.'}
    except SessionPasswordNeededError:
        return {'status': '2fa_required', 'message': '2FA password required'}
    except Exception as e:
        logger.exception("[SIGN-IN] Unexpected error")
        return {'status': 'error', 'message': 'Failed to verify code'}
    finally:
        await client.disconnect()
# ------------------- GET CHATS -------------------

@csrf_exempt
def get_chats(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            session_string = data.get('session_string')

            if not session_string:
                return JsonResponse({'status': 'error', 'message': 'Session string is required'}, status=400)

            response = async_to_sync(fetch_chats)(session_string)
            return JsonResponse(response)

        except Exception as e:
            logger.exception("[GET CHATS] Error")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

async def fetch_chats(session_string):
    client = TelegramClient(StringSession(session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()

    try:
        dialogs = await client.get_dialogs()
        chat_list = []

        for dialog in dialogs:
            chat = dialog.entity
            chat_list.append({
                'id': chat.id,
                'title': getattr(chat, 'title', None),
                'username': getattr(chat, 'username', None),
                'phone': getattr(chat, 'phone', None),
                'type': type(chat).__name__
            })

        return {'status': 'success', 'chats': chat_list}

    except Exception as e:
        logger.exception("[FETCH CHATS] Error")
        return {'status': 'error', 'message': str(e)}

    finally:
        await client.disconnect()

# ------------------- SEND MESSAGE -------------------

@csrf_exempt
def send_message(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            session_string = data.get('session_string')
            target = data.get('target')  # username, ID, or phone
            message = data.get('message')

            if not all([session_string, target, message]):
                return JsonResponse({'status': 'error', 'message': 'Missing fields'}, status=400)

            response = async_to_sync(send_message_async)(session_string, target, message)
            return JsonResponse(response)

        except Exception as e:
            logger.exception("[SEND MESSAGE] Error")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

async def send_message_async(session_string, target, message):
    client = TelegramClient(StringSession(session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()

    try:
        await client.send_message(target, message)
        return {'status': 'success', 'message': 'Message sent'}

    except Exception as e:
        logger.exception("[SEND MESSAGE ASYNC] Failed")
        return {'status': 'error', 'message': str(e)}

    finally:
        await client.disconnect()
@csrf_exempt
def get_chat_history(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            session_string = data.get('session_string')
            target = data.get('target')  # username, user ID, or phone
            limit = data.get('limit', 50)  # default 50 messages

            if not all([session_string, target]):
                return JsonResponse({'status': 'error', 'message': 'Missing session_string or target'}, status=400)

            response = async_to_sync(fetch_chat_history)(session_string, target, int(limit))
            return JsonResponse(response)

        except Exception as e:
            logger.exception("[GET CHAT HISTORY] Error")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

async def fetch_chat_history(session_string, target, limit):
    client = TelegramClient(StringSession(session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()

    try:
        messages = []
        async for msg in client.iter_messages(target, limit=limit):
            messages.append({
                'id': msg.id,
                'text': msg.text,
                'sender_id': msg.sender_id,
                'date': str(msg.date),
                'reply_to': msg.reply_to_msg_id,
            })

        return {'status': 'success', 'messages': messages}

    except Exception as e:
        logger.exception("[FETCH CHAT HISTORY] Failed")
        return {'status': 'error', 'message': str(e)}

    finally:
        await client.disconnect()
@csrf_exempt
def get_user_info(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            session_string = data.get('session_string')

            if not session_string:
                return JsonResponse({'status': 'error', 'message': 'Session string is required'}, status=400)

            response = async_to_sync(fetch_user_info)(session_string)
            return JsonResponse(response)

        except Exception as e:
            logger.exception("[GET USER INFO] Error")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

async def fetch_user_info(session_string):
    client = TelegramClient(StringSession(session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.connect()

    try:
        me = await client.get_me()
        user_info = {
            'id': me.id,
            'first_name': me.first_name,
            'last_name': me.last_name,
            'username': me.username,
            'phone': me.phone
        }
        return {'status': 'success', 'user': user_info}
    except Exception as e:
        logger.exception("[FETCH USER INFO] Failed")
        return {'status': 'error', 'message': str(e)}
    finally:
        await client.disconnect()
