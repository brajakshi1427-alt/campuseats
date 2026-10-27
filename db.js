// Database layer. MySQL (mysql2) when MYSQL_HOST is set; otherwise zero-setup SQL via sql.js (SQLite file in ./data).
// Both paths run real SQL with ? placeholders: query(sql, params) -> { rows, insertId }
const fs = require('fs');
const path = require('path');
let impl;

async function init() {
  if (impl) return impl;
  if (process.env.MYSQL_HOST) {
    const mysql = require('mysql2/promise');
    const pool = mysql.createPool({
      host: process.env.MYSQL_HOST, port: +process.env.MYSQL_PORT || 3306,
      user: process.env.MYSQL_USER || 'root', password: process.env.MYSQL_PASSWORD || '',
      database: process.env.MYSQL_DATABASE || 'campuseats', decimalNumbers: true
    });
    impl = {
      kind: 'MySQL',
      async query(sql, params = []) {
        const [r] = await pool.query(sql, params);
        return Array.isArray(r) ? { rows: r } : { rows: [], insertId: r.insertId };
      }
    };
  } else {
    const initSqlJs = require('sql.js');
    const SQL = await initSqlJs();
    const file = path.join(__dirname, 'data', 'campuseats.sqlite');
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const db = fs.existsSync(file) ? new SQL.Database(fs.readFileSync(file)) : new SQL.Database();
    db.run(`CREATE TABLE IF NOT EXISTS dishes (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, category TEXT, available INTEGER NOT NULL DEFAULT 1)`);
    if (db.exec('SELECT COUNT(*) FROM dishes')[0].values[0][0] === 0) {
      db.run(`INSERT INTO dishes (name, price, category, available) VALUES
        ('Masala Dosa', 60, 'South Indian', 1), ('Veg Burger', 80, 'Fast Food', 1),
        ('Paneer Roll', 90, 'Fast Food', 1), ('Cold Coffee', 50, 'Beverages', 0)`);
    }
    const save = () => fs.writeFileSync(file, Buffer.from(db.export()));
    impl = {
      kind: 'SQLite (sql.js)',
      async query(sql, params = []) {
        if (/^\s*select/i.test(sql)) {
          const st = db.prepare(sql); st.bind(params);
          const rows = []; while (st.step()) rows.push(st.getAsObject()); st.free();
          return { rows };
        }
        db.run(sql, params);
        const insertId = db.exec('SELECT last_insert_rowid()')[0].values[0][0];
        save();
        return { rows: [], insertId };
      }
    };
  }
  return impl;
}
module.exports = { init };
