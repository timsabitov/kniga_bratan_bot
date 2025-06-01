import logging
import psycopg2

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_url):
        self.db_url = db_url

    def get_connection(self):
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def init_db(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS triggers (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        keyword TEXT NOT NULL,
                        type TEXT NOT NULL,
                        response TEXT NOT NULL,
                        added_by TEXT NOT NULL
                    );
                """)
                logger.info("Создана таблица: triggers")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS birthdays (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        username TEXT NOT NULL,
                        birthday DATE NOT NULL
                    );
                """)
                logger.info("Создана таблица: birthdays")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS activity (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        date DATE NOT NULL,
                        word_count INTEGER NOT NULL DEFAULT 0
                    );
                """)
                logger.info("Создана таблица: activity")
            conn.commit()
