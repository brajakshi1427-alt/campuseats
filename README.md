# CampusEats — Menu service in GraphQL (Assignment 7)

**Team:** `<Name Brajakshi mandloi  Roll No 20252651016>` · `<Name Vaishnavi Tiwari Roll No 20252651061>` · …
**Demo video:** `<Google Drive link -   https://drive.google.com/drive/folders/17vNkjCRJiTylgmmBA2pTqUqNFo6wpKXL?usp=sharing>`  ·  **Screenshots:** `screenshots/before.png`, `screenshots/after.png`

## Run (one step)
Double-click **`RUN.bat`** (Windows) or run `bash RUN.sh` (Mac/Linux). It installs dependencies, starts the server and opens http://localhost:4000.
Needs only Node.js 18+. No database setup: it uses a local SQLite file by default, or MySQL if you set `MYSQL_HOST` (see `schema.sql`, `docker-compose.yml`).

Try in the page: list the dishes, add "Paneer Roll" with price 90 — the new row appears (that is the mutation). Or POST to `/graphql`:
```graphql
query { dishes { id name price available } }
mutation { addDish(input: { name: "Paneer Roll", price: 90 }) { id name price } }
```

## Files
`schema.graphql` · `server.js` + `db.js` · `schema.sql` · `public/index.html`

## Answers
1. **Service picked:** Catalogue / Menu (dishes).
2. **Skippable vs required:** a client may skip `category` (nullable). It cannot skip `name`, `price`, `available`, `id` — the `!` means the server guarantees the field is never null, so clients can rely on it (and the server rejects an input that omits a `!` field).
3. **SQL mapping:** the `available` argument of `dishes(available: true)` becomes the `WHERE available = ?` clause (and `dish(id)` becomes `WHERE id = ?`); the **`addDish`** mutation resolver runs the `INSERT INTO dishes …`.
