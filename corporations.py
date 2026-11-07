import json
import numpy as np
import database
from scipy.optimize import milp, Bounds, LinearConstraint
from database import PROJECT_ROOT

CORPORATIONS_CONFIG_ROOT = PROJECT_ROOT / "game" / "corporations.json"

def load_corporations():
    with open(CORPORATIONS_CONFIG_ROOT, "r", encoding="utf-8") as file:
        corporations_config = json.load(file)

    return corporations_config


def get_commodity_prices(conn):
    """
    Retrieves commodity prices from playerdata.db.
    """
    rows = conn.execute("SELECT item_id, current_price FROM market_state").fetchall()
    commodity_prices = dict(rows)

    return commodity_prices


def calculate_corporaton_production_costs(conn, C, B, item_index, recipe_index, corporations_config):
    # p is the price vector that pulls data from the Sqlite3 database
    # Each row of p corresponds to a particular item
    p = np.zeros(len(item_index))
    commodity_prices = get_commodity_prices(conn)

    for item_id, current_price in commodity_prices.items():
        p[item_index[item_id]] = current_price

    # Now calculate (C^T)p through matrix multiplication
    # This will correspond to the input cost of executing every recipe once
    production_cost_vector = C.T @ p

    # Here, production_cost_vector[j] is the cost to execute recipe j once

    # Calculate revenue - B tells us how many items each recipe produces and p tells us the market price of each item
    production_revenue_vector = B.T @ p

    # Calculate profit
    profit_vector = production_revenue_vector - production_cost_vector

    # Calculate corporation production costs
    corporations_financials = {}

    for corporation_id, config in corporations_config.items():
        corporations_financials[corporation_id] = {}
        products = config["products"]
        for item in products:
            # Finds the row of B corresponding to the product
            item_row = item_index[item]

            # recipe_columns is a NumPy array containing the column indices of the recipe that produces a particular item
            # Just in case there is over 1 column that has the recipe
            recipe_columns = np.nonzero(B[item_row])[0]

            if len(recipe_columns) == 0:
                continue

            recipe_column = recipe_columns[0]

            corporations_financials[corporation_id][item] = {
                "cost": float(production_cost_vector[recipe_column]),
                "revenue": float(production_revenue_vector[recipe_column]),
                "profit": float(profit_vector[recipe_column])
            }

            # Index these three vectors with [recipe_column] because recipe_column
            # identifies the col in B corresponding to the recipe that produces a particular product


    return production_cost_vector, corporations_financials


def optimize_daily_production(corporations_config, corporations_financials):
    production_plans = {}

    for corporation_id, config in corporations_config.items():
        production_plans[corporation_id] = {}

        capacity = config["daily_production_capacity"]
        quotas = config["daily_quotas"]
        financials = corporations_financials[corporation_id]

        products = config["products"]
        profits = np.array([financials[product]["profit"] for product in products])
        minimum_quotas = np.array([quotas[product] for product in products])

        bounds = Bounds(lb=minimum_quotas, ub=np.inf) # No individual product has a maximum yet, but each product must meet its minimum quota

        # This represents q1 + q2 + ... + qk <= 20000
        capacity_constraint = LinearConstraint(
            A = np.ones((1, len(products))),     # A row of ones so every product's batch contributes equally to total production
            lb = 0,                             # Total production must be at least 0
            ub = capacity                       # Total production must not exceed 20,000 batches
        )

        result = milp(
            c=-profits,                         # Minimizing negative = maximizing profit because the largest positive number becomes the smallest negative number when multiplied by (-1)
            integrality=np.ones(len(products)),
            bounds=bounds,
            constraints=capacity_constraint
        )

        if not result.success:
            raise ValueError(f"Optimization failed for {corporation_id}: {result.message}")

        optimal_batches = result.x

        for product_index in range(len(optimal_batches)):
            current_product = products[product_index]
            optimal_amount = int(round(optimal_batches[product_index]))
            production_plans[corporation_id][current_product] = optimal_amount
    
    return production_plans

def calculate_daily_corporation_profits(production_plans, corporations_financials):
    daily_corporation_profits = {}

    for corporation_id in corporations_financials:

        products = list(production_plans[corporation_id].keys())

        total_profit = 0.0

        for product in products:
            profit_per_unit = corporations_financials[corporation_id][product]["profit"]
            units = production_plans[corporation_id][product]
            total_profit += profit_per_unit * units

        daily_corporation_profits[corporation_id] = total_profit

    return daily_corporation_profits


PROFIT_DATABASE_CHUNK_SIZE = 2000

def update_daily_corporation_profits_to_db(conn, daily_corporation_profits):
    """
    Store daily corporation profits in SQLite using chunked NumPy arrays.

    Each corporation's profit history is stored in BLOBs containing up to
    PROFIT_DATABASE_CHUNK_SIZE consecutive daily observations.

    The function determines the appropriate chunk from the current game day.
    If the chunk does not exist, it creates a new row. Otherwise, it retrieves
    the existing NumPy array, validates its length, appends the new daily profit, 
    and updates the BLOB.

    This function also advances the game day.

    Args:
        conn (sqlite3.Connection): Active SQLite database connection.
        daily_corporation_profits (dict): Maps corporation IDs to their
            total profit for the current simulated day.

    Raises:
        ValueError: If the number of stored observations does not match
            the expected number for the current game day.

    Returns:
        None: Earnings are saved directly to the database.

    Note:
        Database updates and game-day advancement should occur within
        the same transaction to maintain consistency.
    """
    with conn:
        game_day = conn.execute("SELECT current_day FROM simulation_state WHERE id = 1").fetchone()[0] + 1
        
        for corporation_id, corporation_profits in daily_corporation_profits.items():
            start_day = ((game_day - 1) // PROFIT_DATABASE_CHUNK_SIZE) * PROFIT_DATABASE_CHUNK_SIZE + 1     
            # The first -1 is for boundary cases like day 2000, day 4000, etc. for a chunk size of 2000
            # Without it, day 2000 data would be assigned to chunk 2, but that chunk should start at day 2001 because chunk 1 goes from day 1 to 2000

            cursor = conn.execute(
                """
                SELECT profits
                FROM corporation_earnings_history
                WHERE corporation_id = ? AND start_day = ?
                """,
                (corporation_id, start_day)
                
            ).fetchone()

            # If return NONE instead of Blob, create a new row
            if cursor is None:

                if game_day != start_day:
                    raise ValueError(f"Missing earnings history for {corporation_id}")
                
                end_day = start_day + PROFIT_DATABASE_CHUNK_SIZE - 1
                profits = np.array([round(corporation_profits, 2)], dtype=np.float64)

                conn.execute(
                    """
                    INSERT INTO corporation_earnings_history
                        (corporation_id, start_day, end_day, profits)
                    VALUES (?, ?, ?, ?)
                    """,
                    (corporation_id, start_day, end_day, profits.tobytes())
                )

            else:
                blob = cursor[0]
                profits = np.frombuffer(blob, dtype=np.float64)

                expected_length = game_day - start_day
                if len(profits) != expected_length:
                    raise ValueError(f"Earnings history out of sync for {corporation_id} on day {game_day}")
                
                profits = np.append(profits, round(corporation_profits, 2))

                conn.execute(
                    """
                    UPDATE corporation_earnings_history
                    SET profits = ?
                    WHERE corporation_id = ? AND start_day = ?
                    """,
                    (profits.tobytes(), corporation_id, start_day)
                )

        database.advance_game_day(conn)


def simulate_corporation_day(conn, C, B, item_index, recipe_index, corporations_config):
    """
    One full simulated corporation cycle.
    """
    _, corporations_financials = calculate_corporaton_production_costs(conn, C, B, item_index, recipe_index, corporations_config) # _ is the placeholder for production_cost_vector which we don't need right now
    production_plans = optimize_daily_production(corporations_config, corporations_financials)
    daily_corporation_profits = calculate_daily_corporation_profits(production_plans, corporations_financials)
    update_daily_corporation_profits_to_db(conn, daily_corporation_profits)




if __name__ == "__main__":
    import items
    import database

    conn = database.connect_db()

    try:
        gameitems, gamerecipes = items.load_items_and_recipes()

        C, B, item_index, recipe_index = items.build_crafting_matrices(
            gameitems, gamerecipes
        )

        corporations_config = load_corporations()

        _, corporations_financials = calculate_corporaton_production_costs(
            conn, C, B, item_index, recipe_index, corporations_config
        )

        production_plans = optimize_daily_production(
            corporations_config, corporations_financials
        )

        for corporation_id, plan in production_plans.items():
            config = corporations_config[corporation_id]
            financials = corporations_financials[corporation_id]

            total_batches = sum(plan.values())
            total_profit = sum(
                quantity * financials[product]["profit"]
                for product, quantity in plan.items()
            )

            print(f"\n========== {config['name']} ==========")

            for product, quantity in plan.items():
                quota = config["daily_quotas"][product]
                print(f"{product}: {quantity:,} batches (quota: {quota:,})")

                assert quantity >= quota, f"Quota violated: {product}"

            print(f"Total production: {total_batches:,}")
            print(f"Daily capacity: {config['daily_production_capacity']:,}")
            print(f"Expected daily profit: ${total_profit:,.2f}")

            assert total_batches <= config["daily_production_capacity"], (
                f"Capacity exceeded: {corporation_id}"
            )

        print("\nAll production plans satisfy their quotas and capacity constraints!")

    finally:
        conn.close()