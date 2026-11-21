-- EventBox's tables, as launched. Money in fils; event starts in UTC ("2026-12-03 17:00").
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer',  -- customer or organiser
    facebook_id TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    venue TEXT NOT NULL,
    starts_at TEXT NOT NULL,                -- UTC
    price_fils INTEGER NOT NULL,            -- 0: a free event
    capacity INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    organiser_id INTEGER NOT NULL REFERENCES users (id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events (id),
    user_id INTEGER REFERENCES users (id),  -- NULL: a guest
    email TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    total_fils INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'paid',    -- paid or refunded
    created_at TEXT NOT NULL
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders (id),
    event_id INTEGER NOT NULL REFERENCES events (id),
    qr TEXT NOT NULL UNIQUE,                -- what the QR code on the ticket holds
    checked_in_at TEXT
);

-- Every email the app sends, newest last (the mail server reads it).
CREATE TABLE outbox (
    id INTEGER PRIMARY KEY,
    to_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
