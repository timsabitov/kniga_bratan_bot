import logging
import time
from datetime import time as dtime
from telegram.ext import Application, MessageHandler, filters
from app.config import BOT_TOKEN, DATABASE_URL
from app.database import Database
from app.handlers import BotHandlers

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

time.sleep(10)

db = Database(DATABASE_URL)
db.init_db()

handlers = BotHandlers(db)

application = Application.builder().token(BOT_TOKEN).build()

# Планирование ежедневных задач через job_queue
application.job_queue.run_daily(handlers.reset_beauty_winner, dtime(0, 0), name="reset_beauty")
application.job_queue.run_daily(handlers.check_birthdays, dtime(0, 1), name="check_birthdays")

# Регистрируем обработчики команд
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^!add"), handlers.add_trigger))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^!del"), handlers.delete_trigger))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^!list$"), handlers.list_triggers))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^!bd\s+\d{2}\.\d{2}\.\d{4}"), handlers.handle_birthday_set))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^!help$"), handlers.help_command))
application.add_handler(MessageHandler(filters.TEXT & (filters.Regex("(?i)^!talker$") | filters.Regex("(?i)^болтун$")), handlers.handle_talker_command))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^книга братан$"), handlers.handle_kniga_bratan))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^(кто красавчик сегодня|красавчик сегодня|красавчик)$"), handlers.handle_beauty_trigger))
application.add_handler(MessageHandler(filters.TEXT & ~filters.Regex("(?i)^!"), handlers.handle_trigger_invocation))
application.add_handler(MessageHandler(filters.TEXT & ~filters.Regex("(?i)^!"), handlers.update_activity))

application.run_polling()
