-- StackBridge Production Database Schema
-- Dumped: sometime last year
-- DO NOT RUN THIS ON PROD - it drops everything first
-- (we run this script manually when we need to reset)

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;

-- users table
-- note: passwords stored as md5, we know it's bad but migration is scary
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password    VARCHAR(255),          -- md5 hash
    full_name   VARCHAR(255),
    role        VARCHAR(50) DEFAULT 'user',
    api_key     VARCHAR(255),          -- plain text, used for internal calls
    created_at  TIMESTAMP DEFAULT NOW()
);

-- products - jake added these columns directly in prod last tuesday
CREATE TABLE products (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    price        NUMERIC(10,2),
    stock        INT DEFAULT 0,
    category     VARCHAR(100),
    internal_cost NUMERIC(10,2),       -- DO NOT EXPOSE IN API
    created_at   TIMESTAMP DEFAULT NOW()
);

-- orders
CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    customer_id INT REFERENCES users(id),
    product     VARCHAR(255),
    quantity    INT,
    status      VARCHAR(50) DEFAULT 'pending',
    total       NUMERIC(10,2),
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- audit_log - added by compliance, nobody reads it
CREATE TABLE audit_log (
    id         SERIAL PRIMARY KEY,
    user_id    INT,
    action     TEXT,
    timestamp  TIMESTAMP DEFAULT NOW()
);

-- seed data for staging (also run against prod by accident twice)
INSERT INTO users (email, password, full_name, role, api_key) VALUES
('admin@stackbridge.io',    md5('admin123'),   'Admin User',    'admin', 'sk_internal_abc123'),
('ops@stackbridge.io',      md5('ops2024'),    'Ops Team',      'ops',   'sk_internal_xyz789'),
('developer@stackbridge.io',md5('dev123'),     'Dev User',      'user',  NULL);

INSERT INTO products (name, price, stock, category, internal_cost) VALUES
('Widget A',  29.99, 100, 'hardware', 12.50),
('Widget B',  49.99, 50,  'hardware', 22.00),
('Service X', 99.00, 999, 'software', 5.00);

INSERT INTO orders (customer_id, product, quantity, status, total) VALUES
(1, 'Widget A', 2, 'completed', 59.98),
(2, 'Service X', 1, 'pending',  99.00);

-- index jake said we needed (no idea if it helps)
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- backup policy: jake takes a manual dump every friday
-- restore procedure: ask jake
