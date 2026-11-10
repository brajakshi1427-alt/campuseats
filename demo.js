'use strict';
// Runs the five cases from Task 6 against the real server and prints the
// results (also saved to demo-output.txt - handy for screenshots).
require('./setup-env');
const fs = require('fs');
const path = require('path');
const app = require('./server');

const lines = [];
const out = text => { console.log(text); lines.push(text); };

async function call(label, method, url, { token, body } = {}) {
  const headers = {};
  if (body) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  out(`\n### ${label}`);
  out(`> ${method} ${url.replace(/^https?:\/\/[^/]+/, '')}${token ? '   (Authorization: Bearer <token>)' : '   (no token)'}`);
  out(`< HTTP ${res.status} ${res.statusText}`);
  out(`< ${text.length > 400 ? text.slice(0, 400) + ' ...' : text}`);
  try { return { status: res.status, json: JSON.parse(text) }; } catch (_) { return { status: res.status }; }
}

(async () => {
  const server = app.listen(0);
  const base = `http://localhost:${server.address().port}`;
  try {
    out('CampusEats Assignment 9 - secured API demo');

    await call('1) No token  ->  401', 'GET', `${base}/items`);

    const cust = await call('2) Login as customer  ->  200 + token', 'POST', `${base}/login`,
      { body: { username: 'customer', password: 'customer123' } });
    await call('   (wrong password  ->  401)', 'POST', `${base}/login`,
      { body: { username: 'customer', password: 'wrong' } });

    await call('3) Customer + token on read route  ->  200', 'GET', `${base}/items`, { token: cust.json.token });

    const rest = await call('   Login as restaurant  ->  200 + token', 'POST', `${base}/login`,
      { body: { username: 'restaurant', password: 'restaurant123' } });
    await call('4) Restaurant creates an item  ->  201', 'POST', `${base}/items`,
      { token: rest.json.token, body: { name: 'Veg Sandwich', price: 75, available: true } });

    await call('5) Customer tries to create an item  ->  403', 'POST', `${base}/items`,
      { token: cust.json.token, body: { name: 'Hacked Dish', price: 1 } });

    await call('   (tampered token  ->  401)', 'GET', `${base}/items`, { token: cust.json.token + 'x' });
    out('\nDone: 401 / login / 200 / 201 / 403 all shown above.');
  } catch (err) {
    console.error('Demo failed:', err);
    process.exitCode = 1;
  } finally {
    server.close();
    fs.writeFileSync(path.join(__dirname, 'demo-output.txt'), lines.join('\n') + '\n');
  }
})();
