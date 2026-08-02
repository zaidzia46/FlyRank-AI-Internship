from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from database import get_connection, init_db
from models import TaskIn

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


@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    body = await request.json()
    try:
        task_in = TaskIn(title=body.get("title", ""), done=body.get("done", False))
    except ValidationError:
        return JSONResponse(status_code=400, content={"error": "title is required"})

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?);",
            (task_in.title, int(task_in.done)),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?;", (cursor.lastrowid,)).fetchone()
        return row_to_task(row)
    finally:
        conn.close()


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    body = await request.json()
    try:
        task_in = TaskIn(title=body.get("title", ""), done=body.get("done", False))
    except ValidationError:
        return JSONResponse(status_code=400, content={"error": "title is required"})

    conn = get_connection()
    try:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
        if existing is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?;",
            (task_in.title, int(task_in.done), task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
        return row_to_task(row)
    finally:
        conn.close()


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
        if existing is None:
            return JSONResponse(status_code=404, content={"error": "Task not found"})

        conn.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
        conn.commit()
        return JSONResponse(status_code=204, content=None)
    finally:
        conn.close()
