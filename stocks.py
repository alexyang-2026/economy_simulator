from orderbook import OrderBook
import math
import copy

class StockExchange:
    def __init__(self, conn, corporations_config):
        self.conn = conn
        self.order_books = {}

        for corporation_id in corporations_config:
            self.order_books[corporation_id] = OrderBook()

    def save_order_to_db(self, investor_id, ticker, side, price, quantity):
        cursor = self.conn.execute(
            """
            INSERT INTO stock_orders
                (investor_id, ticker, side, price, quantity, remaining_quantity)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (investor_id, ticker, side, price, quantity, quantity)
        )
        return cursor.lastrowid

    def submit_order(self, investor_id, ticker, side, price, quantity):
        if ticker not in self.order_books:
            raise ValueError(f"Unknown stock ticker: {ticker}")

        if not isinstance(side, str) or side.strip().lower() not in ("buy", "sell"):
            raise ValueError("Side must be 'buy' or 'sell.'")

        side = side.strip().lower() # Just in case we pass in a parameter such as `buY `

        if not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
            raise ValueError("Price must be a positive, finite number.")

        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")


        if side == "buy":
            with self.conn:
                row = self.conn.execute(
                    """SELECT money, reserved_balance FROM profiles WHERE player_id = ?""",
                    (investor_id,)
                ).fetchone()

                if row is None:
                    raise ValueError(f"Investor with player ID {investor_id} does not exist.")

                investor_balance, reserved_balance = row

                required_cash = price * quantity
                available_cash = investor_balance - reserved_balance

                if required_cash > available_cash:
                    raise ValueError("Insufficient available funds.")
                
                
                cursor = self.conn.execute(
                    """
                    UPDATE profiles
                    SET reserved_balance = reserved_balance + ?
                    WHERE player_id = ? AND money - reserved_balance >= ?
                    """,
                    (required_cash, investor_id, required_cash)
                )

                if cursor.rowcount != 1: # safety check to verify SQLite only updated one investor's balance
                    raise ValueError("Insufficient available funds.")

                order_id = self.save_order_to_db(investor_id, ticker, side, price, quantity)

            self.order_books[ticker].add_order(price, quantity, side, investor_id, order_id)

        elif side == "sell":
            with self.conn:
                row = self.conn.execute(
                    "SELECT quantity, reserved FROM stock_holdings WHERE investor_id = ? AND ticker = ?",
                    (investor_id, ticker)
                ).fetchone()

                if row is None:
                    raise ValueError(f"Investor with ID {investor_id} does not have the stock {ticker}.")

                amount_owned = row[0] - row[1]

                if quantity > amount_owned:
                    raise ValueError(f"Insufficient stock quantity owned. Player ID {investor_id} attempted to sell {quantity} when they only had {amount_owned}.")

                cursor = self.conn.execute(
                    """
                    UPDATE stock_holdings
                    SET reserved = reserved + ?
                    WHERE investor_id = ? AND ticker = ? AND quantity - reserved >= ?
                    """,
                    (quantity, investor_id, ticker, quantity)
                )

                if cursor.rowcount != 1: # safety check to verify SQLite only updated one investor's reserved shares
                    raise ValueError("Insufficient stock quantity owned.")

                order_id = self.save_order_to_db(investor_id, ticker, side, price, quantity)

            self.order_books[ticker].add_order(price, quantity, side, investor_id, order_id)

        self.execute_matches(ticker)
        return order_id


    def settle_trade(self, ticker, trade):
        buy_id = trade["buy_order_id"]
        sell_id = trade["sell_order_id"]
        buyer_id = trade["buyer_id"]
        seller_id = trade["seller_id"]
        price = trade["price"]
        quantity = trade["quantity"]

        with self.conn:

            # First we need the original buy and sell orders from SQLite to validate the trade and update their remaining quantities and statuses
            buy = self.conn.execute(
                """
                SELECT investor_id, ticker, side, price,
                    remaining_quantity, status
                FROM stock_orders
                WHERE order_id = ?
                """,
                (buy_id,)
            ).fetchone()

            sell = self.conn.execute(
                """
                SELECT investor_id, ticker, side, price,
                    remaining_quantity, status
                FROM stock_orders
                WHERE order_id = ?
                """,
                (sell_id,)
            ).fetchone()

            # Verify that the trade is valid before transferring any money or shares
            if buy is None or sell is None:
                raise ValueError("One or both orders do not exist.")

            if buy[0] != buyer_id or sell[0] != seller_id:
                raise ValueError("Trade investor IDs do not match the original orders.")

            if buy[1] != ticker or sell[1] != ticker: # if the tickers aren't the same
                raise ValueError("Trade tickers do not match the original orders.")

            if buy[2] != "buy":
                raise ValueError("The buy order is not an actual buy order (argument `side` is not equal to 'buy')")

            if sell[2] != "sell":
                raise ValueError("The sell order is not an actual sell order (argument `side` is not equal to 'sell')")

            if buy[-1] != "open" or sell[-1] != "open":
                raise ValueError("One of these orders do not have status open.")

            if not 0 < quantity <= min(buy[4], sell[4]):
                # A trade must involve at least one share
                # We cannot trade more than the remaining quantity of either the buy order or the sell order
                # These two inequalities must hold simultaneously (quantity <= buy[4] and quantity <= sell[4])
                # That's how we got the inequality 0 < quantity <= min(buy[4], sell[4])
                raise ValueError("Invalid trade quantity.")

            if type(price) not in (int, float) or not math.isfinite(price) or price <= 0:
                raise ValueError("Execution price must be a positive, finite number.")
            
            if not sell[3] <= price <= buy[3]:
                raise ValueError("Execution price must be at least the sell limit price and at most the buy limit price.")
            
            payment = price * quantity
            released_cash = buy[3] * quantity # buy[3] is the original limit price PER SHARE not total price

            # The difference between payment and released_cash:
            # `payment` is the actual money being paid to the seller.
            # `reserved_cash` was the original price the buyer reserved when they made the listing.
            # For example, if someone put a buy order for $25 per share, but the lowest price sell order is $20 per share, then `payment` is 20 * quantity whereas `released_cash` is 25 * quantity.

            buyer_payment_cursor = self.conn.execute(
                """
                UPDATE profiles
                SET money = money - ?, reserved_balance = reserved_balance - ?
                WHERE player_id = ?
                AND money >= ?
                AND reserved_balance >= ?
                """,
                (payment, released_cash, buyer_id, payment, released_cash)
            )

            if buyer_payment_cursor.rowcount != 1:
                raise ValueError("Buyer's balance or reserved funds are inconsistent!")

            seller_payment_cursor = self.conn.execute(
                """
                UPDATE profiles
                SET money = money + ?
                WHERE player_id = ?
                """,
                (payment, seller_id)
            )

            if seller_payment_cursor.rowcount != 1:
                raise ValueError("Seller does not exist.")


            buyer_transfer_stocks_cursor = self.conn.execute(
                """
                INSERT INTO stock_holdings (investor_id, ticker, quantity, reserved)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(investor_id, ticker)
                DO UPDATE SET quantity = quantity + excluded.quantity
                """,
                (buyer_id, ticker, quantity)
            )

            if buyer_transfer_stocks_cursor.rowcount != 1:
                raise RuntimeError("Failed to credit buyer's stock holdings.")

            seller_transfer_stocks_cursor = self.conn.execute(
                """
                UPDATE stock_holdings
                SET quantity = quantity - ?,
                    reserved = reserved - ?
                WHERE investor_id = ? AND ticker = ?
                AND quantity >= ?
                AND reserved >= ?
                """,
                (quantity, quantity, seller_id, ticker, quantity, quantity)
            )

            if seller_transfer_stocks_cursor.rowcount != 1:
                raise ValueError("Seller has insufficient reserved shares.")

            buy_order_update_cursor = self.conn.execute(
                """
                UPDATE stock_orders
                SET remaining_quantity = remaining_quantity - ?, 
                    status = CASE
                        WHEN remaining_quantity = ? THEN 'filled'
                        ELSE 'open'
                    END
                WHERE order_id = ?
                """,
                (quantity, quantity, buy_id) # WHEN remaining_quantity = quantity because SQL checks remaining_quantity using its value BEFORE the update so we can't use (WHEN remaining_quantity = 0)
            )

            if buy_order_update_cursor.rowcount != 1:
                raise ValueError("Failed to update the buy order.")

            sell_order_update_cursor = self.conn.execute(
                """
                UPDATE stock_orders
                SET remaining_quantity = remaining_quantity - ?, 
                    status = CASE
                        WHEN remaining_quantity = ? THEN 'filled'
                        ELSE 'open'
                    END
                WHERE order_id = ?
                """,
                (quantity, quantity, sell_id)
            )

            if sell_order_update_cursor.rowcount != 1:
                raise ValueError("Failed to update the sell order.")

            insert_trade_record_cursor = self.conn.execute(
                """
                INSERT INTO stock_trades (ticker, buy_order_id, sell_order_id, buyer_id, seller_id, price, quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ticker, buy_id, sell_id, buyer_id, seller_id, price, quantity)
            )

            if insert_trade_record_cursor.rowcount != 1:
                raise RuntimeError("Failed to insert the executed trade into stock_trades.")
            

    def execute_matches(self, ticker):
        if ticker not in self.order_books:
            raise ValueError(f"Unknown stock ticker: {ticker}")

        book = self.order_books[ticker]

        original_buy_orders = copy.deepcopy(book.buy_orders)
        original_sell_orders = copy.deepcopy(book.sell_orders)

        try:
            with self.conn:
                trades = book.match_orders()
                for trade in trades:
                    self.settle_trade(ticker, trade)

        except Exception:
            # Undo changes to the Python heaps if settle_trade function fails
            book.buy_orders = original_buy_orders
            book.sell_orders = original_sell_orders
            raise

        return trades



            
        