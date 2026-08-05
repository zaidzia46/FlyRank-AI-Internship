# Tasks API - Postgres + Docker

Same CRUD API, now backed by Postgres running in Docker instead of
SQLite. The routes never changed — only `postgres_repository.py`,
which implements the same `TaskRepository` interface the app talks to.

## Setup

```bash
cp .env.example .env
# edit .env if you want different values, defaults work fine locally
docker compose up
```

This starts Postgres (with a named volume, so data survives) and the
app, both from one command. API is at `http://localhost:8000`.

## Why the routes didn't change

`main.py` only calls methods on `repo` (`list_tasks`, `get_task`,
`create_task`, `update_task`, `delete_task`) — it never touches SQL.
`repository.py` defines that contract; `postgres_repository.py` is
just one implementation of it. Swapping storage meant writing a new
file, not editing the routes.

## How persistence was proven

1. `docker compose up`
2. `curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Test row"}'`
3. `docker compose down` (stops both containers)
4. `docker compose up` again
5. `curl http://localhost:8000/tasks` — the row from step 2 is still there,
   because it lives in the `pgdata` Docker volume, not in the container itself.

## Files

- `repository.py` — the interface (contract) any storage backend must follow
- `postgres_repository.py` — Postgres implementation using psycopg2
- `main.py` — FastAPI routes, storage-agnostic
- `init.sql` — creates the table and seeds 3 rows, runs once when the
  Postgres container is first created
- `docker-compose.yml` — app + db, one volume for data
- `.env.example` — committed template; real `.env` is gitignored
