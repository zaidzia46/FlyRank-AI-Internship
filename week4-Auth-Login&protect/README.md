# FlyRank A4 — Auth · Login & protect (NeonDB edition)

A small Express API with full authentication: sign up, log in, log out, and a protected
`/profile` route guarded by JWTs.

**Note on the Identity Provider swap:** the original assignment uses Supabase Auth, which
hashes passwords and signs/verifies JWTs for you. NeonDB is *just* a Postgres database — it has
no auth layer — so this version does that work itself with `bcryptjs` (password hashing) and
`jsonwebtoken` (signing/verifying tokens). Functionally it's the same trust flow: client →
credentials → server issues a JWT → client sends the JWT on every request → server verifies it.

## Setup

1. `npm install`
2. Create a free project at [neon.tech](https://neon.tech) and copy the **pooled** connection string.
3. Copy `.env.example` to `.env` and fill in `DATABASE_URL` and a random `JWT_SECRET`.
4. Run `schema.sql` against your database once (Neon SQL Editor, or `psql "$DATABASE_URL" -f schema.sql`).

## Run

```
npm start
```

Swagger UI: http://localhost:3000/docs

## API reference

| Route | Method | Auth required | Success | Notes |
|---|---|---|---|---|
| `/auth/signup` | POST | none | 201 | body: `{ email, password }` |
| `/auth/login` | POST | none | 200 | returns `access_token` + `refresh_token` |
| `/auth/logout` | POST | Bearer token | 204 | blacklists the token in memory |
| `/protected/profile` | GET | Bearer token | 200 | returns the logged-in user |
| `/protected/dashboard` | GET | Bearer token | 200 | same guard, reused |
| `/public/info` | GET | none | 200 | open data |

Status codes: `400` missing input · `401` missing/invalid/expired token or bad credentials.

## Swagger screenshot

_Add your screenshot of `/docs` with the Authorize padlock here before submitting._

## Project structure

```
db.js                 Neon connection pool
schema.sql             users table
tokenBlacklist.js       in-memory logout tracking
middleware/auth.js      verifyToken guard (reused across protected routes)
routes/auth.js          signup, login, logout
routes/public.js        public/info
routes/protected.js     protected/profile, protected/dashboard
openapi.json             Swagger/OpenAPI spec with bearer auth
server.js                app entrypoint
```
