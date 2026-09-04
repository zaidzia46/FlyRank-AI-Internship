# Stage 0: Set up NeonDB & the server

What this stage does:
- Creates a free Neon project (https://neon.tech) and a `users` table (see `schema.sql`).
- Loads `DATABASE_URL` / `JWT_SECRET` / `PORT` from a git-ignored `.env`.
- Boots an Express server and confirms it can talk to Neon with `SELECT 1`.

Setup:
1. `npm install`
2. Create a Neon project, copy the pooled connection string into `.env` (copy `.env.example` first).
3. Run `schema.sql` against your Neon database (SQL Editor in the Neon console, or `psql "$DATABASE_URL" -f schema.sql`).
4. `npm start`

Checkpoint:
```
node server.js
# -> "Server running on port 3000 and connected to NeonDB"
```

Commit message: `Stage 0: setup server and neon db connection`
