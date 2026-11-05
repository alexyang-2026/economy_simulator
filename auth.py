import sqlite3

def register_player(conn, username, email):
    cursor = conn.execute(
        "INSERT INTO profiles (username, email) VALUES (?, ?)",
        (username, email)
    )
    # Default money already identified in schema.sql as 1k
    # player_id also auto assigned by sqlite

    conn.commit()
    return cursor.lastrowid


def handle_login_and_registration(conn):
    choice = input("Welcome to Economy Simulator! To create a new account, press 1. To use an existing account, press anything else.")

    if choice == "1":
        while True:
            username = input("Please select a username: ").strip()
            email = input("Please type your email: ").strip()
            try:
                user_id = register_player(conn, username, email)
                break
            except sqlite3.IntegrityError:
                print("Registration failed. Please check your username and email :)\n")

    else:
        while True:
            username = input("Please enter your username of the account you wish to play in:")

            cursor = conn.execute(
                "SELECT player_id FROM profiles WHERE username = ?",
                (username,)
            )

            result = cursor.fetchone()

            if result is None:
                print("Username not found. Please try again :)\n")
            else:
                user_id = result[0]
                break

    return user_id


def get_user_assets(conn, user_id):
    cursor = conn.execute(
        "SELECT money FROM profiles WHERE player_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result is None:
        return None

    balance = result[0]

    cursor = conn.execute(
        "SELECT item_id, quantity FROM inventory WHERE player_id = ?",
        (user_id,)
    )

    inventory = {
        item_id: quantity
        for item_id, quantity in cursor.fetchall()
    }

    return {
        "balance": balance,
        "inventory": inventory
    }

