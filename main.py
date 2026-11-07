import markets
import database
import auth
import items
import trading
import threading
import corporations

MAIN_MENU = """
========== MAIN MENU ==========
1. View Assets
2. View Marketplace
3. Buy Commodities
0. Exit Game
"""

CORPORATION_DAY_INTERVAL = 20 * 60
MARKET_CHECK_INTERVAL = 1

def corporation_simulation_loop(stop_event, C, B, item_index, recipe_index, corporations_config):
    conn = database.connect_db()

    try:
        while not stop_event.wait(CORPORATION_DAY_INTERVAL):
            corporations.simulate_corporation_day(
                conn, C, B, item_index, recipe_index, corporations_config
            )

    finally:
        conn.close()

def market_simulation_loop(stop_event, markets_config, next_updates):
    conn = database.connect_db()

    try:
        while not stop_event.wait(MARKET_CHECK_INTERVAL):
            markets.process_market_updates(conn, markets_config, next_updates)

    finally:
        conn.close()

def main():
    database.initialize_database()
    conn = database.connect_db()

    try:
        markets_config = markets.load_market_data_from_json()
        markets.initialize_market(markets_config, conn)

        items_dict, recipes_dict = items.load_items_and_recipes()

        C, B, item_index, recipe_index = items.build_crafting_matrices(items_dict, recipes_dict)
        corporations_config = corporations.load_corporations()

        stop_event = threading.Event()
        corporation_thread = None
        market_thread = None

        corporation_thread = threading.Thread(
            target=corporation_simulation_loop,
            args=(stop_event, C, B, item_index, recipe_index, corporations_config),
            daemon=True
        )

        # Dictionary to store when the next market updates are
        next_updates = markets.initialize_market_schedule(markets_config)

        market_thread = threading.Thread(
            target=market_simulation_loop,
            args=(stop_event, markets_config, next_updates),
            daemon=True
        )

        # Register or login
        user_id = auth.handle_login_and_registration(conn)
        user_assets = auth.get_user_assets(conn, user_id)

        corporation_thread.start()
        market_thread.start()

        # Main Game Loop
        while True:
            print(MAIN_MENU)
            choice = input("\nSelect an option: ").strip()

            if choice == "1":
                print(f"\nBalance: ${user_assets['balance']:,.2f}")
                print("\nInventory:")

                if not user_assets["inventory"]:
                    print("Your inventory is empty.")
                else:
                    for item_id, quantity in user_assets["inventory"].items():
                        name = items_dict[item_id]["name"]
                        print(f"{name}: {quantity}")


            elif choice == "2":
                print("\n========== MARKETPLACE ==========")

                cursor = conn.execute(
                    """
                    SELECT item_id, current_price, current_state
                    FROM market_state
                    ORDER BY item_id
                    """
                )

                for item_id, price, state in cursor.fetchall():
                    name = items_dict[item_id]["name"]
                    state_name = markets.STATES[state]

                    print(f"{name}: ${price:.2f} | {state_name}")

            elif choice == "3":
                trading.buy_item(conn, user_id, user_assets, markets_config, items_dict)

            elif choice == "0":
                print("\nThanks for playing Economy Simulator!")
                break

            else:
                print("Invalid option. Please try again.")

    finally:
        stop_event.set()

        if corporation_thread is not None and corporation_thread.is_alive():
            corporation_thread.join()

        if market_thread is not None and market_thread.is_alive():
            market_thread.join()

        conn.close()

if __name__ == "__main__":
    main()