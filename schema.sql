-- CampusEats database schema sketch
-- Each table belongs to exactly one service boundary.

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    role VARCHAR(30) NOT NULL
);

CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE cafeterias (
    cafeteria_id INTEGER PRIMARY KEY,
    vendor_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE menus (
    menu_id INTEGER PRIMARY KEY,
    cafeteria_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (cafeteria_id) REFERENCES cafeterias(cafeteria_id)
);

CREATE TABLE food_items (
    item_id INTEGER PRIMARY KEY,
    menu_id INTEGER NOT NULL,
    name VARCHAR(150) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    availability BOOLEAN NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES menus(menu_id)
);

CREATE TABLE carts (
    cart_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE cart_items (
    cart_item_id INTEGER PRIMARY KEY,
    cart_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    -- item_id is a reference to Catalogue Service's food item,
    -- but there is intentionally no cross-service database FK.
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    cart_id INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    -- user_id is resolved through the User Service contract.
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
    -- item_id is a Catalogue Service reference, not a cross-service FK.
);

CREATE TABLE deliveries (
    delivery_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    address VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) NOT NULL
    -- order_id is resolved through the Order Service contract.
);

CREATE TABLE notifications (
    notification_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    message VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL
    -- user_id/order_id are service references; no cross-service FKs.
);
