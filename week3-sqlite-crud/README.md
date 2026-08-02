# FlyRank Tasks API — SQLite version

A CRUD task API. Same endpoints as before, but tasks are now stored
in SQLite (`tasks.db`) instead of memory, so data survives a restart.

## Why SQLite

It's a single file, no server to install or configure. Good enough
for a project this size, and gives real persistence and real SQL.

## Where the database lives

`tasks.db`, created automatically the first time the app runs.
It's git-ignored, so a fresh clone starts clean and re-seeds itself.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Endpoints

- GET /tasks
- GET /tasks/{id}
- POST /tasks
- PUT /tasks/{id}
- DELETE /tasks/{id}

## Stage 4 — example query

```sql
SELECT COUNT(*) FROM tasks;
```
