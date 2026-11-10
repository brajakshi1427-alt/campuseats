'use strict';
// Creates .env (git-ignored) with a random JWT secret if it does not exist yet.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath) && /^JWT_SECRET=.+/m.test(fs.readFileSync(envPath, 'utf8'))) {
  process.exit(0);
}
const secret = crypto.randomBytes(48).toString('hex');
const example = fs.readFileSync(path.join(__dirname, '.env.example'), 'utf8');
fs.writeFileSync(envPath, example.replace(/^JWT_SECRET=.*$/m, `JWT_SECRET=${secret}`));
console.log('Created .env with a new random JWT_SECRET.');
