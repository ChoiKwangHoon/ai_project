"""
db_manager.py
- PostgreSQL 기반 로그 저장/조회
"""

import psycopg2
from psycopg2.extras import RealDictCursor

class DBManager:
    def __init__(self, host, port, dbname, user, password):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def insert_log(self, question: str, answer: str):
        self.cursor.execute(
            "INSERT INTO logs (question, answer) VALUES (%s, %s)",
            (question, answer)
        )
        self.conn.commit()

    def get_recent_logs(self, limit: int = 10):
        self.cursor.execute(
            "SELECT question, answer FROM logs ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_top_faq(self, limit: int = 5):
        self.cursor.execute(
            "SELECT question, COUNT(*) as cnt FROM logs GROUP BY question ORDER BY cnt DESC LIMIT %s",
            (limit,)
        )
        return self.cursor.fetchall()
