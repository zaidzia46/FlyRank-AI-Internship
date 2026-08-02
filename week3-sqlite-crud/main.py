from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import get_connection, init_db

app = FastAPI()


@app.on_event("startup")
def on_startup():
    init_db()


def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.get("/tasks")
def list_tasks():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tasks;").fetchall()
        return [row_to_task(r) for r in rows]
    finally:
        conn.close()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})
        return row_to_task(row)
    finally:
        conn.close()
