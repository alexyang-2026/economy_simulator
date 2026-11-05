import markets
import database
import auth
import items
import trading

MAIN_MENU = """
========== MAIN MENU ==========
1. View Assets
2. View Marketplace
3. Buy Commodities
0. Exit Game
"""

def main():
    database.initialize_database()
    conn = database.connect_db()

    try:
        markets_config = markets.load_market_data_from_json()
        markets.initialize_market(markets_config, conn)

        items_dict, recipes_dict = items.load_items_and_recipes()

        # Dictionary to store when the next market updates are
        next_updates = markets.initialize_market_schedule(markets_config)

        # Register or login
        user_id = auth.handle_login_and_registration(conn)
        user_assets = auth.get_user_assets(conn, user_id)

        # Main Game Loop
        while True:
            markets.process_market_updates(conn, markets_config, next_updates)
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
                trading.buy_item(
                    conn,
                    user_id,
                    user_assets,
                    markets_config,
                    items_dict
                )

            elif choice == "0":
                print("\nThanks for playing Economy Simulator!")
                break

            else:
                print("Invalid option. Please try again.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()