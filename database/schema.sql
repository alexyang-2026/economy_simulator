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

CREATE TABLE IF NOT EXISTS corporation_earnings_history (
    corporation_id TEXT NOT NULL,
    start_day INTEGER NOT NULL,
    end_day INTEGER NOT NULL,
    profits BLOB NOT NULL,
    PRIMARY KEY (corporation_id, start_day)
);

CREATE TABLE IF NOT EXISTS simulation_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    current_day INTEGER NOT NULL DEFAULT 0
);

/* Initialize the game day at 0 */
INSERT OR IGNORE INTO simulation_state (id, current_day)
VALUES (1, 0);