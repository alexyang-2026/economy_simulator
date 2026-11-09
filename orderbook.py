import heapq

class OrderBook:
    def __init__(self):
        # Initialize two empty heaps
        self.buy_orders = []
        self.sell_orders = []

    def add_order(self, price, quantity, side, investor_id, order_id):
        if side == "buy":
            heapq.heappush(self.buy_orders, (-price, order_id, quantity, investor_id))
            # Buy prices are stored as negative because we want the highest bid first (i.e. the absolute value of the most negative negative number) (which is the heap's topmost entry)
        else: # sell
            heapq.heappush(self.sell_orders, (price, order_id, quantity, investor_id))
            # Sell prices are positive because we want the lowest ask first

    def match_orders(self):
        trades = []

        while (self.buy_orders and self.sell_orders and -self.buy_orders[0][0] >= self.sell_orders[0][0]):
            buy_order = heapq.heappop(self.buy_orders)
            sell_order = heapq.heappop(self.sell_orders)

            buy_quantity = buy_order[2]
            sell_quantity = sell_order[2]
            traded_quantity = min(buy_quantity, sell_quantity)

            if buy_order[1] < sell_order[1]:
                execution_price = -buy_order[0]
            else:
                execution_price = sell_order[0]

            # Example: 
            # Say a buyer places an order for a stock at $105. Then, the seller comes, willing to accept $102 for the stock. The trade executes at $105 (so we take the buyer's price if the buyer arrives first).
            # Say the seller first places an order at $102, and the buyer arrives later, willing to pay $105. Then the trade executes at the seller's price of $102 (because the buyer is buying from the seller's existing listing).
            # The seller's $102 is their MINIMUM acceptable price.
            # The buyer's $105 is their MAXIMUM cceptable price.

            trade_data = {
                "buy_order_id": buy_order[1],
                "sell_order_id": sell_order[1],
                "buyer_id": buy_order[3],
                "seller_id": sell_order[3],
                "price": execution_price,
                "quantity": traded_quantity
            }
            
            trades.append(trade_data)

            remaining_buy = buy_quantity - traded_quantity
            if remaining_buy > 0:
                heapq.heappush(self.buy_orders, (buy_order[0], buy_order[1], remaining_buy, buy_order[3]))

            remaining_sell = sell_quantity - traded_quantity
            if remaining_sell > 0:
                heapq.heappush(self.sell_orders, (sell_order[0], sell_order[1], remaining_sell, sell_order[3]))

        return trades

