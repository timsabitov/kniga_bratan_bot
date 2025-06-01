import json
import random
import os
import logging

logger = logging.getLogger(__name__)

def get_message_type(message):
    """
    Определяет тип сообщения (например, текст, фото, видео и т.д.)
    """
    if message.video_note:
        return "video_note"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.audio:
        return "audio"
    elif message.document:
        return "document"
    elif message.sticker:
        return "sticker"
    else:
        return "text"

def get_message_content(message):
    if message.text:
        return message.text
    elif message.caption:
        return message.caption
    elif message.photo:
        return message.photo[-1].file_id
    elif message.video:
        return message.video.file_id
    elif message.video_note:
        return message.video_note.file_id
    elif message.audio:
        return message.audio.file_id
    elif message.document:
        return message.document.file_id
    elif message.sticker:
        return message.sticker.file_id
    return ""

async def is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка проверки админки: {e}")
        return False

def load_quotes(filepath="quotes.json"):
    try:
        # Определяем базовый путь (относительно файла utils.py)
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, "..", filepath)
        with open(full_path, encoding="utf-8") as f:
            quotes = json.load(f)
        return quotes
    except Exception as e:
        logger.error(f"Ошибка загрузки цитат: {e}")
        return []

def get_random_quote():
    quotes = load_quotes()
    if quotes:
        return random.choice(quotes)
    return "Нет доступных цитат."
