# Stage 3: The guard - token verification

What this stage adds:
- `GET /protected/profile` now actually verifies the JWT with `jsonwebtoken.verify()` using `JWT_SECRET`,
  then re-fetches the user row from Neon by the token's `sub` (user id).
- Tampered/expired tokens -> 401 `{"error": "Invalid or expired token"}`.

Checkpoint:
```
# log in first, grab access_token from the response
curl -i http://localhost:3000/protected/profile \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"
# -> 200 with your user details

# change one character of the token and re-run -> 401
```

Commit message: `Stage 3: profile route token verification`
