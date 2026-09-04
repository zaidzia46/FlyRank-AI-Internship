# Stage 1: Open auth - Sign Up & Log In

What this stage adds:
- `POST /auth/signup` - validates input, hashes the password with bcrypt, stores the user in Neon, returns 201.
- `POST /auth/login` - checks credentials against the stored hash, signs a JWT access token + refresh token, returns 200.

Checkpoint:
```
curl -i -X POST http://localhost:3000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# -> 201

curl -i -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# -> 200, body includes "access_token"

curl -i -X POST http://localhost:3000/auth/signup -H "Content-Type: application/json" -d '{"email":"test@example.com"}'
# -> 400
```

Commit message: `Stage 1: signup and login routes working`
