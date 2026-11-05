CREATE TABLE IF NOT EXISTS profiles (
    player_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    money REAL NOT NULL DEFAULT 1000.0 CHECK(money >= 0)
);

CREATE TABLE IF NOT EXISTS inventory (
    player_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),

    PRIMARY KEY (player_id, item_id),
    FOREIGN KEY (player_id) REFERENCES profiles(player_id)
);

CREATE TABLE IF NOT EXISTS market_state (
    item_id TEXT PRIMARY KEY,
    current_price REAL NOT NULL CHECK (current_price > 0),
    current_state INTEGER NOT NULL
        CHECK (current_state BETWEEN 0 AND 4)
);