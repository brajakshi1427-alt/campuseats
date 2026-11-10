'use strict';

// CampusEats - Assignment 9: Securing the API
// Menu / Catalogue service from Assignment 8, now protected with
//   1) bcrypt-hashed users          2) POST /login  -> JWT
//   3) auth middleware (401)        4) requireRole middleware (403)
//   5) secret read from process.env.JWT_SECRET (.env, git-ignored)

const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const PORT = Number(process.env.PORT) || 4009;
const SECRET = process.env.JWT_SECRET;
const TOKEN_TTL = process.env.JWT_EXPIRES_IN || '1h';

if (!SECRET) {
  console.error('\nJWT_SECRET is not set.');
  console.error('Copy .env.example to .env and put a long random value in JWT_SECRET');
  console.error('(or just double-click RUN.bat, it creates .env for you).\n');
  process.exit(1);
}

const app = express();
app.disable('x-powered-by');
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ---------------------------------------------------------------- data
// Menu items stay in an in-memory array, exactly like Assignment 8.
let items = [
  { id: 1, name: 'Masala Dosa', price: 60, available: true },
  { id: 2, name: 'Veg Burger', price: 80, available: true },
  { id: 3, name: 'Paneer Roll', price: 90, available: true },
  { id: 4, name: 'Cold Coffee', price: 50, available: false }
];
let nextId = Math.max(...items.map(item => item.id)) + 1;

// ------------------------------------------------- users (hash only!)
// Plain passwords exist only in this seed list at start-up; what is kept in
// memory and used for every login is the bcrypt hash.
const SEED = [
  { id: 1, username: 'customer',   password: 'customer123',   role: 'customer' },
  { id: 2, username: 'restaurant', password: 'restaurant123', role: 'restaurant' },
  { id: 3, username: 'admin',      password: 'admin123',      role: 'admin' }
];
const users = SEED.map(u => ({
  id: u.id,
  username: u.username,
  role: u.role,
  passwordHash: bcrypt.hashSync(u.password, 10)
}));
// Used when the username does not exist, so the response time is similar.
const DUMMY_HASH = bcrypt.hashSync('not-a-real-password', 10);

// ------------------------------------------------------------- login
// POST /login  { username, password }  ->  200 { token } | 401
app.post('/login', (req, res) => {
  const body = req.body || {};
  const username = typeof body.username === 'string' ? body.username.trim() : '';
  const password = typeof body.password === 'string' ? body.password : '';

  const user = users.find(u => u.username === username);
  const ok = bcrypt.compareSync(password, user ? user.passwordHash : DUMMY_HASH);

  if (!user || !ok) {
    // Same message for "no such user" and "wrong password".
    return res.status(401).json({ error: 'Invalid username or password' });
  }

  const token = jwt.sign(
    { id: user.id, role: user.role },
    SECRET,
    { expiresIn: TOKEN_TTL }
  );
  return res.status(200).json({
    token,
    tokenType: 'Bearer',
    expiresIn: TOKEN_TTL,
    user: { id: user.id, username: user.username, role: user.role }
  });
});

// ---------------------------------------------------- the two guards
// 1) authenticate: who are you?   (401 if token missing / invalid / expired)
function auth(req, res, next) {
  const header = req.get('Authorization') || '';
  const [scheme, token] = header.split(' ');

  if (!token || String(scheme).toLowerCase() !== 'bearer') {
    return res.status(401).json({ error: 'Missing token. Send Authorization: Bearer <token>' });
  }
  try {
    req.user = jwt.verify(token, SECRET, { algorithms: ['HS256'] });
    return next();
  } catch (err) {
    const message = err.name === 'TokenExpiredError' ? 'Token expired' : 'Invalid token';
    return res.status(401).json({ error: message });
  }
}

// 2) authorize: may you?          (403 if role is not allowed)
const requireRole = (...allowed) => (req, res, next) =>
  req.user && allowed.includes(req.user.role)
    ? next()
    : res.status(403).json({ error: 'Forbidden: your role may not do this', yourRole: req.user && req.user.role });

// ------------------------------------------------------------ routes
// Read routes: any logged-in user.
app.get('/items', auth, (req, res) => {
  res.status(200).json(items);
});

app.get('/items/:id', auth, (req, res) => {
  const id = Number(req.params.id);
  const item = Number.isInteger(id) && id > 0
    ? items.find(entry => entry.id === id)
    : undefined;
  if (!item) {
    return res.status(404).json({ error: 'Item not found', id: req.params.id });
  }
  return res.status(200).json(item);
});

// Write route: authenticated AND role restaurant / admin.
app.post('/items', auth, requireRole('restaurant', 'admin'), (req, res) => {
  const body = req.body || {};
  const name = typeof body.name === 'string' ? body.name.trim() : '';
  const price = Number(body.price);

  if (!name) {
    return res.status(422).json({ error: 'Validation failed', message: 'name is required and cannot be empty.' });
  }
  if (body.price === undefined || body.price === null || body.price === '' ||
      !Number.isFinite(price) || price <= 0) {
    return res.status(422).json({ error: 'Validation failed', message: 'price must be a positive number.' });
  }
  if (body.available !== undefined && typeof body.available !== 'boolean') {
    return res.status(422).json({ error: 'Validation failed', message: 'available must be true or false.' });
  }

  const newItem = {
    id: nextId++,
    name,
    price,
    available: body.available === undefined ? true : body.available
  };
  items.push(newItem);
  return res.status(201).json(newItem);
});

// Malformed JSON -> clear 400.
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({ error: 'Bad Request', message: 'Request body must contain valid JSON.' });
  }
  console.error(err);
  return res.status(500).json({ error: 'Internal Server Error' });
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`CampusEats Assignment 9 (secured API) running at http://localhost:${PORT}`);
    console.log('Demo users: customer/customer123, restaurant/restaurant123, admin/admin123');
  });
}

module.exports = app;
