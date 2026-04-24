from datamodel import OrderDepth, TradingState, Order
from typing import List

class Trader:

    def run(self, state: TradingState):
        result = {}

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            #Mid price
            if not order_depth.buy_orders or not order_depth.sell_orders:
                result[product] = orders
                continue

            best_bid = max(order_depth.buy_orders.keys())
            best_ask = min(order_depth.sell_orders.keys())
            mid_price = (best_bid + best_ask) / 2

            #Position 
            position = state.position.get(product, 0)

            #Fair price (inventory adjusted)
            lambda_param = 0.1
            fair_price = mid_price - lambda_param * position

            #Spread
            spread = 2
            bid_price = int(fair_price - spread / 2)
            ask_price = int(fair_price + spread / 2)

            #Position limits
            POSITION_LIMIT = 20
            max_buy = POSITION_LIMIT - position
            max_sell = POSITION_LIMIT + position

            buy_quantity = max(0, max_buy)
            sell_quantity = max(0, max_sell)

            #Place orders
            if buy_quantity > 0:
                orders.append(Order(product, bid_price, buy_quantity))

            if sell_quantity > 0:
                orders.append(Order(product, ask_price, -sell_quantity))

            result[product] = orders

        traderData = ""
        conversions = 0
        return result, conversions, traderData