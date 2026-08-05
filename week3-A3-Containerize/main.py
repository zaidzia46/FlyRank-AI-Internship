from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from models import TaskIn
from postgres_repository import PostgresTaskRepository

app = FastAPI()
repo = PostgresTaskRepository()


@app.get("/tasks")
def list_tasks():
    return repo.list_tasks()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = repo.get_task(task_id)
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task


@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    body = await request.json()
    try:
        task_in = TaskIn(title=body.get("title", ""), done=body.get("done", False))
    except ValidationError:
        return JSONResponse(status_code=400, content={"error": "title is required"})
    return repo.create_task(task_in.title, task_in.done)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    body = await request.json()
    try:
        task_in = TaskIn(title=body.get("title", ""), done=body.get("done", False))
    except ValidationError:
        return JSONResponse(status_code=400, content={"error": "title is required"})

    existing = repo.get_task(task_id)
    if existing is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})

    return repo.update_task(task_id, task_in.title, task_in.done)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    deleted = repo.delete_task(task_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return JSONResponse(status_code=204, content=None)
