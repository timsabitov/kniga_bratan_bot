import logging
from telegram import Message

logger = logging.getLogger(__name__)

def get_message_type(message: Message) -> str:
    if message.text:
        return "text"
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.audio:
        return "audio"
    if message.document:
        return "document"
    if hasattr(message, 'sticker') and message.sticker:
        return "sticker"
    return "unknown"

def get_message_content(message: Message) -> str:
    if message.text:
        return message.text
    if message.photo:
        return message.photo[-1].file_id
    if message.video:
        return message.video.file_id
    if message.audio:
        return message.audio.file_id
    if message.document:
        return message.document.file_id
    if hasattr(message, 'sticker') and message.sticker:
        return message.sticker.file_id
    return ""

async def is_admin(bot, chat_id, user_id) -> bool:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        return user_id in [admin.user.id for admin in admins]
    except Exception as e:
        logger.error(f"Error in is_admin: {e}")
        return False
