-- MySQL table + seed rows (used when MYSQL_HOST is set; otherwise the app creates the same table in a local SQLite file)
CREATE DATABASE IF NOT EXISTS campuseats;
USE campuseats;

CREATE TABLE IF NOT EXISTS dishes (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  name      VARCHAR(100)  NOT NULL,
  price     DECIMAL(8,2)  NOT NULL,
  category  VARCHAR(50),
  available TINYINT(1)    NOT NULL DEFAULT 1
);

INSERT INTO dishes (name, price, category, available) VALUES
  ('Masala Dosa', 60.00, 'South Indian', 1),
  ('Veg Burger',  80.00, 'Fast Food',    1),
  ('Paneer Roll', 90.00, 'Fast Food',    1),
  ('Cold Coffee', 50.00, 'Beverages',    0);
