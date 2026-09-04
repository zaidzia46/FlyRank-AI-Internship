# Stage 2: The public & protected gates

What this stage adds:
- `GET /public/info` - always 200, no auth.
- `GET /protected/profile` - 401 if no `Authorization: Bearer <token>` header is present. Doesn't verify the token yet.

Checkpoint:
```
curl -i http://localhost:3000/public/info                 # -> 200
curl -i http://localhost:3000/protected/profile            # -> 401 (no token sent)
```

Commit message: `Stage 2: public route and unverified protected route`
