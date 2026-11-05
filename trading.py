from difflib import get_close_matches

AGREEMENT_WORDS = {"y", "yes", "yeah", "yea", "yep", "yh", "yeap"}

def buy_item(conn, user_id, user_assets, markets_config, items_dict):
    print("Welcome to the Marketplace!\n")

    name_to_id = {
        item_data["name"].casefold(): item_id
        for item_id, item_data in items_dict.items()
        if item_id in markets_config
    }

    while True:
        item = input("Enter the item you want to buy (or type 0 to exit): ").strip().casefold()

        if item == "0":
            return

        if item not in name_to_id:
            matches = get_close_matches(item, list(name_to_id), n=3, cutoff=0.5)

            if not matches:
                print("No matching commodities found. Please try again.\n")
                continue

            print("Did you mean", matches[0], "? (y/n)")
            confirm_typo = input("> ").strip().lower()

            if confirm_typo in AGREEMENT_WORDS:
                item = matches[0]
            else:
                print("Aborted.\n")
                continue

        item_id = name_to_id[item]

        cursor = conn.execute(
            "SELECT current_price from market_state WHERE item_id = ?",
            (item_id,)
        )

        result = cursor.fetchone()

        if result is None:
            print("This commodity is currently unavailable.\n")
            continue

        current_price = result[0]

        print(f"\nThe current price of {item} is ${current_price:.2f}")
        print("How many would you like to buy? (type 0 to abort): ")

        while True:
            try:
                quantity = int(input("> ").strip())
                break

            except ValueError:
                print("Your inputted quantity must be an integer! Please try again:")

        if quantity == 0:
            print("Purchase aborted.")
            return

        if quantity < 0:
            print("Quantity cannot be negative!")
            continue

        unit_price = round(current_price, 2) 
        total_price = round(unit_price * quantity, 2) # This is because Python uses binary floating-point arithmetic, even though normally a 2 d.p. number times an integer will be at most 2 d.p.

        if user_assets["balance"] < total_price:
            print(f"You don't have enough money to buy that much! Current balance: ${user_assets['balance']:.2f}\n")
            continue

        confirm_purchase = input("\nConfirm Purchase? (y/n): ").strip().casefold()
        if confirm_purchase not in AGREEMENT_WORDS:
            print("Aborted.\n")
            continue

        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE profiles 
                    SET money = money - ? 
                    WHERE player_id = ? AND money >= ?
                    """,
                    (total_price, user_id, total_price)
                )

                if cursor.rowcount == 0:
                    raise ValueError("Insufficient funds or player not found.")

                conn.execute(
                    """
                    INSERT INTO inventory (player_id, item_id, quantity)
                    VALUES (?, ?, ?)
                    ON CONFLICT(player_id, item_id)
                    DO UPDATE SET quantity = inventory.quantity + excluded.quantity
                    """,
                    (user_id, item_id, quantity)
                )

        except ValueError as e:
            print(f"Purchase failed: {e}")
            continue

        user_assets["balance"] = round(user_assets["balance"] - total_price, 2)
        user_assets["inventory"][item_id] = (user_assets["inventory"].get(item_id, 0) + quantity)

        print(f"Successfully purchased {quantity} {item} for ${total_price:.2f}!")
        return

        

        
        
                

