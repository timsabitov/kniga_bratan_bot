import logging
import random
import re
import json
import asyncio
from datetime import datetime, date, time as dtime
from telegram import Update
from telegram.ext import CallbackContext
from app.utils import get_message_type, get_message_content, is_admin
from app.responses import RANDOM_RESPONSES

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, db):
        self.db = db
        self.beauty_winners = {}
        self.BD_TOASTS = [
            "С днём рождения, @{username}! Пусть удача всегда улыбается тебе! 🎉",
            "Поздравляем, @{username}! Желаем радости, успеха и крепкого здоровья! 🥳",
            "С праздником, @{username}! Пусть каждый день приносит тебе только счастье! 🎂",
            "День рождения – отличный повод сказать: @{username}, ты лучший! Пусть всё сбудется! 🎈",
            "Поздравляем, @{username}! Пусть жизнь дарит тебе только яркие моменты! 🎊"
        ]

    async def reset_beauty_winner(self, context: CallbackContext):
        chat_id = context.job.chat_id
        if chat_id in self.beauty_winners:
            del self.beauty_winners[chat_id]
        logger.info(f"Красавчик дня для чата {chat_id} сброшен.")

    async def check_birthdays(self, context: CallbackContext):
        today = date.today()
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT chat_id, user_id, username FROM birthdays WHERE EXTRACT(MONTH FROM birthday) = %s AND EXTRACT(DAY FROM birthday) = %s",
                    (today.month, today.day)
                )
                rows = cur.fetchall()
        if rows:
            for row in rows:
                chat_id, user_id, username = row
                toast = random.choice(self.BD_TOASTS).replace("@{username}", f"@{username}")
                try:
                    await context.bot.send_message(chat_id=chat_id, text=toast)
                    logger.info(f"Поздравление с ДР отправлено в чат {chat_id} для @{username}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке поздравления в чат {chat_id}: {e}")

    async def handle_kniga_bratan(self, update: Update, context: CallbackContext):
        text = update.message.text.strip().lower() if update.message and update.message.text else ""
        if text == "книга братан":
            username = update.message.from_user.username or update.message.from_user.first_name
            response = random.choice(RANDOM_RESPONSES)
            if "@{username}" in response:
                response = response.replace("@{username}", f"@{username}")
            else:
                response += f" 😎 @{username}"
            await update.message.reply_text(response)

    async def add_trigger(self, update: Update, context: CallbackContext):
        if not update.message:
            return
        if not await is_admin(context.bot, update.message.chat_id, update.message.from_user.id):
            await update.message.reply_text("❌ Только для админа! 🚫")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Ответьте на сообщение для добавления триггера! 🔔")
            return
        key = update.message.text[len("!add"):].strip()
        if not key:
            await update.message.reply_text("❌ Укажите ключ триггера после !add!")
            return
        if len(key) > 128:
            await update.message.reply_text("❌ Слишком длинное имя триггера! ⚠️")
            return
        if key.lower() in {"!add", "!del", "!list", "!bd", "!help", "!talker", "болтун"}:
            await update.message.reply_text("❌ Нельзя использовать зарезервированное имя! 🚫")
            return
        username = update.message.from_user.username or update.message.from_user.first_name
        chat_id = update.message.chat_id
        replied_message = update.message.reply_to_message
        content_type = get_message_type(replied_message)
        content = get_message_content(replied_message)
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, response, added_by FROM triggers WHERE chat_id = %s AND keyword = %s",
                            (chat_id, key.lower()))
                row = cur.fetchone()
                if row:
                    trigger_id, existing_response, existing_added_by = row
                    try:
                        responses = json.loads(existing_response)
                        if not isinstance(responses, list):
                            responses = [existing_response]
                    except Exception:
                        responses = [existing_response]
                    try:
                        added_by_list = json.loads(existing_added_by)
                        if not isinstance(added_by_list, list):
                            added_by_list = [existing_added_by]
                    except Exception:
                        added_by_list = [existing_added_by]
                    responses.append(content)
                    if username not in added_by_list:
                        added_by_list.append(username)
                    cur.execute("UPDATE triggers SET response = %s, added_by = %s WHERE id = %s",
                                (json.dumps(responses), json.dumps(added_by_list), trigger_id))
                    conn.commit()
                    await update.message.reply_text(f"✅ Новый ответ для триггера '{key}' добавлен! 👍")
                else:
                    cur.execute(
                        "INSERT INTO triggers (chat_id, keyword, type, response, added_by) VALUES (%s, %s, %s, %s, %s)",
                        (chat_id, key.lower(), content_type, json.dumps([content]), json.dumps([username])))
                    conn.commit()
                    await update.message.reply_text(f"✅ Триггер '{key}' добавлен! 🎉")

    async def delete_trigger(self, update: Update, context: CallbackContext):
        if not update.message:
            return
        if not await is_admin(context.bot, update.message.chat_id, update.message.from_user.id):
            await update.message.reply_text("❌ Только для админа! 🚫")
            return
        key = update.message.text[len("!del"):].strip()
        if not key:
            await update.message.reply_text("❌ Укажите ключ триггера для удаления!")
            return
        chat_id = update.message.chat_id
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM triggers WHERE chat_id = %s AND keyword = %s",
                            (chat_id, key.lower()))
            conn.commit()
        await update.message.reply_text(f"✅ Триггер '{key}' удалён! ✂️")

    async def list_triggers(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT keyword, added_by FROM triggers WHERE chat_id = %s", (chat_id,))
                rows = cur.fetchall()
        if rows:
            lines = ["📋 Список триггеров:"]
            for idx, (keyword, added_by) in enumerate(rows, start=1):
                try:
                    users = json.loads(added_by)
                    user_str = ", ".join(users) if isinstance(users, list) else str(users)
                except Exception:
                    user_str = added_by
                lines.append(f"{idx}. {keyword} (от: {user_str})")
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("В этом чате нет триггеров. 😔")

    async def handle_trigger_invocation(self, update: Update, context: CallbackContext):
        if not update.message or not update.message.text:
            return
        if update.message.text.startswith("!"):
            return
        trigger_key = update.message.text.strip().lower()
        chat_id = update.message.chat_id
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT response, type FROM triggers WHERE chat_id = %s AND keyword = %s",
                            (chat_id, trigger_key))
                row = cur.fetchone()
        if row:
            response_json, resp_type = row
            try:
                responses = json.loads(response_json)
                if not isinstance(responses, list):
                    responses = [response_json]
            except Exception:
                responses = [response_json]
            for resp in responses:
                try:
                    if resp_type == "photo":
                        await update.message.reply_photo(photo=resp)
                    elif resp_type == "video":
                        await update.message.reply_video(video=resp)
                    elif resp_type == "audio":
                        await update.message.reply_audio(audio=resp)
                    elif resp_type == "document":
                        await update.message.reply_document(document=resp)
                    elif resp_type == "sticker":
                        await update.message.reply_sticker(sticker=resp)
                        await asyncio.sleep(0.5)
                    else:
                        await update.message.reply_text(resp)
                except Exception as send_err:
                    logger.error(f"❌ Ошибка при отправке ответа: {send_err}")

    async def handle_beauty_trigger(self, update: Update, context: CallbackContext):
        text = update.message.text.strip().lower() if update.message and update.message.text else ""
        variants = {"кто красавчик сегодня", "красавчик сегодня", "красавчик"}
        if text in variants:
            chat_id = update.message.chat_id
            today_str = date.today().isoformat()
            if chat_id in self.beauty_winners and self.beauty_winners[chat_id].get("date") == today_str:
                winner = self.beauty_winners[chat_id]
            else:
                admins = await context.bot.get_chat_administrators(chat_id)
                if not admins:
                    await update.message.reply_text("Не удалось определить администраторов. 🚫")
                    return
                winner_admin = random.choice(admins).user
                winner = {
                    "winner_id": winner_admin.id,
                    "username": winner_admin.username or winner_admin.first_name,
                    "date": today_str
                }
                self.beauty_winners[chat_id] = winner
            await update.message.reply_text(f"Сегодня красавчик: @{winner['username']}! 🌟")

    async def handle_birthday_set(self, update: Update, context: CallbackContext):
        parts = update.message.text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Формат команды: !bd ДД.ММ.ГГГГ")
            return
        bd_str = parts[1]
        try:
            bd_date = datetime.strptime(bd_str, "%d.%m.%Y").date()
        except ValueError:
            await update.message.reply_text("❌ Неправильный формат даты. Используйте ДД.ММ.ГГГГ, например: !bd 05.04.1998")
            return
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        username = update.message.from_user.username or update.message.from_user.first_name
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM birthdays WHERE chat_id = %s AND user_id = %s",
                            (chat_id, user_id))
                row = cur.fetchone()
                if row:
                    cur.execute("UPDATE birthdays SET birthday = %s, username = %s WHERE id = %s",
                                (bd_date, username, row[0]))
                    conn.commit()
                    await update.message.reply_text(f"✅ Дата рождения обновлена для @{username}! 🎂")
                else:
                    cur.execute("INSERT INTO birthdays (chat_id, user_id, username, birthday) VALUES (%s, %s, %s, %s)",
                                (chat_id, user_id, username, bd_date))
                    conn.commit()
                    await update.message.reply_text(f"✅ Дата рождения установлена для @{username}! 🎉")

    async def help_command(self, update: Update, context: CallbackContext):
        help_text = (
            "🆘 Список команд:\n"
            "1. **Книга братан** – Напиши 'Книга братан' и получи мудрую цитату.\n"
            "2. **!add <ключ>** – Добавить триггер (только админы).\n"
            "3. **!del <ключ>** – Удалить триггер (только админы).\n"
            "4. **!list** – Посмотреть список триггеров.\n"
            "5. **Кто красавчик сегодня** – Узнать, кто сегодня красавчик (обновляется раз в сутки).\n"
            "6. **!bd <ДД.ММ.ГГГГ>** – Установить дату рождения. В день рождения бот поздравит тебя!\n"
            "7. **!talker** или **Болтун** – Узнать, кто болтун сегодня (статистика активности).\n"
            "8. **!help** – Показать это сообщение.\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_talker_command(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        today = date.today()
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, SUM(word_count) FROM activity WHERE chat_id = %s AND date = %s GROUP BY user_id ORDER BY SUM(word_count) DESC LIMIT 1",
                    (chat_id, today)
                )
                today_row = cur.fetchone()
                if not today_row:
                    await update.message.reply_text("Сегодня никто не болтал. 🤐")
                    return
                talker_user_id, today_count = today_row
                cur.execute(
                    "SELECT SUM(word_count) FROM activity WHERE chat_id = %s AND user_id = %s",
                    (chat_id, talker_user_id)
                )
                total_row = cur.fetchone()
                total_count = total_row[0] if total_row and total_row[0] is not None else 0
        member = await context.bot.get_chat_member(chat_id, talker_user_id)
        username = member.user.username or member.user.first_name
        response_text = (
            f"📢 Болтун сегодня: @{username}\n"
            f"Слов за сегодня: {today_count}\n"
            f"Общий счет слов: {total_count}"
        )
        await update.message.reply_text(response_text)

    async def update_activity(self, update: Update, context: CallbackContext):
        if not update.message or not update.message.text:
            return
        if update.message.text.startswith("!"):
            return
        text = update.message.text
        word_count = len(text.split())
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        today = date.today()
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, word_count FROM activity WHERE chat_id = %s AND user_id = %s AND date = %s",
                    (chat_id, user_id, today)
                )
                row = cur.fetchone()
                if row:
                    activity_id, current_count = row
                    cur.execute(
                        "UPDATE activity SET word_count = %s WHERE id = %s",
                        (current_count + word_count, activity_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO activity (chat_id, user_id, date, word_count) VALUES (%s, %s, %s, %s)",
                        (chat_id, user_id, today, word_count)
                    )
            conn.commit()
