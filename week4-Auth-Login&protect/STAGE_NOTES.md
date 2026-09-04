# Stage 4: Middleware protection & logout

What this stage adds:
- `middleware/auth.js` - the Stage 3 verification logic, extracted into one reusable `verifyToken` middleware.
- `/protected/profile` and a new `/protected/dashboard` both use it - zero new auth code for the second route.
- `POST /auth/logout` - itself protected by the same middleware; blacklists the token in memory, returns 204.
- `tokenBlacklist.js` - because JWTs are stateless, "logout" means we remember the token was revoked
  until it would have expired anyway.

Checkpoint:
```
curl -i http://localhost:3000/protected/dashboard -H "Authorization: Bearer <token>"   # -> 200
curl -i http://localhost:3000/protected/dashboard -H "Authorization: Bearer garbage"    # -> 401

curl -i -X POST http://localhost:3000/auth/logout -H "Authorization: Bearer <token>"    # -> 204
curl -i http://localhost:3000/protected/profile -H "Authorization: Bearer <same token>" # -> 401 now
```

Commit message: `Stage 4: auth middleware and logout endpoint`
