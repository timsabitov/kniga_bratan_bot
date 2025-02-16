import psycopg2

class Database:
    def __init__(self, db_url):
        self.db_url = db_url

    def get_connection(self):
        return psycopg2.connect(self.db_url)

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
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS birthdays (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        username TEXT NOT NULL,
                        birthday DATE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS activity (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        date DATE NOT NULL,
                        word_count INTEGER NOT NULL DEFAULT 0
                    );
                """)
            conn.commit()
