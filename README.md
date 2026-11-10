# CampusEats — Securing the API (Assignment 9)

**Course:** CS543 Web Services  
**Service secured:** Menu / Catalogue (same service as Assignment 8)  
**Stack:** Node.js, Express, `jsonwebtoken`, `bcryptjs`, `dotenv`

**Team members:** Add roll numbers and names here.  
**Demo video + screenshots (Google Drive):** Add share link here.

## Run

Windows: double-click **`RUN.bat`** (installs packages the first time, creates `.env` with a random `JWT_SECRET`, opens http://localhost:4009).  
Mac/Linux: `bash RUN.sh`.

To print all five required cases in one go (for screenshots): double-click **`DEMO.bat`** (or `bash DEMO.sh`). The output is also saved in `demo-output.txt`.

Manual setup: `npm install`, copy `.env.example` to `.env`, put a long random value in `JWT_SECRET`, then `npm start`.

## Demo users (passwords are stored only as bcrypt hashes)

| Username | Password | Role |
|---|---|---|
| customer | customer123 | customer |
| restaurant | restaurant123 | restaurant |
| admin | admin123 | admin |

## Routes

| Method | Path | Needs | Result |
|---|---|---|---|
| POST | `/login` | nothing (public) | 200 + JWT, or 401 |
| GET | `/items` | valid token | 200, or 401 |
| GET | `/items/:id` | valid token | 200 / 404, or 401 |
| POST | `/items` | valid token **and** role `restaurant` or `admin` | 201 / 422, or 401 / 403 |

## Test with curl (Windows cmd — use `^` for line breaks, on Mac/Linux use `\`)

```bash
# 1. No token -> 401
curl -i http://localhost:4009/items

# 2. Login -> token
curl -i -X POST http://localhost:4009/login -H "Content-Type: application/json" -d "{\"username\":\"customer\",\"password\":\"customer123\"}"

# 3. With token -> 200   (paste the token from step 2)
curl -i http://localhost:4009/items -H "Authorization: Bearer <TOKEN>"

# 4. Restaurant logs in, then creates an item -> 201
curl -i -X POST http://localhost:4009/login -H "Content-Type: application/json" -d "{\"username\":\"restaurant\",\"password\":\"restaurant123\"}"
curl -i -X POST http://localhost:4009/items -H "Authorization: Bearer <RESTAURANT_TOKEN>" -H "Content-Type: application/json" -d "{\"name\":\"Veg Sandwich\",\"price\":75}"

# 5. Customer token on the write route -> 403
curl -i -X POST http://localhost:4009/items -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"name\":\"Test\",\"price\":10}"
```

The browser page at http://localhost:4009 has a login box too: log in as `customer` and try "Add a dish" to see the 403, then log in as `restaurant` to see the 201.

## Answers for the README questions

1. **Which routes need only authentication, and which also need a role?**  
   Only authentication (any logged-in user, roles `customer`, `restaurant`, `admin`): `GET /items` and `GET /items/:id`.  
   Authentication **and** a role: `POST /items`, allowed only for `restaurant` and `admin`.  
   `POST /login` is public because it is how a user gets a token.

2. **One 401 and one 403, and why that code and not the other.**  
   - `GET /items` with no token returns **401** `{"error":"Missing token. Send Authorization: Bearer <token>"}`. The server does not know who is calling, so authentication failed. It is not 403 because there is no identity to refuse yet.  
   - `POST /items` with a *customer* token returns **403** `{"error":"Forbidden: your role may not do this"}`. The token is valid, so the server knows who the caller is, but that role is not allowed to change data. It is not 401 because authentication succeeded.

3. **What is inside the JWT payload? Why trust the role claim? Why keep the secret out of code?**  
   The payload is `{ "id": <user id>, "role": <role>, "iat": <issued at>, "exp": <expiry> }`.  
   The role claim can be trusted because the token is signed (HMAC-SHA256) with the server's secret. If anyone edits the payload (for example changes `customer` to `admin`), the signature no longer matches and `jwt.verify` rejects it with 401. Only someone who knows the secret can create a valid token. The role is also never taken from the request body.  
   The secret must stay out of the code (and out of GitHub) because anyone who has it can sign their own tokens with any role and become admin. So it is read from `process.env.JWT_SECRET` (the `.env` file is git-ignored; only `.env.example` with a blank value is committed), and it can be changed per environment without touching the code.

## Notes on the implementation

- Passwords are hashed with `bcrypt.hashSync` and checked with `bcrypt.compareSync`; plain passwords are never stored or returned.
- Wrong username and wrong password give the same 401 message, so an attacker cannot find out which usernames exist.
- `jwt.verify` is called with `algorithms: ['HS256']` and tokens expire (`expiresIn`, default `1h`; an expired token gives 401 "Token expired").
- Middleware order on the write route is `auth` first, then `requireRole(...)`: *who are you?* then *may you?*

## Submission checklist

- [ ] Add team names + roll numbers above
- [ ] Take screenshots of the five cases (run `DEMO.bat`, or use curl / the browser page)
- [ ] Record a short demo video and upload to Google Drive, paste the link above
- [ ] Push to GitHub (`.env` must NOT be committed — it is already in `.gitignore`)
