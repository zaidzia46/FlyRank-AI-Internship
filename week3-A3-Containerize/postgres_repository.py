import os
import psycopg2
import psycopg2.extras

from repository import TaskRepository


class PostgresTaskRepository(TaskRepository):
    def __init__(self, dsn=None):
        self.dsn = dsn or os.environ["DATABASE_URL"]

    def _connect(self):
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = True
        return conn

    def list_tasks(self):
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM tasks ORDER BY id;")
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_task(self, task_id):
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def create_task(self, title, done=False):
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *;",
                    (title, done),
                )
                return dict(cur.fetchone())
        finally:
            conn.close()

    def update_task(self, task_id, title, done):
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *;",
                    (title, done, task_id),
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def delete_task(self, task_id):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
                return cur.rowcount > 0
        finally:
            conn.close()
