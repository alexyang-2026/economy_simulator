def get_inventory(conn, player_id):
    """
    Retrieve the player's item quantities from SQLite.
    
    Args:
        conn (sqlite3.Connection): an active database connection.
        player_id (int): an identifier of the player

    Returns:
        dict: maps item IDs to their quantities in the player's inventory.
    """
    cursor = conn.execute(
        "SELECT item_id, quantity FROM inventory WHERE player_id = ?",
        (player_id,)
    )

    return dict(cursor.fetchall())

def add_item(conn, player_id, item_id, quantity):
    """
    Add a positive quantity of an item to a player's inventory.

    Args:
        conn (sqlite3.Connection): Active database connection.
        player_id (int): ID of the player.
        item_id (str): ID of the item.
        quantity (int): Number of units to add.

    Raises:
        ValueError: If quantity is not a positive integer.
    """
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")

    conn.execute(
        """
        INSERT INTO inventory (player_id, item_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(player_id, item_id)
        DO UPDATE SET quantity = quantity + excluded.quantity
        """,
        (player_id, item_id, quantity)
    )

def remove_item(conn, player_id, item_id, quantity):
    """
    Removes a positive quantity of an item from a player's inventory.

    Args:
        conn (sqlite3.Connection): Active database connection.
        player_id (int): ID of the player.
        item_id (str): ID of the item.
        quantity (int): Number of units to remove.

    Raises:
        ValueError: If quantity is not a positive integer.
    """
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a positive integer!")

    cursor = conn.execute(
        """
        UPDATE inventory
        SET quantity = quantity - ?
        WHERE player_id = ?
            AND item_id = ?
            AND quantity >= ?
        """,
        (quantity, player_id, item_id, quantity)
    )

    return cursor.rowcount == 1


