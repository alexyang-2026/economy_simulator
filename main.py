import markets
import database
import time

def main():
    database.initialize_database()
    conn = database.connect_db()

    try:
        markets_config = markets.load_market_data_from_json()
        markets.initialize_market(markets_config, conn)

        conn.commit()
        print(database.get_market_state(conn))

        # Dictionary to store when the next market updates are
        next_updates = markets.initialize_market_schedule(markets_config)

        # Main Game Loop
        while True:
            markets.process_market_updates(conn, markets_config, next_updates)
            time.sleep(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()